from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from cadx.demos import pan_tilt_2axis
from cadx.schemas import ProductSpec
from cadx.pipeline.orchestrator import run_pan_tilt_workflow


WorkflowRun = Callable[[Path, ProductSpec, str], Path]


@dataclass(frozen=True)
class WorkflowDescriptor:
    workflow_id: str
    template_id: str
    supported_product_spec_ids: tuple[str, ...]
    description: str
    run: WorkflowRun

    def supports_product_spec(self, spec: ProductSpec) -> bool:
        return spec.id in self.supported_product_spec_ids


def _run_pan_tilt(out_dir: Path, spec: ProductSpec, run_id: str) -> Path:
    return run_pan_tilt_workflow(out_dir, spec=spec, run_id=run_id)


PAN_TILT_WORKFLOW = WorkflowDescriptor(
    workflow_id="pan_tilt_2axis_demo",
    template_id="pan_tilt_2axis_demo",
    supported_product_spec_ids=(pan_tilt_2axis.product_spec().id,),
    description="Canonical CADX MVP pan/tilt two-axis demo workflow.",
    run=_run_pan_tilt,
)

_WORKFLOWS: tuple[WorkflowDescriptor, ...] = (PAN_TILT_WORKFLOW,)


def list_workflows() -> tuple[WorkflowDescriptor, ...]:
    return _WORKFLOWS


def supported_workflow_ids() -> tuple[str, ...]:
    return tuple(workflow.workflow_id for workflow in _WORKFLOWS)


def select_workflow(spec: ProductSpec) -> WorkflowDescriptor:
    explicit_id = spec.workflow_id or spec.template_id
    if explicit_id:
        for workflow in _WORKFLOWS:
            if explicit_id in {workflow.workflow_id, workflow.template_id}:
                if workflow.supports_product_spec(spec):
                    return workflow
                raise ValueError(
                    f"Workflow {explicit_id!r} does not support product_spec_id={spec.id!r}; "
                    f"supported product specs: {', '.join(workflow.supported_product_spec_ids)}"
                )
        raise ValueError(
            f"Unknown CADX workflow/template {explicit_id!r}; supported workflow IDs: {', '.join(supported_workflow_ids())}"
        )

    matches = [workflow for workflow in _WORKFLOWS if workflow.supports_product_spec(spec)]
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise ValueError(
            f"Ambiguous workflow selection for product_spec_id={spec.id!r}; set workflow_id explicitly. "
            f"Supported workflow IDs: {', '.join(supported_workflow_ids())}"
        )
    raise ValueError(
        f"No CADX workflow supports product_spec_id={spec.id!r}; supported workflow IDs: {', '.join(supported_workflow_ids())}"
    )
