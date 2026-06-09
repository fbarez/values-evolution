"""V-Dem ingestion module.

Single responsibility: download V-Dem country-year dataset and return
a DataFrame of selected indicators for merging as covariates.

V-Dem is CC BY 4.0 — no credentials needed for bulk download.
Must NOT be used as a training target; covariates only.
"""

from __future__ import annotations

# TODO: implement fetch(), parse(), validate()
