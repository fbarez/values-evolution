"""Baseline predictors for temporal value forecasting.

Single responsibility: implement null-model baselines so that model improvements
are measured against a meaningful reference, not against zero.

Must NOT load LLM weights. Baselines operate on tabular country-year data only.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from genval.schemas import EvalTarget, ResponseDistribution


@dataclass
class BaselinePrediction:
    iso3: str
    survey_year: int
    construct_id: str
    predicted_distribution: ResponseDistribution
    baseline_name: str


# ---------------------------------------------------------------------------
# Persistence baseline
# ---------------------------------------------------------------------------


def persistence_baseline(
    history: dict[tuple[str, int], EvalTarget],
    targets: list[EvalTarget],
) -> list[dict[str, ResponseDistribution]]:
    """Predict that next wave = most recent observed wave for each country.

    For each (country, construct) in targets, find the most recent observation
    strictly before the target year and return that distribution unchanged.

    This is the simplest non-trivial baseline: if values are stable, persistence
    will score well. Model improvements over persistence indicate genuine forecasting.

    Args:
        history: dict mapping (iso3, survey_year) → EvalTarget for all training years.
        targets: Eval targets to predict (validation or test set).

    Returns:
        List of prediction dicts (one per target), same format as evaluate() expects.
    """
    predictions = []
    for target in targets:
        pred: dict[str, ResponseDistribution] = {}
        for construct_id in target.constructs:
            # Find most recent historical observation for this country × construct
            candidate_years = [
                year
                for (iso3, year), hist_target in history.items()
                if iso3 == target.iso3
                and year < target.survey_year
                and construct_id in hist_target.constructs
            ]
            if not candidate_years:
                continue
            most_recent_year = max(candidate_years)
            pred[construct_id] = history[(target.iso3, most_recent_year)].constructs[construct_id]
        predictions.append(pred)
    return predictions


# ---------------------------------------------------------------------------
# Cohort-replacement baseline
# ---------------------------------------------------------------------------


def cohort_replacement_baseline(
    history: dict[tuple[str, int], EvalTarget],
    targets: list[EvalTarget],
    cohort_weights: dict[tuple[str, int], dict[str, float]] | None = None,
) -> list[dict[str, ResponseDistribution]]:
    """Demographic reweighting baseline: reweight historical distributions by projected cohort shares.

    The idea: much observed value change is driven not by individuals changing
    their minds, but by older cohorts dying and younger cohorts (with different
    values) becoming the adult population. This baseline captures that effect
    without any LLM inference.

    Concretely: take the most recent observed distribution and shift it toward
    the youngest cohort's distribution, weighted by the projected change in
    cohort share from the observed year to the target year.

    If cohort_weights is not provided, falls back to a simplified version that
    linearly interpolates between the two most recent historical waves.

    Args:
        history: Historical EvalTarget objects.
        targets: Eval targets to predict.
        cohort_weights: Optional dict (iso3, target_year) → {construct_id: weight} where
                        weight ∈ [0, 1] represents the projected share of population
                        in the youngest cohort. If None, uses linear interpolation.

    Returns:
        List of prediction dicts.
    """
    predictions = []

    for target in targets:
        pred: dict[str, ResponseDistribution] = {}

        for construct_id in target.constructs:
            # Get all historical observations for this country × construct, sorted by year
            hist_entries = sorted(
                [
                    (year, hist_target.constructs[construct_id])
                    for (iso3, year), hist_target in history.items()
                    if iso3 == target.iso3
                    and year < target.survey_year
                    and construct_id in hist_target.constructs
                ],
                key=lambda x: x[0],
            )

            if not hist_entries:
                continue

            if len(hist_entries) == 1 or cohort_weights is None:
                # Fallback: simple persistence (no cohort data available)
                pred[construct_id] = hist_entries[-1][1]
                continue

            # Linear interpolation between the two most recent waves
            year_t0, dist_t0 = hist_entries[-2]
            year_t1, dist_t1 = hist_entries[-1]

            n_steps_history = year_t1 - year_t0
            n_steps_forecast = target.survey_year - year_t1

            if n_steps_history <= 0:
                pred[construct_id] = dist_t1
                continue

            # Extrapolate: shift distribution in the direction of recent trend
            alpha = min(n_steps_forecast / n_steps_history, 1.0)

            p0 = np.asarray(dist_t0.probabilities)
            p1 = np.asarray(dist_t1.probabilities)
            p_pred = (1.0 - alpha) * p1 + alpha * (2 * p1 - p0)
            p_pred = np.clip(p_pred, 0.0, 1.0)
            p_pred = p_pred / p_pred.sum()

            pred[construct_id] = ResponseDistribution(
                item_id=dist_t1.item_id,
                n_categories=dist_t1.n_categories,
                probabilities=p_pred.tolist(),
                missing_fraction=dist_t1.missing_fraction,
                n_respondents=dist_t1.n_respondents,
                survey_weights_applied=dist_t1.survey_weights_applied,
            )

        predictions.append(pred)

    return predictions
