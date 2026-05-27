from __future__ import annotations

from pathlib import Path
import typer

from cadx.pipeline.orchestrator import run_pan_tilt_demo
from cadx.pipeline.runner import run_from_spec

app = typer.Typer(help="CADX CLI")

RUNS_ROOT = Path("/Users/daniel/.cobra/workspace/CADX/runs")
DEFAULT_RUN = RUNS_ROOT / "pan_tilt_2axis_demo"


@app.command("run-demo")
def run_demo(name: str = "pan_tilt_2axis_demo", out: Path = DEFAULT_RUN) -> None:
    if name != "pan_tilt_2axis_demo":
        raise typer.BadParameter("Sprint 0 only supports pan_tilt_2axis_demo")
    run_dir = run_pan_tilt_demo(out)
    typer.echo(f"Wrote CADX Sprint 0 demo artifacts to {run_dir}")


@app.command("run")
def run(spec: Path = typer.Option(..., "--spec", help="Path to a ProductSpec JSON file."), run_id: str = typer.Option(..., "--run-id", help="Run id / output directory name under runs/.")) -> None:
    run_dir = run_from_spec(spec, run_id=run_id, runs_root=RUNS_ROOT)
    typer.echo(f"Wrote CADX run artifacts to {run_dir}")


@app.command("validate")
def validate(run: Path = DEFAULT_RUN) -> None:
    report = run / "validation_report.json"
    if not report.exists():
        raise typer.BadParameter(f"Missing validation report: {report}")
    typer.echo(report.read_text())


if __name__ == "__main__":
    app()
