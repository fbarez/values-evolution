# Crosswalks

Crosswalks are **version-controlled research decisions** — not data. They live in this directory and are committed to the repository.

## What is a crosswalk?

A crosswalk maps source-specific survey item codes (e.g. EVS `v72`, ESS `trstprl`) to a common construct space (e.g. `institutional_trust`). It encodes decisions about:

- Which items measure the same underlying construct across surveys
- How to handle wording differences between waves
- How to handle mode effects (face-to-face vs. online administration)
- Which direction of scale reversal is needed for comparability

## Files

| File | Purpose |
|---|---|
| `item_to_construct.csv` | Master mapping: item_id × source → construct_id |
| `wording_change_flags.csv` | Items whose wording changed substantially between waves |
| `mode_adjustment_notes.csv` | Known mode effects and adjustment factors |
| `eb_to_evs.csv` | Eurobarometer → EVS construct mappings |

## Schema — item_to_construct.csv

| Column | Type | Description |
|---|---|---|
| `item_id` | string | Source-specific item code (e.g. `v72`, `trstprl`) |
| `source` | string | `evs` \| `wvs` \| `ess` \| `eurobarometer` |
| `construct_id` | string | Harmonized construct identifier |
| `construct_label` | string | Human-readable construct name |
| `scale_min` | int | Minimum valid response value |
| `scale_max` | int | Maximum valid response value |
| `reversed` | bool | Whether scale is reversed relative to construct direction |
| `waves_applicable` | string | Comma-separated wave years where this mapping applies |
| `notes` | string | Rationale for mapping decision |

## How to add a mapping

1. Add a row to `item_to_construct.csv`
2. If the item has a wording change, add a row to `wording_change_flags.csv`
3. Document the rationale in the `notes` column — this is a research decision
4. Run `pytest tests/test_crosswalks.py` to verify no orphans introduced
5. Commit with a message like `crosswalk: add ESS trstprl → institutional_trust`

## Construct taxonomy

Top-level construct families:

- `social_values` — family, gender roles, marriage, sexuality
- `political_values` — democracy, authority, nationalism, political interest
- `religious_values` — religiosity, church attendance, religious beliefs
- `economic_values` — redistribution, work centrality, ownership, competition
- `interpersonal_trust` — generalised trust in people
- `institutional_trust` — trust in parliament, police, EU, etc.
- `wellbeing` — life satisfaction, happiness, health
- `environment` — post-materialist values (Inglehart), climate concern
- `immigration_attitudes` — attitudes toward immigration and cultural diversity
