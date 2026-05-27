from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from cadx.schemas import ProductSpec
from cadx.pipeline.workflows import select_workflow


@dataclass(frozen=True)
class RunContext:
    """Minimal v0.2 run identity and output location for CADX workflows."""

    run_id: str
    run_dir: Path
    spec_path: Path | None = None


def load_product_spec(path: Path) -> ProductSpec:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Product spec JSON parse failed: {path}: {exc}") from exc
    try:
        return ProductSpec.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Product spec validation failed: {path}: {exc}") from exc


def run_from_spec(spec_path: Path, run_id: str, runs_root: Path) -> Path:
    spec = load_product_spec(spec_path)
    context = RunContext(run_id=run_id, run_dir=runs_root / run_id, spec_path=spec_path)
    workflow = select_workflow(spec)
    return workflow.run(context.run_dir, spec, context.run_id)
