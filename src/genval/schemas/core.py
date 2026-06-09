"""Core pydantic data contracts for genval.

Single responsibility: define and validate the shapes of all data objects
that cross module boundaries. This module must NOT contain any IO, training,
or serialization logic.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class DataSource(str, Enum):
    EVS = "evs"
    WVS = "wvs"
    ESS = "ess"
    EUROBAROMETER = "eurobarometer"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    NOT_STATED = "not_stated"


class EducationLevel(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    NOT_STATED = "not_stated"


class UrbanRural(str, Enum):
    URBAN = "urban"
    SUBURBAN = "suburban"
    RURAL = "rural"
    NOT_STATED = "not_stated"


# ---------------------------------------------------------------------------
# ResponseDistribution
# ---------------------------------------------------------------------------


class ResponseDistribution(BaseModel):
    """Probability distribution over the response categories of a single survey item.

    Response categories are indexed from 1 (most negative/disagree) to n.
    Probabilities must sum to 1.0 within floating-point tolerance.
    Missing-response proportion is stored separately and does NOT enter the distribution.
    """

    item_id: str = Field(..., description="Crosswalk item identifier (e.g. 'evs_v72')")
    n_categories: int = Field(..., ge=2, le=10)
    probabilities: list[Annotated[float, Field(ge=0.0, le=1.0)]] = Field(
        ..., description="P(response = k) for k in 1..n_categories"
    )
    missing_fraction: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Fraction of respondents who did not answer"
    )
    n_respondents: int = Field(..., ge=1, description="Effective N after applying survey weights")
    survey_weights_applied: bool = Field(default=True)

    @field_validator("probabilities")
    @classmethod
    def probabilities_sum_to_one(cls, v: list[float]) -> list[float]:
        total = sum(v)
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Probabilities must sum to 1.0, got {total:.4f}")
        return v

    @model_validator(mode="after")
    def length_matches_categories(self) -> "ResponseDistribution":
        if len(self.probabilities) != self.n_categories:
            raise ValueError(
                f"Expected {self.n_categories} probabilities, got {len(self.probabilities)}"
            )
        return self


# ---------------------------------------------------------------------------
# ConstructValue
# ---------------------------------------------------------------------------


class ConstructValue(BaseModel):
    """A single construct (e.g. 'interpersonal_trust') for a country-wave or respondent.

    For country-level data, value is the population mean and distribution is the
    full response distribution. For individual respondents, distribution has a single
    non-zero probability at the observed response.
    """

    construct_id: str = Field(..., description="Construct identifier from crosswalks/")
    construct_label: str = Field(..., description="Human-readable label")
    value: float | None = Field(
        default=None, description="Point estimate (population mean or individual response)"
    )
    distribution: ResponseDistribution | None = Field(
        default=None, description="Full response distribution; None for individual records"
    )
    source_items: list[str] = Field(
        default_factory=list,
        description="Item IDs that were averaged to compute this construct",
    )
    is_imputed: bool = Field(default=False)

    @model_validator(mode="after")
    def at_least_one_of_value_or_distribution(self) -> "ConstructValue":
        if self.value is None and self.distribution is None:
            raise ValueError("At least one of value or distribution must be set")
        return self


# ---------------------------------------------------------------------------
# CountryYearProfile
# ---------------------------------------------------------------------------


class CountryYearProfile(BaseModel):
    """Country-level covariates for a given survey year.

    Merged from V-Dem and World Bank WDI at the country × survey_year level.
    All fields are optional because coverage varies by country and year.
    """

    iso3: str = Field(..., min_length=3, max_length=3, description="ISO 3166-1 alpha-3")
    country_name: str
    survey_year: int = Field(..., ge=1970, le=2030)

    # World Bank
    gdp_per_capita_ppp: float | None = None    # constant 2017 intl$
    gdp_growth: float | None = None            # annual % growth
    tertiary_enrolment: float | None = None    # % gross enrolment ratio
    urbanisation: float | None = None          # % urban population
    life_expectancy: float | None = None       # years at birth
    unemployment_rate: float | None = None     # %
    gini: float | None = None                  # 0–100

    # V-Dem
    v2x_libdem: float | None = None            # 0–1
    v2x_polyarchy: float | None = None         # 0–1
    v2x_gender: float | None = None            # 0–1
    v2x_rule: float | None = None              # 0–1


# ---------------------------------------------------------------------------
# RespondentRecord
# ---------------------------------------------------------------------------


class RespondentRecord(BaseModel):
    """One survey respondent's harmonized record after crosswalk application.

    This is the intermediate representation produced by genval.harmonize
    and consumed by genval.serialize. It must NOT be committed to any
    repository (microdata license terms).
    """

    respondent_id: str = Field(..., description="Anonymised internal ID; never real survey ID")
    source: DataSource
    iso3: str = Field(..., min_length=3, max_length=3)
    country_name: str
    survey_year: int = Field(..., ge=1970, le=2030)
    wave: str | None = None

    # Demographics
    age: int | None = Field(default=None, ge=16, le=100)
    gender: Gender = Gender.NOT_STATED
    education: EducationLevel = EducationLevel.NOT_STATED
    urban_rural: UrbanRural = UrbanRural.NOT_STATED
    religion: str | None = None
    employment_status: str | None = None

    # Harmonised construct values
    constructs: list[ConstructValue] = Field(default_factory=list)

    # Country-level context (merged at build time)
    country_profile: CountryYearProfile | None = None

    @field_validator("survey_year")
    @classmethod
    def year_not_in_future(cls, v: int) -> int:
        if v > 2030:
            raise ValueError(f"survey_year {v} is implausibly far in the future")
        return v


# ---------------------------------------------------------------------------
# TrainingExample
# ---------------------------------------------------------------------------


class TrainingExample(BaseModel):
    """One training / eval record in the serialized corpus.

    Non-negotiable #5: structured_target stores numbers; rendered_text is
    derived from those numbers by the serializer. Eval scores structured_target,
    never rendered_text.

    This object is what gets written to JSONL corpora under data/processed/.
    """

    example_id: str = Field(..., description="Stable hash of (iso3, survey_year, respondent_id, serialization_config_hash)")
    serialization_config_hash: str = Field(
        ..., description="SHA256 of the serialization config; corpus directories are named by this"
    )
    source: DataSource
    iso3: str = Field(..., min_length=3, max_length=3)
    survey_year: int = Field(..., ge=1970, le=2030)

    # --- Non-negotiable #5 boundary ---
    structured_target: dict[str, float | list[float]] = Field(
        ...,
        description=(
            "Construct id → point estimate or probability distribution. "
            "This is what eval metrics operate on. "
            "Never merge with rendered_text."
        ),
    )
    rendered_text: str = Field(
        ...,
        description=(
            "Natural-language rendering of structured_target produced by the serializer. "
            "Used as the LM training sequence. "
            "Must be derivable from structured_target alone."
        ),
    )

    # Metadata
    split: str | None = Field(
        default=None, description="train | val | test — assigned at corpus build time"
    )
    n_respondents: int | None = Field(
        default=None, description="For country-level docs: number of respondents aggregated"
    )

    @field_validator("survey_year")
    @classmethod
    def year_not_in_future(cls, v: int) -> int:
        if v > 2030:
            raise ValueError(f"survey_year {v} is implausibly far in the future")
        return v

    @field_validator("structured_target")
    @classmethod
    def target_not_empty(cls, v: dict) -> dict:
        if not v:
            raise ValueError("structured_target must contain at least one construct")
        return v

    @field_validator("rendered_text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("rendered_text must not be empty")
        return v


# ---------------------------------------------------------------------------
# EvalTarget
# ---------------------------------------------------------------------------


class EvalTarget(BaseModel):
    """Ground-truth target for one eval prediction.

    Pairs with a model prediction (also a dict of construct → distribution)
    for metric computation. Only used at eval time; never in training.
    """

    example_id: str
    iso3: str = Field(..., min_length=3, max_length=3)
    survey_year: int
    constructs: dict[str, ResponseDistribution] = Field(
        ..., description="Construct id → observed response distribution"
    )
    n_respondents: int
    country_profile: CountryYearProfile | None = None

    class Config:
        frozen = True   # eval targets are immutable once written
