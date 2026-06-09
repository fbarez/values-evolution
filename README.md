# genval — Values Evolution via Mid-Training

Mid-training an open-weights LLM on harmonized cross-national values-survey data to model and forecast how societal values evolve across European and other countries.

## What this is

We fine-tune a 7B-parameter open-weights LLM (Qwen 2.5 or OLMo 2) on respondent-level data from the European Values Study (EVS), World Values Survey (WVS), European Social Survey (ESS), and Eurobarometer, enriched with country-level covariates (V-Dem, World Bank indicators). The trained model is used to:

1. **Predict held-out survey waves** — given a country/year/demographic profile, predict the distribution of responses the next survey wave will observe.
2. **Forecast value trajectories** — extrapolate beyond observed waves to anticipate future shifts.

## Pipeline overview

```
Raw survey data          Harmonized constructs       Training corpus
(EVS/WVS/ESS/EB)  ──►  (crosswalk-driven)    ──►  (serialization config)
        │                       │                         │
   ingest/               harmonize/                 serialize/
        │                       │                         │
        └───────────────────────┴────────────►  mid-training  ──►  eval
                                                    │
                                              temporal holdout
                                            (train ≤2008, val 2017, test 2026)
```

## Quick start

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and install
git clone https://github.com/fbarez/values-evolution
cd values-evolution
uv sync --extra dev

# 3. Copy secrets template
cp .env.example .env
# Fill in GESIS_USERNAME, GESIS_PASSWORD, HF_TOKEN

# 4. Install pre-commit hooks
uv run pre-commit install

# 5. Run tests
uv run pytest

# 6. Check the eval plan
cat docs/eval_plan.md
```

## Key design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Temporal splits | train ≤2008, val 2017, test 2026 | Prevents leakage; mirrors real forecasting scenario |
| Serialization | Config-driven, hash-named | Treats text format as a research variable to ablate |
| Tokenizer | Frozen (from checkpoint) | Preserves vocabulary alignment; prevents drift |
| Targets | Structured fields, not prose | Enables quantitative eval; prose is rendered downstream |
| Baselines | Persistence + cohort-replacement | Meaningful null; prevents crediting model for demographic trends |

## Data sources

| Source | Coverage | License |
|---|---|---|
| EVS/WVS | 1981–2022, ~100 countries | GESIS (non-commercial research) |
| ESS | 2002–2023, 38 countries | CC BY 4.0 |
| Eurobarometer | 1973–2024, EU member states | GESIS (non-commercial research) |
| V-Dem | 1789–2024, 202 countries | CC BY 4.0 |
| World Bank WDI | 1960–present, 217 economies | CC BY 4.0 |

**No microdata is committed to this repo.** See `data/MANIFEST.md` for expected checksums and `scripts/fetch_data.py` to download.

## Repository structure

```
configs/          — Hydra configs (data, serialization, training, eval, model)
crosswalks/       — item-to-construct mappings (version-controlled)
data/             — GITIGNORED (fetch with scripts/fetch_data.py)
src/genval/       — library code
scripts/          — CLI entry points
tests/            — pytest suite
docs/             — eval plan, data card, serialization decisions log
```

Full conventions and non-negotiables: see [CLAUDE.md](CLAUDE.md).

## Eval plan

See [docs/eval_plan.md](docs/eval_plan.md) for the complete evaluation design, metrics, baselines, and ablation grid.

## Status

- [x] Repo scaffold and data contracts
- [ ] Data fetch scripts (pending GESIS credentials)
- [ ] Harmonization + crosswalks (in progress)
- [ ] Baseline eval (pending base checkpoint download)
- [ ] Mid-training run 001
