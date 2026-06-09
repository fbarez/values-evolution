"""Run evaluation against a checkpoint using the temporal holdout design.

Can evaluate any checkpoint — base (un-tuned) or mid-trained.
Always run against the base checkpoint first to establish baselines
before any mid-training.

Usage:
    python scripts/run_eval.py --config-name base_eval
    python scripts/run_eval.py checkpoint=outputs/checkpoints/run_001 split=val
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()
app = typer.Typer(help=__doc__)


@app.command()
def main(
    checkpoint: str = typer.Option(..., help="HF checkpoint id or local path"),
    split: str = typer.Option("val", help="Split to evaluate: val | test"),
    config_name: str = typer.Option("base_eval", help="Eval config name"),
    corpus_hash: str = typer.Option("", help="Corpus hash to load (from build_corpus.py output)"),
    output_dir: str = typer.Option("outputs/evals", help="Directory for eval results"),
) -> None:
    """Evaluate a checkpoint on the temporal holdout split.

    Pipeline:
        checkpoint + eval targets → generate predictions → compute metrics → write results

    Non-negotiable #6: base checkpoint results must exist in outputs/evals/baseline/
    before any mid-trained run is evaluated.

    Results are written to outputs/evals/{run_id}/results.json.
    """
    output_path = Path(output_dir)
    baseline_path = output_path / "baseline"

    # Enforce non-negotiable #6: base eval must precede mid-trained eval
    if "baseline" not in checkpoint and not baseline_path.exists():
        console.print(
            "[red]BLOCKED: outputs/evals/baseline/ does not exist.[/red]\n"
            "Run the base checkpoint evaluation first:\n"
            "  python scripts/run_eval.py checkpoint=<base_hf_id> --output-dir outputs/evals/baseline"
        )
        raise typer.Exit(1)

    # TODO: implement
    # 1. Load temporal splits from configs/eval/temporal_splits.yaml
    # 2. Load eval targets from data/processed/corpus_{hash}/{split}.jsonl
    # 3. Run inference via genval.inference.generate
    # 4. Parse predictions into ResponseDistribution objects
    # 5. Call genval.eval.metrics.evaluate(targets, predictions)
    # 6. Compute baselines (persistence, cohort_replacement)
    # 7. Print results table; write results.json
    console.print("[yellow]run_eval.py is not yet implemented.[/yellow]")
    raise typer.Exit(0)


if __name__ == "__main__":
    app()
