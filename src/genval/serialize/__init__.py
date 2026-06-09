"""Serialization: convert harmonized RespondentRecord objects to TrainingExample JSONL.

Driven entirely by configs/serialization/ — no hardcoded formats.
Each output corpus is named by the SHA256 of its serialization config
(see genval.utils.hashing).

Must NOT define construct values — receives RespondentRecord from harmonize/.
Must NOT embed logic that belongs in configs/ (e.g. which fields to include).
"""
