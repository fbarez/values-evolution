"""Temporal holdout evaluation runner.

Single responsibility: orchestrate loading the temporal splits, running model
inference, computing metrics, and writing results to outputs/evals/.

Must NOT define split boundaries (those live in configs/eval/temporal_splits.yaml).
Must NOT modify training data or checkpoints.
"""

from __future__ import annotations

# TODO: implement after schemas and metrics are stable
# Steps:
# 1. Load temporal_splits.yaml via Hydra
# 2. Load eval targets from data/interim/ parquet (filtered to val or test year)
# 3. Load checkpoint specified in config
# 4. Run inference via genval.inference.generate
# 5. Parse structured predictions from model output
# 6. Call genval.eval.metrics.evaluate(targets, predictions)
# 7. Write EvalResult to outputs/evals/{run_id}/results.json
# 8. Assert baseline results directory exists before any mid-trained run
