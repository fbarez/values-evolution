"""World Bank WDI ingestion module.

Single responsibility: download World Development Indicators bulk CSV and
return a DataFrame of selected indicators for merging as covariates.

WDI is CC BY 4.0 — no credentials needed.
Must NOT be used as a training target; covariates only.
"""

from __future__ import annotations

# TODO: implement fetch(), parse(), validate()
