"""Evaluation metrics for genval.

Single responsibility: compute quantitative scores between predicted and observed
response distributions. All inputs and outputs are numeric; no text is evaluated here.

Must NOT load model weights or run inference — metrics only.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from scipy.stats import wasserstein_distance

from genval.schemas import EvalTarget, ResponseDistribution


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ItemMetrics:
    item_id: str
    construct_id: str
    js_divergence: float
    wasserstein: float
    n_respondents_observed: int


@dataclass
class CalibrationResult:
    ece: float                       # Expected Calibration Error
    bin_accuracies: list[float]
    bin_confidences: list[float]
    bin_counts: list[int]


@dataclass
class VarianceRatioResult:
    ratio: float                     # predicted / observed between-country variance
    predicted_variance: float
    observed_variance: float
    n_countries: int
    construct_id: str


@dataclass
class EvalResult:
    """Aggregated results for one evaluation run."""
    js_divergence_mean: float
    js_divergence_per_item: dict[str, float]
    wasserstein_mean: float
    wasserstein_per_item: dict[str, float]
    calibration: CalibrationResult | None
    variance_ratios: list[VarianceRatioResult]
    n_examples: int
    n_countries: int
    per_country: dict[str, "EvalResult"] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Jensen-Shannon divergence
# ---------------------------------------------------------------------------


def js_divergence(p: Sequence[float], q: Sequence[float]) -> float:
    """Jensen-Shannon divergence between distributions p and q.

    Symmetric, bounded [0, 1] (using log base 2).
    Both distributions must be over the same support and sum to ~1.

    Args:
        p: Observed distribution (ground truth).
        q: Predicted distribution.

    Returns:
        JS divergence in [0, 1]. Returns 1.0 if either distribution is all-zero.
    """
    p_arr = np.asarray(p, dtype=float)
    q_arr = np.asarray(q, dtype=float)

    if p_arr.sum() == 0 or q_arr.sum() == 0:
        return 1.0

    # Normalise (defensive against floating-point drift)
    p_arr = p_arr / p_arr.sum()
    q_arr = q_arr / q_arr.sum()

    m = 0.5 * (p_arr + q_arr)

    def kl(a: np.ndarray, b: np.ndarray) -> float:
        # KL(a || b); skip zeros
        mask = (a > 0) & (b > 0)
        return float(np.sum(a[mask] * np.log2(a[mask] / b[mask])))

    return 0.5 * kl(p_arr, m) + 0.5 * kl(q_arr, m)


# ---------------------------------------------------------------------------
# Ordinal Wasserstein distance
# ---------------------------------------------------------------------------


def ordinal_wasserstein(p: Sequence[float], q: Sequence[float]) -> float:
    """1D Wasserstein (Earth Mover's) distance treating categories as ordered integers.

    More appropriate than JS for ordinal Likert scales because it respects
    the ordering of response categories (e.g. strongly disagree → strongly agree).

    Args:
        p: Observed distribution over categories 1..n.
        q: Predicted distribution over categories 1..n.

    Returns:
        Wasserstein distance (unnormalised; divide by n-1 to get [0,1]).
    """
    p_arr = np.asarray(p, dtype=float)
    q_arr = np.asarray(q, dtype=float)

    n = len(p_arr)
    positions = np.arange(1, n + 1, dtype=float)

    p_arr = p_arr / p_arr.sum() if p_arr.sum() > 0 else np.ones(n) / n
    q_arr = q_arr / q_arr.sum() if q_arr.sum() > 0 else np.ones(n) / n

    return float(wasserstein_distance(positions, positions, p_arr, q_arr))


# ---------------------------------------------------------------------------
# Per-item metrics
# ---------------------------------------------------------------------------


def compute_item_metrics(
    observed: ResponseDistribution,
    predicted: ResponseDistribution,
    construct_id: str,
) -> ItemMetrics:
    """Compute JS divergence and Wasserstein distance for a single item."""
    obs_p = observed.probabilities
    pred_p = predicted.probabilities

    # Pad to same length if categories differ (defensive)
    n = max(len(obs_p), len(pred_p))
    obs_p = list(obs_p) + [0.0] * (n - len(obs_p))
    pred_p = list(pred_p) + [0.0] * (n - len(pred_p))

    return ItemMetrics(
        item_id=observed.item_id,
        construct_id=construct_id,
        js_divergence=js_divergence(obs_p, pred_p),
        wasserstein=ordinal_wasserstein(obs_p, pred_p),
        n_respondents_observed=observed.n_respondents,
    )


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------


def expected_calibration_error(
    predicted_probs: Sequence[float],
    observed_outcomes: Sequence[int],
    n_bins: int = 10,
) -> CalibrationResult:
    """Expected Calibration Error (ECE) for probabilistic predictions.

    Bins predictions by confidence and checks whether predicted probabilities
    match empirical frequencies.

    Args:
        predicted_probs: Model's predicted probability for the positive class.
        observed_outcomes: Binary ground truth (0 or 1).
        n_bins: Number of equal-width bins.

    Returns:
        CalibrationResult with ECE and per-bin statistics.
    """
    probs = np.asarray(predicted_probs, dtype=float)
    outcomes = np.asarray(observed_outcomes, dtype=float)

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_accuracies, bin_confidences, bin_counts = [], [], []

    for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
        mask = (probs >= lo) & (probs < hi)
        if mask.sum() == 0:
            bin_accuracies.append(0.0)
            bin_confidences.append(0.0)
            bin_counts.append(0)
            continue
        bin_accuracies.append(float(outcomes[mask].mean()))
        bin_confidences.append(float(probs[mask].mean()))
        bin_counts.append(int(mask.sum()))

    n_total = len(probs)
    ece = sum(
        count / n_total * abs(acc - conf)
        for acc, conf, count in zip(bin_accuracies, bin_confidences, bin_counts)
    )

    return CalibrationResult(
        ece=float(ece),
        bin_accuracies=bin_accuracies,
        bin_confidences=bin_confidences,
        bin_counts=bin_counts,
    )


# ---------------------------------------------------------------------------
# Between-country variance ratio
# ---------------------------------------------------------------------------


def compute_variance_ratio(
    observed_means: Sequence[float],
    predicted_means: Sequence[float],
    construct_id: str,
) -> VarianceRatioResult:
    """Compute the ratio of predicted to observed between-country variance.

    Detects the known failure mode of flattening toward a generic respondent:
    a model that ignores country identity will predict the same values everywhere,
    producing near-zero between-country variance (ratio → 0).

    Ratio ~1.0 is ideal. Ratio > 1 means over-differentiation.
    Ratio < 0.7 is a warning sign; < 0.5 is a failure.

    Args:
        observed_means: Observed country-level mean construct value (one per country).
        predicted_means: Predicted country-level mean construct value (one per country).
        construct_id: Construct being evaluated.

    Returns:
        VarianceRatioResult with ratio and component variances.
    """
    obs = np.asarray(observed_means, dtype=float)
    pred = np.asarray(predicted_means, dtype=float)

    obs_var = float(np.var(obs, ddof=1)) if len(obs) > 1 else 0.0
    pred_var = float(np.var(pred, ddof=1)) if len(pred) > 1 else 0.0

    ratio = pred_var / obs_var if obs_var > 0 else float("nan")

    return VarianceRatioResult(
        ratio=ratio,
        predicted_variance=pred_var,
        observed_variance=obs_var,
        n_countries=len(obs),
        construct_id=construct_id,
    )


# ---------------------------------------------------------------------------
# Aggregate eval
# ---------------------------------------------------------------------------


def evaluate(
    targets: list[EvalTarget],
    predictions: list[dict[str, ResponseDistribution]],
    compute_calibration: bool = True,
    n_calibration_bins: int = 10,
) -> EvalResult:
    """Compute all metrics for a set of (target, prediction) pairs.

    Args:
        targets: Ground-truth EvalTarget objects.
        predictions: One dict per target mapping construct_id → predicted ResponseDistribution.
        compute_calibration: Whether to compute ECE (slower; needs binarised predictions).
        n_calibration_bins: Number of bins for ECE.

    Returns:
        EvalResult with all aggregate and per-item scores.
    """
    if len(targets) != len(predictions):
        raise ValueError(
            f"targets ({len(targets)}) and predictions ({len(predictions)}) must have same length"
        )

    all_js: list[float] = []
    all_ws: list[float] = []
    js_per_item: dict[str, list[float]] = {}
    ws_per_item: dict[str, list[float]] = {}
    country_construct_observed: dict[tuple[str, str], list[float]] = {}
    country_construct_predicted: dict[tuple[str, str], list[float]] = {}

    for target, pred in zip(targets, predictions):
        for construct_id, obs_dist in target.constructs.items():
            if construct_id not in pred:
                continue
            pred_dist = pred[construct_id]
            item_m = compute_item_metrics(obs_dist, pred_dist, construct_id)

            all_js.append(item_m.js_divergence)
            all_ws.append(item_m.wasserstein)
            js_per_item.setdefault(construct_id, []).append(item_m.js_divergence)
            ws_per_item.setdefault(construct_id, []).append(item_m.wasserstein)

            # Collect country-level means for variance ratio
            obs_mean = sum(
                (i + 1) * p for i, p in enumerate(obs_dist.probabilities)
            )
            pred_mean = sum(
                (i + 1) * p for i, p in enumerate(pred_dist.probabilities)
            )
            key = (target.iso3, construct_id)
            country_construct_observed.setdefault(key, []).append(obs_mean)
            country_construct_predicted.setdefault(key, []).append(pred_mean)

    # Per-construct variance ratios
    constructs_seen = {k for _, k in country_construct_observed}
    variance_ratios = []
    for construct_id in constructs_seen:
        countries = sorted({iso3 for iso3, cid in country_construct_observed if cid == construct_id})
        obs_means = [
            float(np.mean(country_construct_observed[(c, construct_id)]))
            for c in countries
            if (c, construct_id) in country_construct_observed
        ]
        pred_means = [
            float(np.mean(country_construct_predicted[(c, construct_id)]))
            for c in countries
            if (c, construct_id) in country_construct_predicted
        ]
        if len(obs_means) >= 2:
            variance_ratios.append(
                compute_variance_ratio(obs_means, pred_means, construct_id)
            )

    countries_seen = {t.iso3 for t in targets}

    return EvalResult(
        js_divergence_mean=float(np.mean(all_js)) if all_js else float("nan"),
        js_divergence_per_item={k: float(np.mean(v)) for k, v in js_per_item.items()},
        wasserstein_mean=float(np.mean(all_ws)) if all_ws else float("nan"),
        wasserstein_per_item={k: float(np.mean(v)) for k, v in ws_per_item.items()},
        calibration=None,   # populated separately if compute_calibration=True
        variance_ratios=variance_ratios,
        n_examples=len(targets),
        n_countries=len(countries_seen),
    )
