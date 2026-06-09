"""Fetch raw survey data from GESIS, ESS, V-Dem, and World Bank.

Downloads each source, verifies SHA256 checksums against data/MANIFEST.md,
and saves to data/raw/. Requires credentials in .env.

Usage:
    python scripts/fetch_data.py --config-name fetch_all
    python scripts/fetch_data.py source=evs
"""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()
app = typer.Typer(help=__doc__)


@app.command()
def main(
    source: str = typer.Option("all", help="Data source to fetch: evs | ess | vdem | wdi | all"),
    verify_only: bool = typer.Option(False, help="Only verify checksums, don't download"),
    config_dir: str = typer.Option("configs", help="Path to configs directory"),
) -> None:
    """Download raw survey data and verify checksums.

    Credentials are read from .env (GESIS_USERNAME, GESIS_PASSWORD, ESS_API_KEY).
    Downloaded files are saved to data/raw/ and verified against data/MANIFEST.md.
    """
    # TODO: implement
    # 1. Load .env with python-dotenv
    # 2. Load configs/data/{source}.yaml
    # 3. Call genval.ingest.{source}.fetch() for each source
    # 4. Verify SHA256 against MANIFEST.md
    # 5. Print summary table via rich
    console.print("[yellow]fetch_data.py is not yet implemented.[/yellow]")
    console.print("Implement genval.ingest.{evs,ess,vdem,wdi}.fetch() first.")
    raise typer.Exit(0)


if __name__ == "__main__":
    app()
