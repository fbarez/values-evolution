# Evaluation Plan — genval

## Overview

We evaluate whether mid-training an LLM on cross-national values-survey data enables it to (a) predict held-out survey waves and (b) forecast how values evolve over time. All evaluation is quantitative, operating on structured numeric targets, not on prose.

---

## 1. Temporal Holdout Design

### Rationale

Values data is inherently longitudinal. The natural evaluation framework mirrors real forecasting: train on past waves, predict future ones. This makes the train/val/test split a temporal, not a random, split.

A random split would be epistemically incorrect: it would leak future information into training (a respondent from a 2017 wave in the training set implicitly encodes 2017-level values), and it would not test the thing we actually care about — forecasting.

### Split boundaries

| Split | Survey year(s) | Purpose |
|---|---|---|
| **Train** | ≤ 2008 | Mid-training corpus. Covers EVS waves 1981, 1990, 1999, 2008. |
| **Validation** | 2017 | Hyperparameter selection, early stopping, serialization ablation. Do not report final numbers on val. |
| **Test** | 2026 (EVS 2022 + ESS round 11) | Final held-out evaluation. Inspect once, after all decisions frozen. |

The 2008 → 2017 → 2026 gap structure is intentional: it tests forecasting across a ~9-year horizon in both steps, matching the EVS wave interval.

### Operationalisation

1. `configs/eval/temporal_splits.yaml` is the single source of truth for all boundary years.
2. `tests/test_temporal_splits.py` asserts no training example has `survey_year >= 2017`.
3. `scripts/build_corpus.py` assigns `split` labels at corpus build time using these boundaries.
4. No code may define a split anywhere other than `temporal_splits.yaml`.

---

## 2. Metrics

### 2.1 Distributional distance — primary metric

**What we predict**: a probability distribution over response categories for each construct × country × wave.

**Why not point estimates**: response distributions encode more information than means (bimodality, variance, tail behaviour). A model that predicts the mean correctly but misses a bimodal distribution has failed in a meaningful way.

#### Jensen-Shannon Divergence (JS)

$$\text{JS}(P \| Q) = \frac{1}{2} D_\text{KL}(P \| M) + \frac{1}{2} D_\text{KL}(Q \| M), \quad M = \frac{P+Q}{2}$$

- Symmetric, bounded ∈ [0, 1] (base-2 logarithm).
- **Primary headline metric**: `js_divergence_mean` averaged over all construct × country pairs.
- Reported per construct and per country.

#### Ordinal Wasserstein Distance

- 1D Wasserstein (Earth Mover's) distance treating response categories as ordered integers.
- Better than JS for Likert scales: respects that "strongly disagree" → "disagree" is a smaller error than "strongly disagree" → "strongly agree".
- Reported as secondary metric alongside JS.

**Implementation**: `src/genval/eval/metrics.py` — `js_divergence()`, `ordinal_wasserstein()`.

### 2.2 Calibration — Expected Calibration Error (ECE)

For each construct where the model outputs a probability distribution, ECE measures whether the predicted probabilities match empirical frequencies:

$$\text{ECE} = \sum_{b=1}^{B} \frac{|B_b|}{n} \left| \text{acc}(B_b) - \text{conf}(B_b) \right|$$

- 10 equal-width bins.
- A perfectly calibrated model has ECE = 0.
- Used to detect overconfident predictions (a common failure of fine-tuned LLMs).

**Implementation**: `src/genval/eval/metrics.py` — `expected_calibration_error()`.

### 2.3 Between-country variance ratio

$$\text{VR}(c) = \frac{\text{Var}_{\text{pred}}(\bar{y}_{k,c})}{\text{Var}_{\text{obs}}(\bar{y}_{k,c})}$$

where $\bar{y}_{k,c}$ is the mean construct value $k$ in country $c$.

**Purpose**: detects the known failure mode of flattening toward a generic respondent. A model that ignores country identity will predict the same distribution everywhere → VR ≈ 0.

- Target: VR ≈ 1.0.
- Warn threshold: VR < 0.7.
- Fail threshold: VR < 0.5.
- Reported per construct.

**Implementation**: `src/genval/eval/metrics.py` — `compute_variance_ratio()`.

---

## 3. Baselines

Model improvements must be measured against meaningful null hypotheses.

### 3.1 Persistence baseline

**Definition**: for each (country, construct), predict that the next wave equals the most recent observed wave.

**Motivation**: values are sticky. If this baseline scores well, it means the model is not learning anything beyond "things don't change much". Only improvements over persistence are scientifically interesting.

**Implementation**: `src/genval/eval/baselines.py` — `persistence_baseline()`.

### 3.2 Cohort-replacement baseline

**Definition**: linearly extrapolate the trend from the two most recent historical waves. More sophisticated than persistence: it captures the fact that measured change often reflects cohort turnover (younger cohorts with different values replacing older ones) rather than individuals changing their minds.

**Motivation**: much of the secular trend in values (declining religiosity, rising gender egalitarianism) is mechanically driven by cohort replacement. If the model does not beat this baseline, it is not learning anything beyond demographic arithmetic.

**Implementation**: `src/genval/eval/baselines.py` — `cohort_replacement_baseline()`.

### 3.3 Base checkpoint zero-shot

**Definition**: the base (un-tuned) Qwen 2.5 / OLMo 2 checkpoint, prompted zero-shot with the country/year/demographic profile.

**Purpose**: measures what the model already "knows" about values from pre-training, before any mid-training. Non-negotiable #6 requires this baseline to be established before any mid-training.

Output: `outputs/evals/baseline/results.json`.

---

## 4. Ablation Grid

The ablation grid systematically isolates the effect of each research decision.

### 4.1 Serialization variants

| Variant | Description |
|---|---|
| `country_year_doc` | One doc per country × wave. Aggregated distributions. |
| `respondent_profile` | One doc per respondent. Individual responses. |
| `qa_pairs` | Q&A format. Closest to inference use case. |

**Evaluation**: hold model, training HP, and data constant; vary serialization config. Measure JS divergence on val set. Select best variant before any test-set inspection.

### 4.2 Model architecture

| Model | HF ID | Notes |
|---|---|---|
| Qwen 2.5 7B | `Qwen/Qwen2.5-7B` | Strong multilingual; good coverage of European languages |
| OLMo 2 7B | `allenai/OLMo-2-1124-7B` | Fully documented training data; cleaner attribution |

**Evaluation**: fix serialization and HP; swap model. Isolates architecture effect.

### 4.3 Training data scope

| Variant | Sources |
|---|---|
| EVS only | EVS/WVS waves ≤ 2008 |
| EVS + ESS | Add ESS rounds ≤ 2008 |
| Full | EVS + ESS + Eurobarometer |
| Full + covariates | Full + V-Dem + WDI merged at country-year level |

**Evaluation**: measure marginal gain from each additional source.

### 4.4 Replay ratio

| Replay ratio | Description |
|---|---|
| 0.0 | No replay (likely catastrophic forgetting) |
| 0.10 | 10% general-domain data per batch |
| 0.15 | Default |
| 0.20 | Higher replay, slower values learning |

**Evaluation**: measure general-capability degradation (benchmark like MMLU or HellaSwag) vs. values task improvement.

### 4.5 Covariate inclusion

- With / without country-level covariates (V-Dem, WDI).
- Tests whether political-economic context improves forecasting or introduces noise.

---

## 5. Evaluation Protocol

### Step 1 — Establish baseline (before any mid-training)

```bash
python scripts/run_eval.py checkpoint=Qwen/Qwen2.5-7B split=val \
    --output-dir outputs/evals/baseline
```

Record: `js_divergence_mean`, `calibration_ece`, `variance_ratio` per construct.

### Step 2 — Serialization ablation (val set only)

For each serialization variant:
1. Build corpus: `python scripts/build_corpus.py --config-name {variant}`
2. Train: `python scripts/run_midtrain.py corpus_hash={hash}`
3. Eval on val: `python scripts/run_eval.py checkpoint=outputs/... split=val`

Select best variant by `js_divergence_mean`. Freeze this choice.

### Step 3 — Model ablation (val set)

With the best serialization: run Qwen vs. OLMo. Select best model. Freeze.

### Step 4 — Data scope ablation (val set)

With best serialization + model: run EVS-only → Full+covariates. Freeze.

### Step 5 — Final test evaluation (once only)

After all choices frozen:
```bash
python scripts/run_eval.py checkpoint=outputs/checkpoints/best split=test
```

Report: headline JS divergence, per-country and per-construct breakdown, baseline deltas, calibration, variance ratios.

**Rule**: test set is inspected exactly once. No hyperparameter changes after test-set inspection.

---

## 6. Reporting

### Per-run result format

```json
{
  "run_id": "...",
  "checkpoint": "...",
  "serialization_config_hash": "...",
  "split": "val",
  "metrics": {
    "js_divergence_mean": 0.12,
    "wasserstein_mean": 0.31,
    "calibration_ece": 0.08,
    "variance_ratio_mean": 0.84
  },
  "baselines": {
    "persistence_js": 0.18,
    "cohort_replacement_js": 0.15
  },
  "per_country": {...},
  "per_construct": {...}
}
```

### Acceptance bar for claiming mid-training works

A mid-trained model is considered to have learned something if, on the **validation set**:
1. JS divergence < persistence baseline JS divergence (beats persistence)
2. Variance ratio > 0.7 (not flattening toward generic respondent)
3. ECE < 0.15 (reasonably calibrated)

The test set is used for final reporting only.
