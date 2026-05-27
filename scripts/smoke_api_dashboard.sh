#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${CADX_PYTHON:-$PWD/.venv/bin/python}"
CADX_BIN="${CADX_BIN:-$PWD/.venv/bin/cadx}"

if [ ! -x "$PYTHON_BIN" ]; then
    echo "CADX API smoke requires the project virtualenv. Run: .venv/bin/python -m pip install -e '.[api]' pytest" >&2
    exit 1
fi

"$PYTHON_BIN" -c "import fastapi, httpx; from fastapi.testclient import TestClient" || {
    echo "CADX API smoke requires optional API dependencies. Install them with: .venv/bin/python -m pip install -e '.[api]' pytest" >&2
    exit 1
}

"$CADX_BIN" run-demo
"$CADX_BIN" validate

"$PYTHON_BIN" -c '
from fastapi.testclient import TestClient
from cadx.server import app

client = TestClient(app)
for method, path in [
    ("GET", "/health"),
    ("GET", "/workflows"),
    ("GET", "/"),
    ("GET", "/dashboard"),
    ("GET", "/runs/pan_tilt_2axis_demo"),
    ("GET", "/runs/pan_tilt_2axis_demo/artifacts"),
]:
    response = client.request(method, path)
    if response.status_code != 200:
        raise SystemExit(f"{method} {path} failed: {response.status_code} {response.text}")

health = client.get("/health").json()
workflows = client.get("/workflows").json()["workflows"]
dashboard = client.get("/dashboard").text
summary = client.get("/runs/pan_tilt_2axis_demo").json()
artifacts = client.get("/runs/pan_tilt_2axis_demo/artifacts").json()["artifacts"]

assert health == {"status": "ok", "service": "cadx"}
assert any(workflow["workflow_id"] == "pan_tilt_2axis_demo" for workflow in workflows)
for token in ["CADX", "Workflows", "Runs", "Current canonical run", "stale", "preview", "validation", "artifacts", "review_state.json", "reproducibility_report.json", "worker contracts", "part catalog provenance", "Validation gate table"]:
    assert token in dashboard, token
assert summary["validation_status"] == "pass", summary
assert summary["gate_count"] == 16, summary
assert summary["preview_target_count"] == 2, summary
assert summary["worker_contract_count"] == 6, summary
assert summary["review_checklist_count"] == 5, summary
assert summary["review_artifact_group_count"] == 5, summary
assert "no_arbitrary_file_streaming" in summary["review_limitations"], summary
paths = {artifact["path"] for artifact in artifacts}
for required in ["validation_report.json", "artifact_manifest.json", "preview.json", "part_catalog.json", "part_selection_trace.json", "worker_contracts.json", "review_state.json", "reproducibility_report.json", "repair_plan.json"]:
    assert required in paths, required
print(
    "CADX API/dashboard smoke passed: "
    f"workflow_count={len(workflows)} "
    f"validation_status={summary['"'"'validation_status'"'"']} "
    f"gate_count={summary['"'"'gate_count'"'"']} "
    f"preview_target_count={summary['"'"'preview_target_count'"'"']} "
    f"artifact_count={len(artifacts)}"
)
'
