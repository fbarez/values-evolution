"""Build a serialized training corpus from harmonized survey data.

Runs the full harmonize → serialize pipeline for a given serialization config.
Output is written to data/processed/corpus_{hash}/ where hash is the SHA256
of the serialization config.

Usage:
    python scripts/build_corpus.py --config-name country_year_doc
    python scripts/build_corpus.py serialization=respondent_profile
"""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()
app = typer.Typer(help=__doc__)


@app.command()
def main(
    config_name: str = typer.Option("country_year_doc", help="Serialization config name (from configs/serialization/)"),
    dry_run: bool = typer.Option(False, help="Print what would be done without writing"),
    overwrite: bool = typer.Option(False, help="Overwrite existing corpus if hash matches"),
) -> None:
    """Harmonize raw data and serialize to a hash-named corpus directory.

    Pipeline:
        data/raw/ → ingest → harmonize (crosswalks) → serialize → data/processed/corpus_{hash}/

    The output directory name encodes the exact serialization config,
    so different configs produce different directories automatically.
    """
    # TODO: implement
    # 1. Load serialization config via Hydra
    # 2. Compute config hash (genval.utils.hashing.hash_config)
    # 3. Check if corpus_{hash}/ already exists; exit early if not overwrite
    # 4. Load data/interim/ parquet files
    # 5. Apply crosswalks (genval.harmonize.apply_crosswalks)
    # 6. Serialize to TrainingExample JSONL (genval.serialize.builder)
    # 7. Apply temporal splits from configs/eval/temporal_splits.yaml
    # 8. Write train/val/test JSONL + manifest
    # 9. Print summary: n_examples per split, output path
    console.print("[yellow]build_corpus.py is not yet implemented.[/yellow]")
    console.print("Implement harmonize + serialize modules first.")
    raise typer.Exit(0)


if __name__ == "__main__":
    app()
