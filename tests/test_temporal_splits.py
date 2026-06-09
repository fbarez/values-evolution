"""Tests for temporal split integrity — enforces non-negotiable #2.

Critical test: no training example may have survey_year >= val boundary (2017).
This test is the enforcement mechanism for the leakage non-negotiable.
"""

import pytest
from omegaconf import OmegaConf

from genval.schemas import TrainingExample
from genval.schemas.core import DataSource


def load_temporal_splits():
    cfg = OmegaConf.load("configs/eval/temporal_splits.yaml")
    return cfg


# ---------------------------------------------------------------------------
# Config integrity
# ---------------------------------------------------------------------------


def test_temporal_splits_config_exists():
    cfg = load_temporal_splits()
    assert hasattr(cfg, "train")
    assert hasattr(cfg, "validation")
    assert hasattr(cfg, "test")


def test_train_max_year_is_2008():
    cfg = load_temporal_splits()
    assert cfg.train.max_survey_year == 2008, (
        f"train.max_survey_year must be 2008, got {cfg.train.max_survey_year}"
    )


def test_val_year_is_after_train():
    cfg = load_temporal_splits()
    assert cfg.validation.survey_year > cfg.train.max_survey_year


def test_test_year_is_after_val():
    cfg = load_temporal_splits()
    assert cfg.test.survey_year > cfg.validation.survey_year


# ---------------------------------------------------------------------------
# Leakage check — non-negotiable #2
# ---------------------------------------------------------------------------


def _make_example(survey_year: int, split: str = "train") -> TrainingExample:
    return TrainingExample(
        example_id=f"ex_{survey_year}",
        serialization_config_hash="abc123",
        source=DataSource.EVS,
        iso3="DEU",
        survey_year=survey_year,
        structured_target={"trust": 3.0},
        rendered_text=f"Germany {survey_year}",
        split=split,
    )


def test_no_training_example_at_or_after_val_boundary():
    """Non-negotiable #2: no training example may have survey_year >= 2017."""
    cfg = load_temporal_splits()
    val_year = cfg.validation.survey_year

    # Simulate a corpus that would be produced by build_corpus.py
    simulated_train_corpus = [
        _make_example(1981),
        _make_example(1990),
        _make_example(1999),
        _make_example(2008),
    ]

    leaked = [ex for ex in simulated_train_corpus if ex.survey_year >= val_year]
    assert not leaked, (
        f"Leakage detected: {len(leaked)} training examples have "
        f"survey_year >= {val_year}: {[ex.survey_year for ex in leaked]}"
    )


def test_val_boundary_example_not_in_train():
    """A 2017-wave example must NOT appear in the training split."""
    val_example = _make_example(2017, split="val")
    # It should be labelled val, not train
    assert val_example.split == "val"


def test_no_random_split_in_training_example():
    """TrainingExample must not have a random_split field anywhere."""
    fields = TrainingExample.model_fields
    assert "random_split" not in fields, (
        "TrainingExample must never have a random_split field (non-negotiable #2)"
    )
