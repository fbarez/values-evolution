"""Apply crosswalk mappings to raw respondent dicts.

Single responsibility: read crosswalks/item_to_construct.csv and map
raw item responses to harmonized ConstructValue objects.

Must NOT define the mappings — those live in crosswalks/.
Must NOT write output files — returns Python objects.
"""

from __future__ import annotations

# TODO: implement
# Steps:
# 1. Load crosswalks/item_to_construct.csv as a lookup table
# 2. For each raw respondent dict, map item codes → construct values
# 3. Apply scale reversal flags (crosswalks/wording_change_flags.csv)
# 4. Return RespondentRecord objects
