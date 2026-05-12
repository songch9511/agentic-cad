# Agentic CAD Benchmarks

This directory adds a small evaluator and benchmark runner on top of the bundled
build123d/OpenCascade CAD harness.

## Run

From the repo root:

```bash
./.venv/bin/python benchmarks/run_benchmark.py benchmarks/tasks/smoke.json \
  --json-out benchmark-results/smoke.json
```

The runner:

1. Regenerates each task target with `skills/cad/scripts/gen_step_part` or `gen_step_assembly`.
2. Reads the generated STEP topology manifest.
3. Scores geometric checks such as bounding box size, volume range, selector counts, and cylindrical faces.
4. Writes a machine-readable result JSON when `--json-out` is provided.

Use `--skip-generate` to score existing generated artifacts without rebuilding them.

If the local Python environment does not already include the CAD dependencies,
run through `uv`:

```bash
uv run --with-requirements requirements-cad.txt python benchmarks/run_benchmark.py \
  benchmarks/tasks/model_006_pdf.json \
  --json-out benchmark-results/model_006_pdf.json
```

## Task Schema

Each task is a JSON object with:

- `id`: stable benchmark id.
- `kind`: `part` or `assembly`.
- `target`: repo-relative Python generator or STEP/STP file.
- `prompt`: source prompt for agent runs.
- `checks`: weighted evaluator checks.

Drawing-to-CAD tasks may also include an `inputs` object with source artifacts
such as `drawingPdf` and `drawingPreview`. The current runner preserves those
fields as benchmark data for agents, while scoring still happens against the
generated CAD target and geometric checks.

Supported checks:

- `step_exists`
- `topology_exists`
- `glb_exists`
- `valid_shape`
- `bbox_size`
- `bbox_center`
- `selector_count`
- `surface_count`
- `curve_count`
- `volume_range`
- `assembly_occurrence_count`
  - Reads `topology.json["assembly"]["root"]` and counts assembly occurrences.
  - `scope`: `top_level`, `leaf`, or `all`.
  - Supports `min`, `max`, and `equals`.
- `named_occurrence_contains`
  - Requires each string in `names` to appear in an assembly node `displayName` or `instancePath`.
- `repeated_component_count`
  - Counts matching leaf assembly nodes.
  - `contains` may be a string or list and is matched against `displayName`, `instancePath`, and `sourcePath` by default.
  - `fields` can narrow matching to any of `displayName`, `instancePath`, or `sourcePath`.
  - Supports `min`, `max`, and `equals`.

The first assembly checks are manifest-only and intentionally avoid expensive BREP
intersection or visual recognizability. Use them to reject monolithic outputs and
verify named hierarchy/reused components before adding heavier assembly semantics.
