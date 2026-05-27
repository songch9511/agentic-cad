from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from cadx.demos import pan_tilt_2axis
from cadx.pipeline.orchestrator import run_pan_tilt_workflow, write_artifact_manifest, write_json, write_report
from cadx.schemas import ProductSpec, ValidationReport


SUPPORTED_WORKFLOW_ID = "pan_tilt_2axis_demo"
DEFAULT_ADAPTER_PROVIDER = "cadx"
DEFAULT_ADAPTER_MODEL = "deterministic-pan-tilt-fallback-v1"
DEFAULT_ADAPTER_MODE = "deterministic_fallback"


class AgentAdapterConfig(BaseModel):
    provider: str = Field(default=DEFAULT_ADAPTER_PROVIDER, pattern=r"^[A-Za-z0-9_.-]+$")
    model: str = Field(default=DEFAULT_ADAPTER_MODEL, pattern=r"^[A-Za-z0-9_.:-]+$")
    mode: Literal["deterministic_fallback", "mock"] = DEFAULT_ADAPTER_MODE

    def trace_metadata(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "mode": self.mode,
            "external_call_performed": False,
            "network_access": "disabled",
            "fallback": "deterministic_pan_tilt_2axis_demo",
        }


class AgentRunRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    run_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_.-]+$")
    adapter: AgentAdapterConfig = Field(default_factory=AgentAdapterConfig)


class AgentModifyRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    run_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_.-]+$")
    adapter: AgentAdapterConfig = Field(default_factory=AgentAdapterConfig)


@dataclass(frozen=True)
class AgentRunResult:
    run_id: str
    run_dir: Path
    trace: dict[str, Any]


def _slug(text: str, prefix: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", text.strip().lower()).strip("_")[:48]
    return f"{prefix}_{slug or 'request'}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _unsupported_requirements(prompt: str) -> list[str]:
    prompt_lower = prompt.lower()
    unsupported: list[str] = []
    checks = {
        "fusion_360_live_viewer": ["fusion", "live viewer"],
        "general_freeform_cad": ["anything", "arbitrary", "freeform", "free-form"],
        "cloud_vendor_part_search": ["web search", "vendor catalog", "online catalog", "download step"],
        "new_cad_kernel": ["solidworks", "onshape", "freecad"],
        "unsupported_template_request": ["gearbox", "drone", "enclosure", "bracket", "robot arm", "gripper"],
    }
    for requirement, tokens in checks.items():
        if any(token in prompt_lower for token in tokens):
            unsupported.append(requirement)
    if SUPPORTED_WORKFLOW_ID not in prompt_lower and "pan" not in prompt_lower and "tilt" not in prompt_lower:
        unsupported.append("non_pan_tilt_prompt_mapped_to_supported_template")
    return sorted(set(unsupported))


def _generated_spec(prompt: str) -> ProductSpec:
    base = pan_tilt_2axis.product_spec()
    assumptions = list(base.assumptions) + [
        "Agent harness v1 uses deterministic fallback mapping; no external LLM call is required.",
        "Only the pan_tilt_2axis_demo workflow/template is supported in this iteration.",
        f"Original natural-language prompt: {prompt}",
    ]
    unsupported = _unsupported_requirements(prompt)
    if unsupported:
        assumptions.append(f"Unsupported request aspects were recorded instead of hallucinated: {', '.join(unsupported)}.")
    return base.model_copy(update={"workflow_id": SUPPORTED_WORKFLOW_ID, "template_id": SUPPORTED_WORKFLOW_ID, "assumptions": assumptions})


def _validation_summary(run_dir: Path) -> dict[str, Any]:
    validation_path = run_dir / "validation_report.json"
    if not validation_path.exists():
        return {"status": "missing", "gate_count": 0, "metrics": {}}
    import json

    validation = json.loads(validation_path.read_text())
    return {
        "status": validation.get("status", "missing"),
        "gate_count": len(validation.get("gates", [])),
        "geometry_backend": validation.get("metrics", {}).get("geometry_backend", "unknown"),
        "assembly_step_bytes": validation.get("metrics", {}).get("assembly_step_bytes", 0),
    }


def _tool_call(order: int, name: str, inputs: dict[str, Any], outputs: dict[str, Any], status: str = "pass") -> dict[str, Any]:
    return {
        "order": order,
        "timestamp": _utc_now(),
        "tool_name": name,
        "action": name,
        "inputs": inputs,
        "outputs": outputs,
        "artifact_refs": outputs.get("artifact_refs", []),
        "status": status,
    }


def _refresh_agent_artifact_integration(run_dir: Path, trace: dict[str, Any]) -> dict[str, Any]:
    write_json(run_dir / "agent_trace.json", trace)
    validation_path = run_dir / "validation_report.json"
    if validation_path.exists():
        import json

        report = ValidationReport.model_validate(json.loads(validation_path.read_text()))
        write_artifact_manifest(run_dir, report)
        write_report(run_dir, report)
    return trace


def _trace_base(
    *,
    run_id: str,
    parent_run_id: str | None,
    request_type: Literal["generate", "modify"],
    prompt: str,
    adapter: AgentAdapterConfig,
    spec: ProductSpec,
    unsupported: list[str],
    validation_summary: dict[str, Any],
    tool_calls: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "agent_trace.v2",
        "id": f"agent_trace_{run_id}",
        "run_id": run_id,
        "parent_run_id": parent_run_id,
        "request_type": request_type,
        "prompt": prompt,
        "adapter": adapter.trace_metadata(),
        "provider": adapter.provider,
        "model": adapter.model,
        "mode": adapter.mode,
        "selected_workflow": SUPPORTED_WORKFLOW_ID,
        "selected_template": SUPPORTED_WORKFLOW_ID,
        "mapper": "deterministic_pan_tilt_fallback_v2",
        "assumptions": spec.assumptions,
        "unsupported_requirements": unsupported,
        "generated_product_spec": spec.model_dump(mode="json"),
        "tool_calls": tool_calls,
        "actions": [
            {"tool": call["tool_name"], "action": call["action"], "status": call["status"]}
            for call in tool_calls
        ],
        "validation_summary": validation_summary,
    }


def create_agent_run(prompt: str, runs_root: Path, run_id: str | None = None, adapter: AgentAdapterConfig | None = None) -> AgentRunResult:
    adapter = adapter or AgentAdapterConfig()
    resolved_run_id = run_id or _slug(prompt, "agent_run")
    unsupported = _unsupported_requirements(prompt)
    spec = _generated_spec(prompt)
    mapper_call = _tool_call(
        1,
        "llm_adapter.map_prompt_to_product_spec",
        {"prompt": prompt, "adapter": adapter.trace_metadata()},
        {
            "selected_workflow": SUPPORTED_WORKFLOW_ID,
            "selected_template": SUPPORTED_WORKFLOW_ID,
            "unsupported_requirements": unsupported,
            "artifact_refs": ["product_spec.json"],
        },
    )
    run_dir = run_pan_tilt_workflow(runs_root / resolved_run_id, spec=spec, run_id=resolved_run_id)
    validation_summary = _validation_summary(run_dir)
    tool_calls = [
        mapper_call,
        _tool_call(2, "cadx.workflow.run_pan_tilt_2axis_demo", {"run_id": resolved_run_id}, {"artifact_refs": ["assembly.step", "robot.urdf", "artifact_manifest.json"]}),
        _tool_call(3, "cadx.validation.summarize", {"run_id": resolved_run_id}, {"validation_summary": validation_summary, "artifact_refs": ["validation_report.json"]}, validation_summary["status"]),
    ]
    trace = _trace_base(
        run_id=resolved_run_id,
        parent_run_id=None,
        request_type="generate",
        prompt=prompt,
        adapter=adapter,
        spec=spec,
        unsupported=unsupported,
        validation_summary=validation_summary,
        tool_calls=tool_calls,
    )
    _refresh_agent_artifact_integration(run_dir, trace)
    return AgentRunResult(run_id=resolved_run_id, run_dir=run_dir, trace=trace)


def modify_agent_run(parent_run_id: str, prompt: str, runs_root: Path, run_id: str | None = None, adapter: AgentAdapterConfig | None = None) -> AgentRunResult:
    adapter = adapter or AgentAdapterConfig()
    parent_dir = runs_root / parent_run_id
    if not parent_dir.exists():
        raise FileNotFoundError(f"Unknown parent run: {parent_run_id}")
    resolved_run_id = run_id or f"{parent_run_id}_mod_{_slug(prompt, 'request').removeprefix('request_')}"
    parent_spec_path = parent_dir / "product_spec.json"
    import json

    parent_spec = ProductSpec.model_validate(json.loads(parent_spec_path.read_text()))
    unsupported = _unsupported_requirements(prompt)
    child_assumptions = list(parent_spec.assumptions) + [f"Modification request: {prompt}"]
    if unsupported:
        child_assumptions.append(f"Unsupported modification aspects were recorded instead of applied: {', '.join(unsupported)}.")
    child_spec = parent_spec.model_copy(update={"assumptions": child_assumptions, "workflow_id": SUPPORTED_WORKFLOW_ID, "template_id": SUPPORTED_WORKFLOW_ID})
    run_dir = run_pan_tilt_workflow(runs_root / resolved_run_id, spec=child_spec, run_id=resolved_run_id)
    modification_request = {
        "id": f"modification_{resolved_run_id}",
        "parent_run_id": parent_run_id,
        "child_run_id": resolved_run_id,
        "prompt": prompt,
        "adapter": adapter.trace_metadata(),
        "supported_change_policy": "deterministic_trace_only_v1",
        "applied_changes": [{"field": "assumptions", "operation": "append", "value": f"Modification request: {prompt}"}],
        "unsupported_requirements": unsupported,
    }
    delta = {
        "id": f"delta_{resolved_run_id}",
        "parent_run_id": parent_run_id,
        "child_run_id": resolved_run_id,
        "changed_spec_fields": ["assumptions", "workflow_id", "template_id"],
        "unchanged_spec_fields": ["functional_requirements", "constraints", "preferred_parts", "avoid_parts", "output_requirements"],
        "summary": "Modification harness v1 records the natural-language delta and reruns the constrained pan_tilt workflow without arbitrary geometry edits.",
    }
    write_json(run_dir / "modification_request.json", modification_request)
    write_json(run_dir / "delta_summary.json", delta)
    validation_summary = _validation_summary(run_dir)
    tool_calls = [
        _tool_call(
            1,
            "llm_adapter.map_modification_to_spec_patch",
            {"prompt": prompt, "parent_run_id": parent_run_id, "adapter": adapter.trace_metadata()},
            {"unsupported_requirements": unsupported, "artifact_refs": ["modification_request.json", "delta_summary.json"]},
        ),
        _tool_call(2, "cadx.workflow.run_pan_tilt_2axis_demo_child", {"run_id": resolved_run_id, "parent_run_id": parent_run_id}, {"artifact_refs": ["product_spec.json", "assembly.step", "robot.urdf"]}),
        _tool_call(3, "cadx.validation.summarize_child", {"run_id": resolved_run_id}, {"validation_summary": validation_summary, "artifact_refs": ["validation_report.json"]}, validation_summary["status"]),
    ]
    trace = _trace_base(
        run_id=resolved_run_id,
        parent_run_id=parent_run_id,
        request_type="modify",
        prompt=prompt,
        adapter=adapter,
        spec=child_spec,
        unsupported=unsupported,
        validation_summary=validation_summary,
        tool_calls=tool_calls,
    ) | {"modification_request": modification_request, "delta_summary": delta}
    _refresh_agent_artifact_integration(run_dir, trace)
    write_json(run_dir / "modification_request.json", modification_request)
    write_json(run_dir / "delta_summary.json", delta)
    return AgentRunResult(run_id=resolved_run_id, run_dir=run_dir, trace=trace)
