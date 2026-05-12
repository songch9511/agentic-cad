# MODEL-006 benchmark run log

Date: 2026-05-07 KST
Task: `benchmarks/tasks/model_006_pdf.json`
Target: `models/benchmarks/model_006_pipe_elbow.py`
Result JSON: `benchmark-results/model_006_pdf.json`

## Command

```bash
./.venv/bin/python benchmarks/run_benchmark.py benchmarks/tasks/model_006_pdf.json --json-out benchmark-results/model_006_pdf.json
```

## Result

- Passed count: `1`
- Failed count: `0`
- Average score: `100.0%`
- Target STEP: `models/benchmarks/model_006_pipe_elbow.step`

## Key checks

- `valid_shape`: passed
- `shapeCount`: `1`
- `bbox_size`: `[89.9, 57.499286, 83.75]`
- `faceCount`: `56`
- `edgeCount`: `135`
- Torus surfaces: `2`
- Radius `2.5` cylinder surfaces: `10`
- Radius `12.5` cylinder surfaces: `2`
- Volume: `41214.413886`

## Delta recorded

The current checkout already contains the MODEL-006 tangent/union repair pattern (`JernArc` elbow path and aligned vertical riser). This run verifies the repaired state at `100.0%`; no additional source patch was needed in this run. The seeded historical failure is documented in `cobra/case_studies/model_006_elbow_tangent_union_repair.md`, with the reusable repair promoted to `cobra/repair_patterns/pipe_bend_tangent_union.md` and evaluator guidance added in `cobra/evaluator_rules/pipe_bend_tangent_solid_contract.md`.

## 2026-05-07 17:54 KST rerun

- Command: `./.venv/bin/python benchmarks/run_benchmark.py benchmarks/tasks/model_006_pdf.json --json-out benchmark-results/model_006_pdf.json`
- Passed count: `1`
- Failed count: `0`
- Average score: `100.0%`
- Evaluator delta: `100.0% -> 100.0%`
- Checks still failing: none
- Source patch: none; current CAD source already implements the tangent-controlled elbow and aligned vertical pipe contract.
- Memory update: appended the rerun note to `cobra/case_studies/model_006_elbow_tangent_union_repair.md`.
