"""EVS/WVS ingestion module.

Single responsibility: download the EVS/WVS joint longitudinal file from GESIS,
verify its checksum, and parse it into a list of raw (pre-crosswalk) dicts.

Must NOT apply crosswalks. Must NOT commit data files.
"""

from __future__ import annotations

# TODO: implement fetch(), parse(), validate()
# fetch():
#   - Read GESIS_USERNAME / GESIS_PASSWORD from .env
#   - POST to GESIS login endpoint to obtain session cookie
#   - GET the download URL from configs/data/evs.yaml
#   - Stream to data/raw/ZA7503_v3-0-0.dta
#   - Verify SHA256 against configs/data/evs.yaml expected_sha256
#   - Raise on mismatch
#
# parse():
#   - Read the Stata file with pandas.read_stata()
#   - Return a list[dict] with only the columns needed by harmonize/
#   - Preserve original item codes (e.g. v72) — crosswalk maps these to constructs
#
# validate():
#   - Check expected waves are present (1981, 1990, 1999, 2008, 2017)
#   - Check expected country count per wave
#   - Log warnings for unexpected missingness patterns
