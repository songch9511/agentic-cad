from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover - exercised by optional dependency import behavior
    raise RuntimeError("CADX API requires the optional dependency extra: pip install -e '.[api]'") from exc

from cadx.agent import AgentModifyRequest, AgentRunRequest, create_agent_run, modify_agent_run
from cadx.pipeline.runner import run_from_spec
from cadx.pipeline.workflows import list_workflows

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_ROOT = REPO_ROOT / "runs"


class RunCreateRequest(BaseModel):
    spec_path: str = Field(..., description="ProductSpec JSON path relative to the CADX repo root or runs root.")
    run_id: str = Field(..., pattern=r"^[A-Za-z0-9_.-]+$")


def _safe_relative_path(raw_path: str, root: Path) -> Path:
    candidate = (root / raw_path).resolve()
    root_resolved = root.resolve()
    if candidate == root_resolved or root_resolved in candidate.parents:
        return candidate
    raise HTTPException(status_code=400, detail=f"Path escapes allowed root: {raw_path}")


def _run_dir(run_id: str, runs_root: Path) -> Path:
    if "/" in run_id or "\\" in run_id or ".." in Path(run_id).parts:
        raise HTTPException(status_code=400, detail="run_id must be a single safe path segment")
    return _safe_relative_path(run_id, runs_root)


def _read_json_if_present(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Artifact JSON parse failed: {path.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=500, detail=f"Artifact JSON is not an object: {path.name}")
    return data


def _manifest_artifacts(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []

    def add(kind: str, path_value: str) -> None:
        rel = Path(path_value)
        if rel.is_absolute() or ".." in rel.parts:
            return
        artifacts.append({"kind": kind, "path": path_value})

    for name, path_value in manifest.get("core_artifacts", {}).items():
        if isinstance(path_value, str):
            add(f"core:{name}", path_value)
    for part_id, entries in manifest.get("custom_parts", {}).items():
        for path_value in entries:
            add(f"custom_part:{part_id}", path_value)
    for part_id, entries in manifest.get("retrieved_parts", {}).items():
        for path_value in entries:
            add(f"retrieved_part:{part_id}", path_value)
    for path_value in manifest.get("urdf_meshes", []):
        add("urdf_mesh", path_value)
    return artifacts


def _run_summary_payload(run_id: str, runs_root: Path) -> dict[str, Any]:
    run_dir = _run_dir(run_id, runs_root)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Unknown run: {run_id}")
    validation = _read_json_if_present(run_dir / "validation_report.json")
    manifest = _read_json_if_present(run_dir / "artifact_manifest.json")
    preview = _read_json_if_present(run_dir / "preview.json")
    repair_plan = _read_json_if_present(run_dir / "repair_plan.json")
    part_catalog = _read_json_if_present(run_dir / "part_catalog.json")
    part_selection_trace = _read_json_if_present(run_dir / "part_selection_trace.json")
    worker_contracts = _read_json_if_present(run_dir / "worker_contracts.json")
    review_state = _read_json_if_present(run_dir / "review_state.json")
    agent_trace = _read_json_if_present(run_dir / "agent_trace.json")
    modification_request = _read_json_if_present(run_dir / "modification_request.json")
    delta_summary = _read_json_if_present(run_dir / "delta_summary.json")
    gates = validation.get("gates", []) if validation else []
    return {
        "run_id": run_id,
        "validation_status": validation.get("status") if validation else "missing",
        "gate_count": len(gates),
        "gate_statuses": {gate.get("id", "unknown"): gate.get("status", "unknown") for gate in gates},
        "artifact_count": len(_manifest_artifacts(manifest)) if manifest else 0,
        "preview_target_count": len(preview.get("preview_targets", [])) if preview else 0,
        "repair_status": repair_plan.get("status") if repair_plan else "missing",
        "part_catalog_count": len(part_catalog.get("parts", [])) if part_catalog else 0,
        "selected_part_id": part_selection_trace.get("selected_part_id") if part_selection_trace else "missing",
        "worker_contract_count": len(worker_contracts.get("contracts", [])) if worker_contracts else 0,
        "review_checklist_count": len(review_state.get("checklist", [])) if review_state else 0,
        "review_artifact_group_count": len(review_state.get("artifact_groups", [])) if review_state else 0,
        "review_limitations": review_state.get("limitations", []) if review_state else [],
        "agent_request_type": agent_trace.get("request_type") if agent_trace else "missing",
        "agent_parent_run_id": agent_trace.get("parent_run_id") if agent_trace else None,
        "agent_selected_workflow": agent_trace.get("selected_workflow") if agent_trace else "missing",
        "agent_adapter_provider": agent_trace.get("adapter", {}).get("provider") if agent_trace else "missing",
        "agent_adapter_mode": agent_trace.get("adapter", {}).get("mode") if agent_trace else "missing",
        "agent_tool_call_count": len(agent_trace.get("tool_calls", [])) if agent_trace else 0,
        "modification_parent_run_id": modification_request.get("parent_run_id") if modification_request else None,
        "delta_changed_spec_fields": delta_summary.get("changed_spec_fields", []) if delta_summary else [],
        "artifacts": {
            "validation_report": validation is not None,
            "artifact_manifest": manifest is not None,
            "preview": preview is not None,
            "repair_plan": repair_plan is not None,
            "part_catalog": part_catalog is not None,
            "part_selection_trace": part_selection_trace is not None,
            "worker_contracts": worker_contracts is not None,
            "review_state": review_state is not None,
            "agent_trace": agent_trace is not None,
            "modification_request": modification_request is not None,
            "delta_summary": delta_summary is not None,
        },
    }


def _dashboard_html(runs_root: Path) -> str:
    workflows = list_workflows()
    run_cards: list[str] = []
    if runs_root.exists():
        for run_dir in sorted(path for path in runs_root.iterdir() if path.is_dir()):
            try:
                summary = _run_summary_payload(run_dir.name, runs_root)
            except HTTPException:
                continue
            artifacts = ", ".join(name for name, present in summary["artifacts"].items() if present) or "none"
            gate_rows = " ".join(f"{html.escape(gate_id)}={html.escape(str(status))}" for gate_id, status in sorted(summary["gate_statuses"].items()))
            limitations = ", ".join(summary["review_limitations"]) or "metadata unavailable"
            is_current_demo = (
                summary["run_id"] == "pan_tilt_2axis_demo"
                and summary["validation_status"] == "pass"
                and summary["gate_count"] >= 15
                and summary["preview_target_count"] >= 2
                and summary["review_checklist_count"] >= 5
            )
            run_label = "Current canonical run" if is_current_demo else "Local/stale run"
            run_cards.append(
                "<li>"
                f"<strong>{html.escape(summary['run_id'])}</strong> "
                f"<em>{html.escape(run_label)}</em> "
                f"validation={html.escape(str(summary['validation_status']))} "
                f"gates={summary['gate_count']} "
                f"preview_targets={summary['preview_target_count']} "
                f"repair={html.escape(str(summary['repair_status']))} "
                f"selected_part={html.escape(str(summary['selected_part_id']))} "
                f"worker_contracts={summary['worker_contract_count']} "
                f"review_checklist={summary['review_checklist_count']} "
                f"review_groups={summary['review_artifact_group_count']} "
                f"artifacts={html.escape(artifacts)} "
                f"<details><summary>Validation gate table / inspect state</summary><p>{gate_rows}</p><p>Local review limitations: {html.escape(limitations)}</p></details> "
                f"<a href=\"/runs/{html.escape(summary['run_id'])}\">summary JSON</a> "
                f"<a href=\"/runs/{html.escape(summary['run_id'])}/artifacts\">artifact metadata</a>"
                "</li>"
            )
    if not run_cards:
        run_cards.append("<li>No runs found yet. Use the form below or run <code>cadx run-demo</code>.</li>")

    workflow_rows = "".join(
        "<li>"
        f"<strong>{html.escape(workflow.workflow_id)}</strong> "
        f"template={html.escape(workflow.template_id)} "
        f"specs={html.escape(', '.join(workflow.supported_product_spec_ids))} "
        f"— {html.escape(workflow.description)}"
        "</li>"
        for workflow in workflows
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CADX local review dashboard</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 920px; margin: 2rem auto; line-height: 1.45; }}
    code, input {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
    section {{ border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin: 1rem 0; }}
    label {{ display: block; margin: .5rem 0; }}
    .note {{ color: #555; }}
  </style>
</head>
<body>
  <h1>CADX local review dashboard</h1>
  <p>This minimal dashboard reviews local CADX workflows, runs, validation gates, artifact groups, preview targets, repair status, part catalog provenance, worker contracts, and review_state.json metadata. It is not a production frontend, arbitrary file download service, cloud/auth/TLS layer, React/Vite app, vector DB, web scraper, or new CAD kernel.</p>
  <section>
    <h2>Workflows</h2>
    <ul>{workflow_rows}</ul>
    <p>API: <a href="/workflows">/workflows</a></p>
  </section>
  <section>
    <h2>Create run</h2>
    <form method="post" action="/runs">
      <label>Spec path <input name="spec_path" value="runs/pan_tilt_2axis_demo/product_spec.json" size="48"></label>
      <label>Run id <input name="run_id" value="dashboard_review"></label>
      <p>This HTML form documents the boundary; use the JSON API or curl for execution.</p>
    </form>
    <pre>curl -X POST /runs -H 'content-type: application/json' -d '{{"spec_path":"runs/pan_tilt_2axis_demo/product_spec.json","run_id":"dashboard_review"}}'</pre>
  </section>
  <section>
    <h2>Runs</h2>
    <p class="note">Current canonical run: <code>pan_tilt_2axis_demo</code> with 16 validation gates, preview targets, worker contracts, review_state.json, and reproducibility_report.json. Older local/stale runs may have fewer gates or no review-state artifact.</p>
    <ul>{''.join(run_cards)}</ul>
  </section>
  <section>
    <h2>Review / inspect terms</h2>
    <p>validation_report.json · artifact_manifest.json · review_state.json · preview.json · repair_plan.json · part_catalog.json · part_selection_trace.json · worker_contracts.json · assembly.step · robot.urdf · artifacts</p>
    <p class="note">Artifact metadata is manifest-backed only: this dashboard reports safe run-relative paths, existence, sizes, statuses, and review checklist state, but it does not stream arbitrary local files.</p>
  </section>
</body>
</html>"""


def create_app(runs_root: Path = RUNS_ROOT) -> FastAPI:
    app = FastAPI(title="CADX API", version="0.1.0")
    app.state.runs_root = runs_root

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "cadx"}

    @app.get("/", response_class=HTMLResponse)
    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard() -> str:
        return _dashboard_html(app.state.runs_root)

    @app.get("/workflows")
    def workflows() -> dict[str, Any]:
        return {
            "workflows": [
                {
                    "workflow_id": workflow.workflow_id,
                    "template_id": workflow.template_id,
                    "supported_product_spec_ids": list(workflow.supported_product_spec_ids),
                    "description": workflow.description,
                }
                for workflow in list_workflows()
            ]
        }

    @app.post("/runs")
    def create_run(request: RunCreateRequest) -> dict[str, Any]:
        spec_path = _safe_relative_path(request.spec_path, REPO_ROOT)
        if not spec_path.exists():
            raise HTTPException(status_code=404, detail=f"Missing spec: {request.spec_path}")
        run_dir = run_from_spec(spec_path, run_id=request.run_id, runs_root=app.state.runs_root)
        return {"run_id": request.run_id, "run_dir": run_dir.name, "status_url": f"/runs/{request.run_id}"}

    @app.post("/agent/runs")
    def create_agent_generated_run(request: AgentRunRequest) -> dict[str, Any]:
        result = create_agent_run(request.prompt, runs_root=app.state.runs_root, run_id=request.run_id, adapter=request.adapter)
        summary = _run_summary_payload(result.run_id, app.state.runs_root)
        return {"run_id": result.run_id, "run_dir": result.run_dir.name, "status_url": f"/runs/{result.run_id}", "agent_trace": "agent_trace.json", "adapter": result.trace["adapter"], "validation_status": summary["validation_status"], "gate_count": summary["gate_count"]}

    @app.post("/agent/runs/{run_id:path}/modify")
    def modify_agent_generated_run(run_id: str, request: AgentModifyRequest) -> dict[str, Any]:
        try:
            result = modify_agent_run(run_id, request.prompt, runs_root=app.state.runs_root, run_id=request.run_id, adapter=request.adapter)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        summary = _run_summary_payload(result.run_id, app.state.runs_root)
        return {"run_id": result.run_id, "parent_run_id": run_id, "run_dir": result.run_dir.name, "status_url": f"/runs/{result.run_id}", "agent_trace": "agent_trace.json", "modification_request": "modification_request.json", "delta_summary": "delta_summary.json", "validation_status": summary["validation_status"], "gate_count": summary["gate_count"]}

    @app.get("/runs/{run_id:path}/artifacts")
    def run_artifacts(run_id: str) -> dict[str, Any]:
        run_dir = _run_dir(run_id, app.state.runs_root)
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail=f"Unknown run: {run_id}")
        manifest = _read_json_if_present(run_dir / "artifact_manifest.json")
        if manifest is None:
            raise HTTPException(status_code=404, detail=f"Missing artifact_manifest.json for run: {run_id}")
        artifacts = []
        for artifact in _manifest_artifacts(manifest):
            artifact_path = run_dir / artifact["path"]
            artifacts.append({**artifact, "exists": artifact_path.exists(), "bytes": artifact_path.stat().st_size if artifact_path.exists() else 0})
        return {"run_id": run_id, "artifacts": artifacts}

    @app.get("/runs/{run_id:path}")
    def run_summary(run_id: str) -> dict[str, Any]:
        return _run_summary_payload(run_id, app.state.runs_root)

    return app


app = create_app()
