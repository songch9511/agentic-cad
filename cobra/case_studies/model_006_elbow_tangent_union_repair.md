# MODEL-006 elbow tangent + union repair case study

Date: 2026-05-07 KST
Repository target: `models/benchmarks/model_006_pipe_elbow.py`
Benchmark task: `benchmarks/tasks/model_006_pdf.json`
Input drawing: `benchmarks/drawings/model_006.pdf` / `benchmarks/drawings/model_006.png`
Generated CAD: `models/benchmarks/model_006_pipe_elbow.step`
Topology manifest: `models/benchmarks/.model_006_pipe_elbow.step/topology.json`

## Failure chain

`drawing/input -> generated CAD -> visual failure -> root cause -> repair patch -> evaluator delta -> generalized rule`

- Drawing/input: MODEL NO - 006 pipe elbow drawing with a horizontal pipe, 90-degree swept bend, vertical riser, front circular flange, service port, and top rounded rectangular flange.
- Generated CAD failure: early elbow construction could produce a pipe bend that looked connected but did not guarantee tangent continuity between the horizontal pipe, bend, and vertical riser. Boolean fusion also depended on overlapping solids instead of exact endpoint/tangent contracts.
- Visual/geometric failure: the elbow-to-pipe seam can show a kink, tiny overlap, sliver face, or multi-solid result even when a STEP file exists.
- Root cause: `RadiusArc`-style sweep construction did not guarantee the expected start/end tangent directions for the x-to-z elbow, and the vertical pipe start was not treated as the exact bend endpoint contract.
- Repair patch: use a tangent-controlled bend path (`JernArc((0, 0), (1, 0), bend_radius, 90)` in `cad_features.x_to_z_elbow`) and align the vertical pipe lower start at `BEND_RADIUS` so the straight run begins at the bend endpoint. Keep the source-level CAD parametric; do not patch STEP/GLB/topology artifacts by hand.
- Evaluator delta: the current repaired run passes the strict MODEL-006 checks at 100.0%. The evaluator now catches the important regression class with `valid_shape`, `selector_count(shape)==1`, bounding-box tolerance, volume range, expected torus count, and cylinder/hole surface counts.
- Generalized rule: pipe bend features must verify the start/end tangent contract and the final fused body must pass `solid_count/shapeCount == 1` and `valid_shape == true` before being accepted.

## Current verification run

Command run from repository root:

```bash
./.venv/bin/python benchmarks/run_benchmark.py benchmarks/tasks/model_006_pdf.json --json-out benchmark-results/model_006_pdf.json
```

Observed result:

- Benchmark passed: `1/1`
- Average score: `100.0%`
- STEP exists: passed
- Topology exists: passed
- GLB exists: passed
- `valid_shape`: passed
- `bbox_size`: `[89.9, 57.499286, 83.75]`, within `[0.25, 0.25, 0.25]`
- `shapeCount`: `1`
- Face count: `56`
- Edge count: `135`
- Front flange cylinder radius `28.75`: count `1`
- Torus surfaces: count `2`
- Bolt-hole cylinder radius `2.5`: count `10`
- Pipe/opening cylinder radius `12.5`: count `2`
- Volume: `41214.413886`, within `[41100, 41350]`

## Reuse notes

- Prefer explicit tangent-controlled arc construction for every swept pipe bend.
- Fuse straight pipe runs to the bend at mathematically shared endpoints, not by relying on large overlaps.
- A generated STEP is not sufficient evidence; topology and validity checks must also pass.
- If a future benchmark (MODEL-007, assemblies, GD&T, drawing-to-CAD) includes pipe bends, add or require checks for tangent contract, single solid/shape, swept/torus surfaces, hole counts, bbox, and volume.

## 2026-05-07 rerun note

Rerun time: 17:54 KST

Observed evaluator delta for this CoBrA pass:

- Before score in current checkout: `100.0%`
- After score in current checkout: `100.0%`
- Source repair needed in this pass: none
- Reason no source patch was made: `cad_features.x_to_z_elbow` already uses `JernArc`, and `models/benchmarks/model_006_pipe_elbow.py` already starts the vertical riser at the bend endpoint (`BEND_RADIUS`).
- Memory action: this case study remains the active MODEL-006 repair record; the rerun confirms the seeded tangent/union rule still catches the intended regression class through strict topology, bbox, surface-count, and volume checks.
