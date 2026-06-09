"""Corpus builder: RespondentRecord → TrainingExample JSONL.

Single responsibility: apply the serialization config to produce rendered_text
from structured_target fields. Write output to a hash-named corpus directory.

Must NOT modify structured_target values — only renders them to text.
"""

from __future__ import annotations

# TODO: implement
# Steps:
# 1. Accept a serialization DictConfig and a list[RespondentRecord]
# 2. Compute config hash via genval.utils.hashing.hash_config
# 3. For each record, produce TrainingExample with:
#    - structured_target: dict of construct_id → value/distribution
#    - rendered_text: template-rendered string from config
# 4. Assign split labels from configs/eval/temporal_splits.yaml
# 5. Write to data/processed/corpus_{hash}/train.jsonl, val.jsonl, test.jsonl
# 6. Write a manifest with n_examples per split and config hash
