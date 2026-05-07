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

## Task Schema

Each task is a JSON object with:

- `id`: stable benchmark id.
- `kind`: `part` or `assembly`.
- `target`: repo-relative Python generator or STEP/STP file.
- `prompt`: source prompt for agent runs.
- `checks`: weighted evaluator checks.

Supported checks in this initial harness:

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
