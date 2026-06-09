"""Harmonization: apply crosswalks to map raw survey items to constructs.

Reads crosswalks/ CSVs to translate source-specific item codes (e.g. EVS v72,
ESS trstprl) into a common construct space (e.g. institutional_trust).
Outputs RespondentRecord objects consumed by serialize/.

Must NOT read raw files directly — receives parsed dicts from ingest/.
Must NOT modify crosswalk CSVs — those are version-controlled research decisions.
"""
