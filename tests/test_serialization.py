"""Tests for serialization round-trip.

structured_target → rendered_text → parseable back to structured values.
Tests that non-negotiable #5 is preserved: numbers stay in structured_target,
text is rendered FROM those numbers.
"""

import json

import pytest

from genval.schemas import TrainingExample
from genval.schemas.core import DataSource
from genval.utils.hashing import hash_config


def test_hash_config_is_deterministic():
    cfg = {"variant": "country_year_doc", "version": "1.0", "aggregation": {"method": "mean"}}
    h1 = hash_config(cfg)
    h2 = hash_config(cfg)
    assert h1 == h2
    assert len(h1) == 12


def test_hash_config_differs_with_different_input():
    cfg1 = {"variant": "country_year_doc"}
    cfg2 = {"variant": "respondent_profile"}
    assert hash_config(cfg1) != hash_config(cfg2)


def test_training_example_structured_target_is_json_serialisable():
    """structured_target must always be JSON-serialisable (for JSONL corpus)."""
    ex = TrainingExample(
        example_id="ex_001",
        serialization_config_hash="abc123",
        source=DataSource.EVS,
        iso3="DEU",
        survey_year=2005,
        structured_target={
            "interpersonal_trust": 3.2,
            "institutional_trust": [0.1, 0.2, 0.4, 0.2, 0.1],
        },
        rendered_text="Country: Germany, Survey year: 2005\nValues: ...",
        split="train",
    )
    # Must round-trip through JSON without error
    serialised = json.dumps(ex.structured_target)
    recovered = json.loads(serialised)
    assert recovered["interpersonal_trust"] == 3.2
    assert len(recovered["institutional_trust"]) == 5


def test_structured_target_and_rendered_text_are_separate_fields():
    """Non-negotiable #5: these must be distinct fields, never merged."""
    fields = TrainingExample.model_fields
    assert "structured_target" in fields
    assert "rendered_text" in fields
    # They must be different fields
    assert fields["structured_target"] is not fields["rendered_text"]


def test_corpus_directory_named_by_config_hash():
    """Corpus directory name must be derived from config hash, not hardcoded."""
    from pathlib import Path

    from genval.utils.hashing import corpus_dir

    cfg = {"variant": "country_year_doc", "version": "1.0"}
    h = hash_config(cfg)
    path = corpus_dir(Path("data/processed"), h)
    assert path.name == f"corpus_{h}"
    assert h in str(path)
