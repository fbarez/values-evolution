"""Data ingestion: fetch, parse, and validate raw survey data from external sources.

Each submodule handles one source (EVS, ESS, Eurobarometer, V-Dem, WDI).
Must NOT apply crosswalks or harmonize constructs — that is harmonize's job.
Must NOT commit or redistribute microdata.
"""
