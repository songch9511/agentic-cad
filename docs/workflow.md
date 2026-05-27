# CADX Workflow Registry and Artifact Contract

CADX v0.2 is a run-based workflow engine with an explicit, minimal workflow registry boundary. It is not a generic text-to-CAD generator yet: the only supported runtime workflow today is `pan_tilt_2axis_demo`.

## Workflow selection

Runs enter through one of two CLI paths:

```bash
cadx run-demo
cadx run --spec <product_spec.json> --run-id <run_id>
```

`cadx run-demo` remains the compatibility path for the canonical demo and writes to `runs/pan_tilt_2axis_demo/`.

`cadx run --spec ... --run-id ...` loads a `ProductSpec`, creates a `RunContext`, selects a registered workflow, and writes artifacts under `runs/<run_id>/`.

An optional FastAPI review boundary is available with `pip install -e '.[api]'` and `uvicorn cadx.server:app --reload`. It exposes health, workflow listing, safe local run creation, run summary, manifest-backed artifact metadata routes, and a minimal local HTML dashboard at `/` or `/dashboard`. The dashboard is a pre-frontend review boundary for workflows, runs, validation gates, artifact groups, preview targets, repair status, part provenance, worker contracts, review_state.json, and artifact metadata; it is not a production deployment layer or a JavaScript frontend stack. The same app exposes `POST /agent/runs` and `POST /agent/runs/{run_id}/modify` as the Frontier-model CAD Agent Harness v1 boundary: prompts are accepted through an LLM-facing contract, then mapped through the deterministic `pan_tilt_2axis_demo` fallback unless a future model adapter is explicitly added. Requests may include adapter metadata (`provider`, `model`, `mode`) but CADX records `external_call_performed=false` and performs no network calls. Agent runs emit `agent_trace.json` with ordered tool calls, inputs, outputs, artifact refs, statuses, timestamps, assumptions, unsupported requirements, and validation summary; modification runs also emit `modification_request.json` and `delta_summary.json` with parent-child lineage. For local operator verification, run `cadx run-demo && cadx validate` followed by `scripts/smoke_api_dashboard.sh`; the smoke script imports the app and uses FastAPI TestClient instead of starting a background server.

A minimal local reproducibility boundary is available through `Dockerfile`, `compose.yaml`, and `scripts/smoke_docker.sh`. The image uses Python 3.12, installs the existing CAD/API extras, runs compileall, the canonical demo, validation, and the stable API/dashboard test slice during build, and serves `cadx.server:app` on port 8000. The smoke script rebuilds the image, rechecks compile/demo/validation/API-dashboard tests inside the container, then verifies the existing health, workflow, dashboard, run summary, and manifest-backed artifact metadata routes. Compose and the smoke script bind-mount `./runs` to `/app/runs` so the local operator can inspect persistent run metadata through the same dashboard/API routes. Docker reproducibility must not change workflow semantics, validation gates, artifact names, build123d/fallback behavior, external STEP immutability, or the manifest-backed metadata-only artifact API; it is not a cloud deployment, production-auth, or arbitrary file streaming layer. Full geometry pytest remains the host workspace contract. If build123d/OCP is unavailable or platform-sensitive on a target Docker host, report the fallback geometry warning explicitly instead of claiming real build123d geometry support.

Selection order:

1. If `workflow_id` is set in the product spec, it must match a registered workflow id.
2. Else if `template_id` is set, it must match a registered template id.
3. Else CADX falls back by matching `ProductSpec.id` against a workflow's supported product spec ids.
4. Unknown or ambiguous specs fail closed with an error listing supported workflow ids.

Current registry:

| workflow_id | template_id | Supported product spec ids | Status |
| --- | --- | --- | --- |
| `pan_tilt_2axis_demo` | `pan_tilt_2axis_demo` | `pan_tilt_2axis_demo` | implemented |

Future workflows should be registered through `src/cadx/pipeline/workflows.py` with a descriptor containing the workflow id, template id, supported product spec ids, description, and run function. Do not add hidden branching in `runner.py`.

## RunContext contract

`RunContext` is intentionally small:

- `run_id`: stable run identifier supplied by the caller.
- `run_dir`: output directory, normally `runs/<run_id>/`.
- `spec_path`: optional source path for the input product spec.

Workflow run functions must preserve the caller-provided `run_id` in generated reports and manifests.

## Artifact contract

Every implemented workflow must either emit the following artifact chain or explicitly document why a narrower contract is acceptable:

1. `product_spec.json`
2. `bom.json`
3. `retrieved_parts/` for source-grounded vendor/library parts
4. `catalog/parts/<part_id>/` as the local STEP catalog seed layout with `metadata.json`, immutable `original.step`, and `normalized.step`
5. `part_catalog.json` as the small run-local index of retrieved/local catalog parts for future Part RAG
6. `part_selection_trace.json` as the deterministic record of selected catalog part, candidates, constraints, source refs, and immutable/normalized STEP paths
7. `worker_contracts.json` as the CAD worker skill/contract artifact for intake, part sourcing, custom CAD, assembly/URDF, validation/repair, and report/review responsibilities
8. `review_state.json` as the local review/inspect state for checklist, artifact groups, preview targets, repair status, provenance, worker contracts, and limitations
9. `reproducibility_report.json` as the local environment diagnostics artifact for Python/platform/package probes, geometry backend, validation status, smoke commands, and Docker caveats
5. `custom_parts/` for generated editable CAD parts and contracts
6. `assembly_plan.json`
6. `assembly.step`
7. `joints.json`
8. `robot.urdf`
9. `validation_report.json`
10. `repair_plan.json`
11. `preview.json`
12. `artifact_manifest.json`
13. `run_report.html`

The canonical pan/tilt workflow currently emits all of these.

## Validation contract

A workflow is not complete until `validation_report.json` is written and all required gates are represented. Current pan/tilt gates are:

- `artifacts`
- `external_immutable`
- `geometry_backend`
- `assembly_step`
- `urdf_joint_contract`
- `assembly_urdf_frame_consistency`
- `urdf_mesh_linkage`
- `retrieved_part_metadata`
- `part_catalog`

The `part_catalog` gate validates the local STEP catalog boundary: catalog references must be run-relative, metadata must include source/provenance/license status, original STEP files must remain immutable with separate normalized copies, checksums must match, duplicate part ids are rejected, and geometry/metadata files must exist. The current v1 seed is `servo_mg996r`; broader step.parts-style import remains a later local-only command.
- `interface_contract_lock`
- `worker_contracts`
- `preview_artifact`
- `review_state`
- `reproducibility_report`
- `run_artifact_manifest`

The `worker_contracts` gate validates `worker_contracts.json`: current local-first CADX worker categories must cover intake/spec decomposition, part sourcing/catalog provenance, custom CAD generation, assembly/URDF, validation/repair, and report/review UX; required artifact references must be safe run-relative paths; core validation gates must be covered; and the contracts must preserve explicit non-goals for no cloud, auth/TLS, React/Vite rewrite, live scraping, vector DB, or new CAD kernel.

The `review_state` gate validates `review_state.json`: the review checklist, artifact groups, preview targets, part provenance, worker contract reference, local limitations, and run-relative artifact references must be present and safe. Future workflows may add gates, but must not weaken existing gates for `pan_tilt_2axis_demo`.

The `reproducibility_report` gate validates `reproducibility_report.json`: the report must record the Python 3.12 runtime contract, safe platform fields, package probes for build123d/FastAPI/uvicorn/httpx, geometry backend, validation status/gate count, documented smoke commands, Docker smoke status, and local-only limitations. It does not require Docker daemon access during pytest.

## Manifest and report contract

`artifact_manifest.json` must reference only files that exist relative to the run directory. It should preserve enough metadata for an auditor to trace the run from product spec through BOM, retrieved/custom parts, assembly, URDF, validation, preview, and report.

`preview.json` is the minimal machine-readable preview boundary for future server/frontend work. It lists stable preview targets such as `assembly.step` and `robot.urdf` without adding a UI runtime.

`worker_contracts.json` is the machine-readable CAD worker skill taxonomy for the run. It is inspired by external CAD skill catalogs but scoped to CADX's current local-first artifact workflow, so it describes implemented responsibilities rather than enabling network scraping, cloud execution, a new frontend, or a new CAD kernel.

`review_state.json` is the machine-readable local review/inspect boundary. It summarizes validation status, checklist state, artifact groups, preview targets, repair status, part provenance, worker contracts, and explicit limitations for the dashboard without enabling arbitrary file serving.

`reproducibility_report.json` is the machine-readable local reproducibility diagnostics boundary. It records safe host/runtime facts and smoke commands so another local operator can compare environment assumptions without turning CADX into CI, cloud deployment, or production support tooling.

`run_report.html` is the human-readable summary of the same chain. It should include run id, product spec id, validation status, gate summaries, major artifacts, worker contracts, review state, reproducibility diagnostics, preview summary, and enough source/provenance information to explain retrieved and generated parts. When `agent_trace.json` is present, the manifest and report include it as optional metadata, including the adapter provider/model/mode and tool-call count; modification runs also include `modification_request.json` and `delta_summary.json`.

## Current limitation

The registry boundary is real, but only one workflow is implemented. Product spec variation does not yet drive a generic CAD generation pipeline; `pan_tilt_2axis_demo` remains the deterministic deployable template used to harden contracts, validation, and reporting.
