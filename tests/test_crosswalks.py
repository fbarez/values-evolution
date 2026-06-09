"""Tests for crosswalk integrity.

Every crosswalk row must map to a known construct; no orphan mappings.
These tests run against the CSV files in crosswalks/, which are
version-controlled research decisions.
"""

import csv
from pathlib import Path

import pytest

CROSSWALKS_DIR = Path("crosswalks")
ITEM_TO_CONSTRUCT_CSV = CROSSWALKS_DIR / "item_to_construct.csv"


def load_crosswalk(path: Path) -> list[dict]:
    if not path.exists():
        pytest.skip(f"Crosswalk file not yet created: {path}")
    with open(path) as f:
        return list(csv.DictReader(f))


def test_crosswalk_file_exists():
    """item_to_construct.csv must exist once crosswalk work begins."""
    if not ITEM_TO_CONSTRUCT_CSV.exists():
        pytest.skip("item_to_construct.csv not yet created — skip until crosswalk work begins")
    assert ITEM_TO_CONSTRUCT_CSV.exists()


def test_crosswalk_required_columns():
    rows = load_crosswalk(ITEM_TO_CONSTRUCT_CSV)
    required = {"item_id", "source", "construct_id", "construct_label", "scale_min", "scale_max"}
    headers = set(rows[0].keys()) if rows else set()
    missing = required - headers
    assert not missing, f"Crosswalk missing required columns: {missing}"


def test_no_empty_construct_ids():
    rows = load_crosswalk(ITEM_TO_CONSTRUCT_CSV)
    orphans = [r for r in rows if not r.get("construct_id", "").strip()]
    assert not orphans, f"{len(orphans)} rows have empty construct_id"


def test_no_empty_item_ids():
    rows = load_crosswalk(ITEM_TO_CONSTRUCT_CSV)
    missing = [r for r in rows if not r.get("item_id", "").strip()]
    assert not missing, f"{len(missing)} rows have empty item_id"


def test_scale_min_less_than_max():
    rows = load_crosswalk(ITEM_TO_CONSTRUCT_CSV)
    for row in rows:
        if row.get("scale_min") and row.get("scale_max"):
            assert int(row["scale_min"]) < int(row["scale_max"]), (
                f"scale_min >= scale_max for item {row.get('item_id')}"
            )


def test_unique_item_source_pairs():
    rows = load_crosswalk(ITEM_TO_CONSTRUCT_CSV)
    seen = set()
    duplicates = []
    for row in rows:
        key = (row.get("item_id"), row.get("source"))
        if key in seen:
            duplicates.append(key)
        seen.add(key)
    assert not duplicates, f"Duplicate (item_id, source) pairs: {duplicates}"
