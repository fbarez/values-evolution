"""Launch mid-training on the values corpus.

Usage:
    python scripts/run_midtrain.py --config-name midtrain model=qwen2.5-7b
    python scripts/run_midtrain.py corpus_hash=abc123 model=olmo2-7b
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

console = Console()
app = typer.Typer(help=__doc__)


@app.command()
def main(
    config_name: str = typer.Option("midtrain", help="Training config name"),
    corpus_hash: str = typer.Option(..., help="Hash of corpus to train on (from build_corpus.py)"),
    model: str = typer.Option("qwen2.5-7b", help="Model config name"),
    resume_from: str = typer.Option("", help="Resume from checkpoint path"),
) -> None:
    """Mid-train a base checkpoint on the values corpus.

    Requires outputs/evals/baseline/ to exist (non-negotiable #6).
    Uses replay mixing (configs/training/midtrain.yaml replay section)
    to mitigate catastrophic forgetting.
    """
    baseline_path = Path("outputs/evals/baseline")
    if not baseline_path.exists():
        console.print(
            "[red]BLOCKED: outputs/evals/baseline/ does not exist.[/red]\n"
            "Run base eval first: python scripts/run_eval.py checkpoint=<base_id>"
        )
        raise typer.Exit(1)

    corpus_path = Path(f"data/processed/corpus_{corpus_hash}")
    if not corpus_path.exists():
        console.print(
            f"[red]Corpus not found: {corpus_path}[/red]\n"
            "Run: python scripts/build_corpus.py first."
        )
        raise typer.Exit(1)

    # TODO: implement
    # 1. Load configs/training/midtrain.yaml + configs/model/{model}.yaml via Hydra
    # 2. Load corpus from corpus_path/train.jsonl
    # 3. Call genval.training.midtrain.train()
    console.print("[yellow]run_midtrain.py is not yet implemented.[/yellow]")
    raise typer.Exit(0)


if __name__ == "__main__":
    app()
