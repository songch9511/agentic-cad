# CADX Worker Contracts

This document defines the expected handoff contract for CoBrA/CADX specialist workers. CADX is currently centered on Part RAG, custom CAD generation, assembly/URDF construction, validation, repair planning, and report output. The only implemented workflow is `pan_tilt_2axis_demo`; future workers must preserve that artifact contract while extending the system.

Each canonical run emits `worker_contracts.json`, a machine-readable worker skill taxonomy/contract artifact inspired by CAD skill catalogs but scoped to CADX's local-first runtime. The artifact maps intake/spec decomposition, part sourcing/catalog provenance, custom CAD generation, assembly/URDF, validation/repair, and report/review UX to expected inputs, outputs, required artifacts, validation gates, responsible worker type, and non-goals. The `worker_contracts` validation gate verifies this artifact without adding cloud services, auth/TLS, React/Vite, live scraping, vector DB, or a new CAD kernel.

## General worker rules

- Work inside `/Users/daniel/.cobra/workspace/CADX` unless explicitly reassigned.
- Preserve existing artifact names and validation gates for `pan_tilt_2axis_demo`.
- Prefer small, vertical increments: schema + pipeline hook + regression test + acceptance run.
- Do not introduce frontend, API, Docker, or deployment services unless that is the assigned task.
- If a change affects generated artifacts, run the full chain with the project virtualenv: `.venv/bin/cadx run-demo && .venv/bin/cadx validate && .venv/bin/python -m pytest`.
- If a new failure mode is discovered, capture it in validation output or a future `repair_plan.json` contract rather than silently tolerating it.

## Intake worker

Purpose: convert user/product intent into a bounded `ProductSpec`.

Inputs:
- User request or structured product brief.
- Existing workflow/template ids, currently only `pan_tilt_2axis_demo`.

Outputs:
- `product_spec.json` compatible with `cadx.schemas.ProductSpec`.
- Optional `workflow_id` or `template_id` when selecting a workflow explicitly.
- Assumptions for ambiguous dimensions, payloads, interfaces, or materials.

Acceptance:
- Product spec validates under Pydantic.
- Unknown workflow ids fail clearly through the workflow registry.
- The spec does not claim generic CAD generation when routed to a fixed template.

## Part RAG worker

Purpose: resolve reusable source-grounded parts before generating custom geometry.

Inputs:
- `product_spec.json`
- part requirements or BOM candidates
- local catalog/vendor metadata

Outputs:
- `bom.json`
- `retrieved_parts/<part_id>/part_record.json`
- immutable `retrieved_parts/<part_id>/original.step`
- normalized downstream geometry such as `normalized.step` when needed
- run-local `part_catalog.json` entries that index retrieved part provenance, tags, interfaces, and immutable/normalized references

Contract:
- External originals are immutable.
- Part metadata must include source/provenance, manufacturer or source label when known, interfaces, and trace fields sufficient for validation.
- Downstream assembly should reference normalized copies or transforms, not mutate originals.

Acceptance:
- `retrieved_part_metadata` gate remains pass for retrieved parts.
- `part_catalog` gate remains pass and manifest/report include `part_catalog.json`.
- Manifest includes retrieved part records and STEP artifacts.

## Custom CAD generation worker

Purpose: create missing adapters, brackets, plates, and other editable custom parts.

Inputs:
- BOM gaps
- locked interface requirements
- target assembly frames and mate constraints

Outputs:
- `custom_parts/<part_id>/source.py`
- `custom_parts/<part_id>/part.step`
- `custom_parts/<part_id>/design_contract.json`

Contract:
- Generated parts must preserve locked interfaces in `design_contract.json`.
- Build123d output is preferred when available; deterministic placeholder fallback is acceptable only when validation records the backend status.
- Custom source should remain editable and traceable to the design contract.

Acceptance:
- `geometry_backend`, `external_immutable`, and `interface_contract_lock` gates remain pass or intentionally warning/fail with clear diagnostics.

## Assembly and URDF worker

Purpose: convert parts and interfaces into a coherent assembly and robot description.

Inputs:
- `bom.json`
- retrieved/custom part records
- interface contracts
- `assembly_plan.json`
- `joints.json`

Outputs:
- `assembly.step`
- `robot.urdf`
- local URDF mesh proxies under `urdf_meshes/`

Contract:
- Assembly components must reference known retrieved or custom part ids.
- Mate constraints must reference valid component interfaces.
- URDF links/joints must match the joint contract and frame/origin expectations.
- URDF visual/collision mesh references must point to local run artifacts.

Acceptance:
- `assembly_step`, `urdf_joint_contract`, `assembly_urdf_frame_consistency`, and `urdf_mesh_linkage` gates pass.

## Validation and repair worker

Purpose: evaluate generated artifacts and produce actionable diagnostics for failures.

Inputs:
- all run artifacts
- validation gate definitions
- previous validation output when re-running

Outputs:
- `validation_report.json`
- `repair_plan.json`

Contract:
- Validation must be deterministic and fail closed for missing or contradictory artifacts.
- Gate details should be specific enough to route repair work to Part RAG, custom CAD, assembly/URDF, or reporting.
- Repair planning is classification-only unless a later workflow explicitly implements repair execution.

Repair fields:
- `run_id`
- `status`
- `failure_class`
- `source_gate_id`
- `summary`
- `recommended_owner`
- `suggested_actions`
- `blocking_artifacts`

Recommended failure classes:
- `spec_invalid`
- `part_retrieval_failed`
- `custom_geometry_failed`
- `assembly_failed`
- `urdf_contract_failed`
- `manifest_or_report_stale`
- `validation_internal_error`

## Report output worker

Purpose: make the run auditable by humans and downstream automation.

Inputs:
- product spec, BOM, part records, assembly, URDF, validation report, repair plan

Outputs:
- `artifact_manifest.json`
- `preview.json`
- `run_report.html`

Contract:
- Manifest references must be relative to the run directory and point to existing files.
- Report and manifest must preserve `run_id` and product spec id.
- `preview.json` must expose stable local preview targets such as `assembly.step` and `robot.urdf` without adding frontend runtime behavior.
- Report must summarize validation gates, metrics, retrieved parts, custom parts, preview targets, assembly, URDF, and interface contracts.

Acceptance:
- `preview_artifact` gate passes.
- `run_artifact_manifest` gate passes.
- Audit scripts can trace the full chain without external state.

## Handoff checklist

Every worker result should include:

- Files changed.
- Artifacts generated or inspected.
- Commands run and exact outcome.
- Validation gate/test evidence.
- Remaining limitations or the next recommended worker step.
