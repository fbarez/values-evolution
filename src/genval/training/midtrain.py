"""Mid-training (continued pre-training) on the values corpus.

Single responsibility: configure and launch HuggingFace Trainer for
the LM objective on the values corpus with replay mixing.

Must NOT define eval metrics — calls genval.eval.metrics.
Must NOT retrain the tokenizer.
"""

from __future__ import annotations

# TODO: implement
# Steps:
# 1. Load model + tokenizer from configs/model/
# 2. Load corpus from data/processed/corpus_{hash}/ (train split only)
# 3. Mix in replay data at configs/training/midtrain.yaml replay.ratio
# 4. Configure HuggingFace Trainer with midtrain.yaml HP
# 5. Assert outputs/evals/baseline/ is non-empty before launching
# 6. Run training; save checkpoints to outputs/checkpoints/
