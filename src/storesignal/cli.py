"""
StoreSignal AI — Typer CLI
===========================
Single entry point: python -m storesignal.cli <command>
"""

import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from storesignal.paths import (
    CODE_ROOT,
    DATA_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    REFERENCE_DIR,
    REPORTS_DIR,
)
ROOT = CODE_ROOT
PY = ROOT / ".venv" / "bin" / "python"

app = typer.Typer(add_completion=False, help="StoreSignal AI command-line interface")
console = Console()


def _run(module: str):
    """Run a pipeline module as `python -m storesignal.<module>`."""
    console.print(f"[cyan]Running[/cyan] storesignal.{module}")
    res = subprocess.run(
        [str(PY), "-m", f"storesignal.{module}"],
        check=False, cwd=str(ROOT),
    )
    if res.returncode != 0:
        console.print(f"[red]FAILED:[/red] {module}")
        raise typer.Exit(code=res.returncode)


@app.command()
def pipeline():
    """Run the full pipeline end to end."""
    _run("pipeline")


@app.command()
def mock(): _run("generate_mock_data")

@app.command()
def ingest(): _run("ingestion")

@app.command()
def normalize(): _run("normalization")

@app.command()
def classify(): _run("classification")

@app.command()
def policy(): _run("risk_policy")

@app.command()
def radar(): _run("detection")

@app.command()
def route(): _run("routing")

@app.command()
def fuse(): _run("fusion")

@app.command()
def alerts(): _run("alerts")

@app.command()
def briefs(): _run("briefs")

@app.command()
def evaluate(): _run("evaluate")

@app.command()
def graph(): _run("relationship_graph")

@app.command()
def forecast(): _run("forecasting")


@app.command()
def status():
    """Show artifact readiness."""
    table = Table(title="StoreSignal AI — Status")
    table.add_column("Artifact")
    table.add_column("Ready")
    for name in [
        "raw_feedback.parquet", "normalized_feedback.parquet",
        "predictions.parquet", "escalations.parquet",
        "radar_flags.parquet", "routing.parquet",
        "incidents.parquet", "alerts.parquet",
        "forecasts.parquet", "relationship_graph.json",
    ]:
        p = PROCESSED_DIR / name
        table.add_row(name, "[green]yes[/green]" if p.exists() else "[red]no[/red]")
    briefs_dir = PROCESSED_DIR / "briefs"
    table.add_row("briefs/", "[green]yes[/green]" if briefs_dir.exists() else "[red]no[/red]")
    evalr = REPORTS_DIR / "evaluation_report.json"
    table.add_row("evaluation_report.json", "[green]yes[/green]" if evalr.exists() else "[red]no[/red]")
    console.print(table)


@app.command()
def serve(port: int = 8000):
    """Start FastAPI."""
    subprocess.run(
        [str(ROOT / ".venv" / "bin" / "uvicorn"),
         "storesignal.api:app", "--reload", "--port", str(port)],
        check=False, cwd=str(ROOT),
    )


@app.command()
def ui(port: int = 8501):
    """Start Streamlit."""
    subprocess.run(
        [str(ROOT / ".venv" / "bin" / "streamlit"), "run",
         str(ROOT / "src" / "storesignal" / "ui.py"),
         "--server.port", str(port)],
        check=False, cwd=str(ROOT),
    )


@app.command()
def test(): _run_pytest = subprocess.run([str(PY), "-m", "pytest", "-q", "tests"],
                                         check=False, cwd=str(ROOT))


@app.command()
def import_data(
    source: str = typer.Argument(..., help="CSV / JSONL / Parquet file to import"),
    channel: str = typer.Option(None, "--channel", help="Force channel for all rows"),
):
    """Import an external feedback file through the validation wizard."""
    from storesignal.import_wizard import mapping_template, preview, run_import

    src = Path(source).expanduser().resolve()
    if not src.exists():
        console.print(f"[red]not found:[/red] {src}")
        raise typer.Exit(code=1)
    pv = preview(src)
    if "error" in pv:
        console.print(f"[red]{pv['error']}[/red]")
        raise typer.Exit(code=1)
    console.print(f"[cyan]format:[/cyan] {pv['format']}")
    console.print(f"[cyan]columns:[/cyan] {pv['columns']}")
    mapping = mapping_template()
    result = run_import(src, mapping, channel_override=channel)
    if "error" in result:
        console.print(f"[red]import failed:[/red] {result}")
        raise typer.Exit(code=1)
    table = Table(title=f"Import batch {result['batch_id']}")
    table.add_column("Field"); table.add_column("Value")
    for k in ("rows_in", "rows_valid", "rows_rejected", "warnings", "raw_artifact"):
        table.add_row(k, str(result[k]))
    console.print(table)


@app.command()
def imports():
    """List completed import batches."""
    from storesignal.import_wizard import list_batches
    table = Table(title="Import history")
    table.add_column("batch_id"); table.add_column("rows_valid"); table.add_column("completed_at")
    for b in list_batches():
        table.add_row(b["batch_id"], str(b.get("rows_valid", "?")), b.get("completed_at", "?"))
    console.print(table)


if __name__ == "__main__":
    app()
