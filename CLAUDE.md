# genval — CLAUDE.md

This file is the law. Every non-negotiable below is enforced by tests, hooks, or CI. Do not route around them.

---

## Non-negotiables

### 1. No survey microdata is ever committed
`data/` is gitignored. The pre-commit hook (`scripts/hooks/no_data_commit.py`) blocks any commit that touches a file under `data/` or any file >5 MB. GESIS/EVS/ESS license terms prohibit redistribution. The repo ships fetch scripts and SHA256 manifests; it never ships data files.

**Consequence:** if you need to share a dataset subset for debugging, use a synthetic stub in `tests/fixtures/`, not real microdata.

### 2. Temporal splits only — no random splits anywhere
Train/val/test boundaries live exclusively in `configs/eval/temporal_splits.yaml`. The canonical split is:
- **Train**: survey year ≤ 2008
- **Val**: survey year = 2017 wave
- **Test**: survey year = 2026 wave (held out until final evaluation)

No function may accept a `random_split` argument. `test_temporal_splits.py` asserts that no training example has a survey year ≥ the validation boundary. If you see `random_split` anywhere in `src/`, it is a bug.

### 3. The tokenizer comes from the checkpoint — never retrain it
Load the tokenizer from the HuggingFace checkpoint ID specified in `configs/model/`. Do not call `tokenizer.train_new_from_iterator()` or any tokenizer-training API. There is no tokenizer-training code in this repo; adding any is a bug.

### 4. Serialization is config-driven and versioned
How survey microdata becomes training text is a research variable, not a hardcoded format. Every built corpus is named by the SHA256 of its serialization config (handled by `src/genval/utils/hashing.py`). Never hardcode a serialization format in a training or eval script — always compose from `configs/serialization/`.

### 5. Structured targets, prose renderings
`TrainingExample.structured_target` stores numeric construct values and response distributions. `TrainingExample.rendered_text` is derived from those fields by the serializer. Eval scores numbers, never prose. Do not add fields that merge numeric targets with text.

### 6. Eval before training
`scripts/run_eval.py` must run against the base (un-tuned) checkpoint before any mid-training. The baseline results go in `outputs/evals/baseline/`. Training scripts should assert this directory exists and is non-empty before launching.

---

## Conventions

- **Python 3.11+**, `uv` for env/deps, `ruff` for lint + format, `pytest` for tests.
- **Hydra** for config composition; every script takes `--config-name` (or `+config_name=`).
- **Type hints everywhere**; pydantic at all data boundaries (see `src/genval/schemas/`).
- **Conventional commits**: `feat:`, `fix:`, `data:`, `eval:`, `config:`, `docs:`, `test:`, `chore:`.
- **Secrets** via `.env` only (gitignored). Ship `.env.example` with every new secret key.
- **Every module** has a docstring stating its single responsibility and what it must NOT do.
- **Crosswalks are research decisions**, not data. `crosswalks/` is version-controlled. Document every mapping change with a rationale comment.

---

## Project layout (quick reference)

```
configs/       — Hydra configs: data sources, serialization variants, training HP, eval splits
crosswalks/    — item-to-construct mappings (version-controlled CSVs, not data)
data/          — GITIGNORED: raw/, interim/, processed/
src/genval/    — library code; import as `from genval.schemas import TrainingExample`
scripts/       — CLI entry points (fetch, build, eval, train)
tests/         — pytest suite; must pass from a fresh clone
docs/          — eval_plan.md (authoritative), data_card.md, serialization_decisions.md
```

---

## Adding a new data source

1. Add a config in `configs/data/<source>.yaml` with URL/DOI, version, expected checksums, and license note.
2. Implement `src/genval/ingest/<source>.py` with `fetch()`, `parse()`, `validate()`.
3. Add crosswalk entries in `crosswalks/` for any new items.
4. Update `data/MANIFEST.md` with expected file checksums.
5. Add a test in `tests/test_crosswalks.py` asserting no orphan mappings.

## Adding a serialization variant

1. Add a config in `configs/serialization/<variant>.yaml`.
2. Implement or extend `src/genval/serialize/`.
3. Run `scripts/build_corpus.py` — the output directory will be named by the config hash.
4. Log the rationale in `docs/serialization_decisions.md`.

## Running evals

```bash
# Baseline (base checkpoint, no mid-training)
python scripts/run_eval.py --config-name base_eval

# Post-training
python scripts/run_eval.py --config-name midtrain_eval checkpoint=outputs/checkpoints/run_001
```
