"""Tests for genval.schemas — data contract validation."""

import pytest
from pydantic import ValidationError

from genval.schemas import (
    ConstructValue,
    EvalTarget,
    RespondentRecord,
    ResponseDistribution,
    TrainingExample,
)
from genval.schemas.core import DataSource, EducationLevel, Gender

# ---------------------------------------------------------------------------
# ResponseDistribution
# ---------------------------------------------------------------------------


def make_dist(item_id: str = "test_item", probs: list[float] | None = None) -> ResponseDistribution:
    probs = probs or [0.1, 0.2, 0.4, 0.2, 0.1]
    return ResponseDistribution(
        item_id=item_id,
        n_categories=len(probs),
        probabilities=probs,
        n_respondents=500,
    )


def test_distribution_valid():
    dist = make_dist()
    assert len(dist.probabilities) == 5
    assert abs(sum(dist.probabilities) - 1.0) < 0.01


def test_distribution_rejects_non_unit_sum():
    with pytest.raises(ValidationError, match="sum to 1.0"):
        ResponseDistribution(
            item_id="bad",
            n_categories=3,
            probabilities=[0.1, 0.1, 0.1],  # sums to 0.3
            n_respondents=100,
        )


def test_distribution_rejects_length_mismatch():
    with pytest.raises(ValidationError):
        ResponseDistribution(
            item_id="bad",
            n_categories=3,
            probabilities=[0.5, 0.5],  # length 2, not 3
            n_respondents=100,
        )


# ---------------------------------------------------------------------------
# ConstructValue
# ---------------------------------------------------------------------------


def test_construct_value_with_distribution():
    cv = ConstructValue(
        construct_id="interpersonal_trust",
        construct_label="Interpersonal trust",
        distribution=make_dist("trust_item"),
    )
    assert cv.distribution is not None


def test_construct_value_requires_value_or_distribution():
    with pytest.raises(ValidationError, match="At least one"):
        ConstructValue(
            construct_id="trust",
            construct_label="Trust",
            value=None,
            distribution=None,
        )


# ---------------------------------------------------------------------------
# RespondentRecord
# ---------------------------------------------------------------------------


def test_respondent_record_minimal():
    rec = RespondentRecord(
        respondent_id="anon_001",
        source=DataSource.EVS,
        iso3="DEU",
        country_name="Germany",
        survey_year=2008,
    )
    assert rec.gender == Gender.NOT_STATED
    assert rec.education == EducationLevel.NOT_STATED


def test_respondent_record_with_constructs():
    rec = RespondentRecord(
        respondent_id="anon_002",
        source=DataSource.ESS,
        iso3="FRA",
        country_name="France",
        survey_year=2006,
        age=42,
        gender=Gender.FEMALE,
        constructs=[
            ConstructValue(
                construct_id="trust",
                construct_label="Trust",
                value=3.5,
                distribution=make_dist("trust_item"),
            )
        ],
    )
    assert len(rec.constructs) == 1


# ---------------------------------------------------------------------------
# TrainingExample — non-negotiable #5
# ---------------------------------------------------------------------------


def test_training_example_separates_target_and_text():
    ex = TrainingExample(
        example_id="ex_001",
        serialization_config_hash="abc123",
        source=DataSource.EVS,
        iso3="DEU",
        survey_year=2000,
        structured_target={"interpersonal_trust": 3.2, "institutional_trust": 2.8},
        rendered_text="Country: Germany (DEU), Survey year: 2000\nValues: ...",
        split="train",
    )
    # structured_target and rendered_text are separate — the core non-negotiable
    assert isinstance(ex.structured_target, dict)
    assert isinstance(ex.rendered_text, str)
    assert "interpersonal_trust" in ex.structured_target


def test_training_example_rejects_empty_target():
    with pytest.raises(ValidationError, match="at least one construct"):
        TrainingExample(
            example_id="bad",
            serialization_config_hash="abc",
            source=DataSource.EVS,
            iso3="DEU",
            survey_year=2000,
            structured_target={},
            rendered_text="Some text",
        )


def test_training_example_rejects_empty_text():
    with pytest.raises(ValidationError, match="not be empty"):
        TrainingExample(
            example_id="bad",
            serialization_config_hash="abc",
            source=DataSource.EVS,
            iso3="DEU",
            survey_year=2000,
            structured_target={"trust": 3.0},
            rendered_text="   ",
        )


# ---------------------------------------------------------------------------
# EvalTarget
# ---------------------------------------------------------------------------


def test_eval_target_is_immutable():
    target = EvalTarget(
        example_id="tgt_001",
        iso3="GBR",
        survey_year=2017,
        constructs={"trust": make_dist("trust_item")},
        n_respondents=1200,
    )
    with pytest.raises(ValidationError):
        target.iso3 = "FRA"
