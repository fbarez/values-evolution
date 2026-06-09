"""Training wrappers for mid-training and SFT.

Thin wrappers around HuggingFace Trainer / Accelerate.
Must NOT define eval logic — that is eval/'s job.
Must NOT retrain the tokenizer.
"""
