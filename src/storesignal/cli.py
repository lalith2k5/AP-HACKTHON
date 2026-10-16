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

ROOT = Path.home() / "storesignal-ai"
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
        p = ROOT / "data" / "processed" / name
        table.add_row(name, "[green]yes[/green]" if p.exists() else "[red]no[/red]")
    briefs_dir = ROOT / "data" / "processed" / "briefs"
    table.add_row("briefs/", "[green]yes[/green]" if briefs_dir.exists() else "[red]no[/red]")
    evalr = ROOT / "data" / "evaluation" / "reports" / "evaluation_report.json"
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


if __name__ == "__main__":
    app()
