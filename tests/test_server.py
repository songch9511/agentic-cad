from pathlib import Path
import json

import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")
from fastapi.testclient import TestClient

from cadx.demos import pan_tilt_2axis
from cadx.server import create_app


def test_api_lists_workflows_and_existing_run_summary(tmp_path: Path):
    app = create_app(runs_root=tmp_path / "runs")
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "service": "cadx"}

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert "text/html" in dashboard.headers["content-type"]
    for token in [
        "CADX",
        "Workflows",
        "Runs",
        "Current canonical run",
        "stale",
        "artifacts",
        "preview",
        "validation",
        "review_state.json",
        "worker contracts",
        "part catalog provenance",
    ]:
        assert token in dashboard.text

    root_dashboard = client.get("/")
    assert root_dashboard.status_code == 200
    assert "CADX local review dashboard" in root_dashboard.text

    workflows = client.get("/workflows")
    assert workflows.status_code == 200
    assert workflows.json()["workflows"][0]["workflow_id"] == "pan_tilt_2axis_demo"

    spec_path = tmp_path / "spec.json"
    spec_path.write_text(pan_tilt_2axis.product_spec().model_dump_json(indent=2))
    create_response = client.post("/runs", json={"spec_path": str(spec_path), "run_id": "api_test_run"})
    assert create_response.status_code == 400

    repo_spec = Path("runs") / "api_spec.json"
    repo_spec_abs = Path(__file__).resolve().parents[1] / repo_spec
    repo_spec_abs.parent.mkdir(parents=True, exist_ok=True)
    repo_spec_abs.write_text(pan_tilt_2axis.product_spec().model_dump_json(indent=2))
    try:
        create_response = client.post("/runs", json={"spec_path": str(repo_spec), "run_id": "api_test_run"})
        assert create_response.status_code == 200
        assert create_response.json()["status_url"] == "/runs/api_test_run"

        summary = client.get("/runs/api_test_run")
        assert summary.status_code == 200
        body = summary.json()
        assert body["run_id"] == "api_test_run"
        assert body["validation_status"] in {"pass", "warning"}
        assert body["gate_count"] == 16
        assert body["preview_target_count"] == 2
        assert body["repair_status"] in {"pass", "warning"}
        assert body["part_catalog_count"] == 1
        assert body["selected_part_id"] == "servo_mg996r"
        assert body["worker_contract_count"] == 6
        assert body["review_checklist_count"] == 5
        assert body["review_artifact_group_count"] == 5
        assert "no_arbitrary_file_streaming" in body["review_limitations"]
        assert body["artifacts"]["preview"] is True
        assert body["artifacts"]["review_state"] is True

        artifacts = client.get("/runs/api_test_run/artifacts")
        assert artifacts.status_code == 200
        artifact_paths = {artifact["path"] for artifact in artifacts.json()["artifacts"]}
        assert "preview.json" in artifact_paths
        assert "artifact_manifest.json" in artifact_paths
        assert "retrieved_parts/servo_mg996r/original.step" in artifact_paths
    finally:
        repo_spec_abs.unlink(missing_ok=True)


def test_api_rejects_unsafe_run_and_spec_paths(tmp_path: Path):
    app = create_app(runs_root=tmp_path / "runs")
    client = TestClient(app)

    unsafe_run = client.get("/runs/..%2Foutside")
    assert unsafe_run.status_code == 400

    unsafe_spec = client.post("/runs", json={"spec_path": "../outside.json", "run_id": "bad"})
    assert unsafe_spec.status_code == 400

    bad_run_id = client.post("/runs", json={"spec_path": "runs/missing.json", "run_id": "bad/run"})
    assert bad_run_id.status_code == 422


def test_docker_reproducibility_boundary_documents_local_smoke_contract():
    repo_root = Path(__file__).resolve().parents[1]
    dockerfile = (repo_root / "Dockerfile").read_text()
    smoke_script = (repo_root / "scripts" / "smoke_docker.sh").read_text()
    compose = (repo_root / "compose.yaml").read_text()

    assert "FROM python:3.12-slim" in dockerfile
    assert "pip install -e '.[cad,api]' pytest" in dockerfile
    for token in ["python -m compileall src/cadx tests", "cadx run-demo", "cadx validate", "pytest -q"]:
        assert token in dockerfile
        assert token in smoke_script
    assert "docker info" in smoke_script
    assert "CADX Docker smoke passed" in smoke_script
    assert 'grep -q \'"status":"ok"\'' in smoke_script
    assert "./runs:/app/runs" in compose


def test_agent_generate_and_modify_routes_create_traceable_runs(tmp_path: Path):
    app = create_app(runs_root=tmp_path / "runs")
    client = TestClient(app)

    generate = client.post(
        "/agent/runs",
        json={
            "prompt": "Generate a simple two-axis pan tilt CAD assembly for MG996R servos",
            "run_id": "agent_generate_test",
            "adapter": {"provider": "frontier-mock", "model": "mock-cad-model-v0", "mode": "mock"},
        },
    )
    assert generate.status_code == 200
    assert generate.json()["run_id"] == "agent_generate_test"
    assert generate.json()["validation_status"] in {"pass", "warning"}

    run_dir = tmp_path / "runs" / "agent_generate_test"
    trace = json.loads((run_dir / "agent_trace.json").read_text())
    assert trace["request_type"] == "generate"
    assert trace["parent_run_id"] is None
    assert trace["adapter"]["provider"] == "frontier-mock"
    assert trace["adapter"]["model"] == "mock-cad-model-v0"
    assert trace["adapter"]["mode"] == "mock"
    assert trace["adapter"]["external_call_performed"] is False
    assert len(trace["tool_calls"]) == 3
    assert trace["tool_calls"][0]["tool_name"] == "llm_adapter.map_prompt_to_product_spec"
    assert "product_spec.json" in trace["tool_calls"][0]["artifact_refs"]
    assert trace["selected_workflow"] == "pan_tilt_2axis_demo"
    assert trace["generated_product_spec"]["id"] == "pan_tilt_2axis_demo"
    assert trace["validation_summary"]["gate_count"] >= 16
    manifest = json.loads((run_dir / "artifact_manifest.json").read_text())
    assert manifest["core_artifacts"]["agent_trace"] == "agent_trace.json"
    assert "Agent harness trace" in (run_dir / "run_report.html").read_text()

    modify = client.post(
        "/agent/runs/agent_generate_test/modify",
        json={
            "prompt": "Make the base wider but preserve the pan tilt workflow",
            "run_id": "agent_modify_test",
            "adapter": {"provider": "cadx", "model": "deterministic-pan-tilt-fallback-v1", "mode": "deterministic_fallback"},
        },
    )
    assert modify.status_code == 200
    assert modify.json()["parent_run_id"] == "agent_generate_test"
    child_dir = tmp_path / "runs" / "agent_modify_test"
    child_trace = json.loads((child_dir / "agent_trace.json").read_text())
    modification = json.loads((child_dir / "modification_request.json").read_text())
    delta = json.loads((child_dir / "delta_summary.json").read_text())
    assert child_trace["request_type"] == "modify"
    assert child_trace["parent_run_id"] == "agent_generate_test"
    assert child_trace["adapter"]["mode"] == "deterministic_fallback"
    assert child_trace["tool_calls"][0]["tool_name"] == "llm_adapter.map_modification_to_spec_patch"
    assert "modification_request.json" in child_trace["tool_calls"][0]["artifact_refs"]
    assert modification["parent_run_id"] == "agent_generate_test"
    assert modification["adapter"]["external_call_performed"] is False
    assert delta["child_run_id"] == "agent_modify_test"
    child_manifest = json.loads((child_dir / "artifact_manifest.json").read_text())
    assert child_manifest["core_artifacts"]["agent_trace"] == "agent_trace.json"
    assert child_manifest["core_artifacts"]["modification_request"] == "modification_request.json"
    assert child_manifest["core_artifacts"]["delta_summary"] == "delta_summary.json"

    summary = client.get("/runs/agent_modify_test").json()
    assert summary["agent_request_type"] == "modify"
    assert summary["agent_parent_run_id"] == "agent_generate_test"
    assert summary["agent_adapter_provider"] == "cadx"
    assert summary["agent_adapter_mode"] == "deterministic_fallback"
    assert summary["agent_tool_call_count"] == 3
    assert "assumptions" in summary["delta_changed_spec_fields"]


def test_agent_unsupported_prompt_is_recorded_not_silently_hallucinated(tmp_path: Path):
    app = create_app(runs_root=tmp_path / "runs")
    client = TestClient(app)

    response = client.post(
        "/agent/runs",
        json={"prompt": "Generate an arbitrary freeform drone gearbox using an online catalog", "run_id": "unsupported_agent_test"},
    )
    assert response.status_code == 200
    trace = json.loads((tmp_path / "runs" / "unsupported_agent_test" / "agent_trace.json").read_text())
    assert trace["selected_workflow"] == "pan_tilt_2axis_demo"
    assert trace["adapter"]["external_call_performed"] is False
    assert "general_freeform_cad" in trace["unsupported_requirements"]
    assert "cloud_vendor_part_search" in trace["unsupported_requirements"]
    assert "unsupported_template_request" in trace["unsupported_requirements"]
    assert "non_pan_tilt_prompt_mapped_to_supported_template" in trace["unsupported_requirements"]
    assert any("Unsupported request aspects" in assumption for assumption in trace["assumptions"])


def test_agent_modify_rejects_missing_parent(tmp_path: Path):
    app = create_app(runs_root=tmp_path / "runs")
    client = TestClient(app)

    response = client.post("/agent/runs/missing_parent/modify", json={"prompt": "change it", "run_id": "child"})
    assert response.status_code == 404
