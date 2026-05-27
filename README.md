# CADX Sprint 0

CADX is a minimal MVP scaffold for an agentic text-to-CAD product pipeline whose core is **Part RAG + Assembly Agent + URDF Agent**, not free-form part generation.

Sprint 0 runs a fixed `pan_tilt_2axis_demo` that emits inspectable artifacts under `runs/pan_tilt_2axis_demo/`.

## Run

```bash
cd /Users/daniel/.cobra/workspace/CADX
python3 -m venv .venv
.venv/bin/python -m pip install -e . pytest
.venv/bin/cadx run-demo
.venv/bin/cadx validate
.venv/bin/python -m pytest
```

Install the optional CAD backend when available:

```bash
.venv/bin/python -m pip install -e '.[cad]' pytest
```

Install and smoke-test the optional API/dashboard boundary when needed:

```bash
.venv/bin/python -m pip install -e '.[api]' pytest
.venv/bin/cadx run-demo && .venv/bin/cadx validate
PATH="$PWD/.venv/bin:$PATH" scripts/smoke_api_dashboard.sh
.venv/bin/uvicorn cadx.server:app --reload
open http://127.0.0.1:8000/dashboard
```

The FastAPI app is a local review boundary for existing CADX runs, not production deployment. It exposes health, workflow listing, run creation from safe repo-local specs, run summaries, manifest-backed artifact metadata, and a minimal HTML dashboard at `/` or `/dashboard` for reviewing workflows, runs, validation, preview, and artifacts without a frontend build toolchain. It also exposes the local-only agent harness endpoints `POST /agent/runs` and `POST /agent/runs/{run_id}/modify`; these accept natural-language prompts but use the deterministic `pan_tilt_2axis_demo` fallback mapper by default, write `agent_trace.json`, and preserve the canonical fixture. The smoke script uses FastAPI TestClient and does not require starting uvicorn.

Run the optional local reproducibility boundary after the non-Docker smoke is green:

```bash
# Requires Docker CLI + daemon.
docker build -t cadx:local .
docker compose up --build
# then open http://127.0.0.1:8000/dashboard
```

Or run the container smoke script:

```bash
scripts/smoke_docker.sh
```

The Docker image is based on Python 3.12, installs `cadx` with the existing `[cad,api]` extras plus `pytest`, and runs `python -m compileall src/cadx tests`, `cadx run-demo`, `cadx validate`, and the stable API/dashboard test slice during the image build. The smoke script then rechecks compile, demo generation, validation, and the API/dashboard test slice inside the built image before starting the existing FastAPI/dashboard app on port 8000. Compose and the smoke script bind-mount `./runs` to `/app/runs`, so local run artifacts persist outside the container. This boundary is local-first reproducibility only: no cloud deployment, production auth, frontend rewrite, or arbitrary artifact download service is included. Full geometry pytest remains the host workspace contract; on Docker hosts where build123d/OCP dependencies such as `py_lib3mf` are unavailable, the container may use the documented placeholder geometry fallback and report `validation_report.json` status `warning` rather than proving real build123d STEP export.

If build123d is unavailable or STEP export fails, Sprint 0 intentionally writes deterministic placeholder STEP files and marks this in `validation_report.json`. When build123d succeeds, `custom_parts/*/part.step` is exported from editable `source.py` files and the validation geometry backend gate passes.

## Design policies

- **Local STEP catalog / part selection provenance v1:** the canonical run emits a step.parts-inspired local seed under `catalog/parts/servo_mg996r/` with `metadata.json`, immutable `original.step`, and `normalized.step`, indexes it in `part_catalog.json` with source/provenance/license/checksum/interface/dimension/selection suitability metadata, and writes `part_selection_trace.json` explaining why the deterministic demo selected that part. This is curated local fixture ingestion only; no web scraping, bulk catalog import, vector DB, arbitrary external downloads, license bypass, or network dependency is included.
- **Worker skill taxonomy / contract artifact v1:** the canonical run emits `worker_contracts.json` to describe the local-first CADX worker responsibilities for intake, part sourcing/catalog provenance, custom CAD generation, assembly/URDF, validation/repair, and report/review UX. The artifact is descriptive and validated; it does not add cloud services, auth/TLS, React/Vite, live scraping, vector DB, or a new CAD kernel.
- **FluidCAD-style local review / inspect UX v1:** the canonical run emits `review_state.json` and the server-rendered `/dashboard` surfaces run status, validation gates, artifact groups, preview targets, repair status, part provenance, worker contracts, and explicit local limitations from manifest-backed metadata. This is a local review affordance only; it does not stream arbitrary files or introduce a frontend framework.
- **Local reproducibility diagnostics v1:** the canonical run emits `reproducibility_report.json` with safe runtime diagnostics: Python major/minor, platform fields, package availability probes for build123d/FastAPI/uvicorn/httpx, geometry backend, validation status/gate count, documented smoke commands, and a Docker smoke caveat. This is an internal local diagnostic artifact, not CI, deployment, production support, or a Docker daemon dependency for pytest.
- **Frontier-model CAD Agent Harness v1:** `POST /agent/runs` and `POST /agent/runs/{run_id}/modify` provide an LLM-facing contract for generate/modify flows, but no external model call is required. The v1 harness records prompt, selected workflow/template, deterministic mapper actions, assumptions, unsupported requirements, generated product spec, validation summary, parent-child lineage, `modification_request.json`, `delta_summary.json`, and `agent_trace.json`. `agent_trace.json` now includes an explicit adapter boundary (`provider`, `model`, `mode`, `external_call_performed=false`) and ordered CAD tool-call records with inputs, outputs, artifact refs, status, and timestamps. It is constrained to `pan_tilt_2axis_demo`; it is not arbitrary product generation, production auth, cloud orchestration, or a live CAD viewer.
- **Part RAG metadata first:** Sprint 0 uses deterministic local metadata matching instead of real vendor STEP search.
- **Immutable external STEP originals:** `retrieved_parts/*/original.step` is copied/generated once and never directly edited.
- **Normalized copies allowed:** downstream transforms should operate on `normalized.step` or assembly transforms.
- **Editable custom parts:** generated adapters live in `custom_parts/*/source.py` plus `design_contract.json`.
- **Interface locks:** design contracts list locked interfaces that future direct edits must preserve.
- **Future direct editing path:** before/after geometric diff, locked-interface pose checks, and invariant validation are required before replacing any external/custom geometry.

## Required Sprint 0 artifacts

- `bom.json`
- `retrieved_parts/`
- `custom_parts/`
- `assembly.step`
- `robot.urdf`
- `joints.json`
- `validation_report.json`
- `worker_contracts.json`
- `review_state.json`
- `reproducibility_report.json`
- optional agent-run artifacts: `agent_trace.json`, `modification_request.json`, `delta_summary.json`
- `run_report.html`

## Docs

- [Workflow registry and artifact contract](docs/workflow.md)
- [CoBrA/CADX worker contracts](docs/worker_contracts.md)
