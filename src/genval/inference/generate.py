"""Batch inference over eval prompts.

Single responsibility: given a checkpoint and a list of TrainingExample
(with rendered_text as prompt), produce model output strings.
Parsing those strings into ResponseDistribution objects is the caller's job.

Must NOT compute metrics.
"""

from __future__ import annotations

# TODO: implement
# Steps:
# 1. Load checkpoint from path or HF hub id
# 2. Build prompts from EvalTarget objects via the serializer
# 3. Run batched generation with vLLM or HF generate()
# 4. Return raw string outputs (parsing happens in temporal_eval.py)
