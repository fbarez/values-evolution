"""ESS (European Social Survey) ingestion module.

Single responsibility: download the ESS cumulative file, verify checksum,
parse into raw dicts. Requires ESS_API_KEY in .env for API access,
or downloads bulk CSV from the ESS data portal.

Must NOT apply crosswalks. Must NOT commit data files.
"""

from __future__ import annotations

# TODO: implement fetch(), parse(), validate()
# ESS API docs: https://ess.sikt.no/en/api
