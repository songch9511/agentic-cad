# Evaluator rule proposal: pipe bend tangent + single-solid contract

## Motivation

MODEL-006 showed that `STEP exists` is too weak for pipe elbows. A model can export while still containing a non-tangent bend, overlapping straight pipes, sliver faces, or multiple solids. Pipe-bend benchmarks need topology and geometry checks that reject those false passes.

## Required checks for pipe-bend tasks

Use these checks when a drawing includes a swept pipe elbow, conduit bend, hose route, or tube run:

```json
[
  {"type": "valid_shape", "weight": 16},
  {"type": "selector_count", "selector": "shape", "equals": 1, "weight": 6},
  {"type": "bbox_size", "expected": [/* task dimensions */], "tolerance": [/* tolerances */], "weight": 24},
  {"type": "surface_count", "surface_type": "torus", "equals": 2, "weight": 10},
  {"type": "surface_count", "surface_type": "cylinder", "radius": 2.5, "radius_tolerance": 0.05, "equals": /* hole count */, "weight": 10},
  {"type": "volume_range", "min": /* lower */, "max": /* upper */, "weight": 12}
]
```

The exact radius/count values are task-specific. For MODEL-006 the current task uses the above pattern with bbox `[89.9, 57.499286, 83.75]`, torus count `2`, bolt-hole cylinder radius `2.5` count `10`, pipe/opening cylinder radius `12.5` minimum `2`, and volume range `[41100, 41350]`.

## Proposed future evaluator extension

Add a check type such as `tangent_continuity` or `pipe_bend_contract` that can verify the seam between a selected torus/swept bend face and adjacent cylindrical pipe faces.

Suggested schema:

```json
{
  "type": "pipe_bend_contract",
  "bend_surface_type": "torus",
  "incoming_axis": "x",
  "outgoing_axis": "z",
  "expected_sweep_degrees": 90,
  "tangent_tolerance_degrees": 1.0,
  "endpoint_tolerance": 0.05,
  "weight": 12
}
```

Acceptance criteria:

- exactly one continuous bend feature for each expected elbow wall surface,
- incoming seam tangent parallel to the incoming pipe axis,
- outgoing seam tangent parallel to the outgoing pipe axis,
- endpoint gap/overlap below tolerance,
- final top-level body is one valid shape.

## Curriculum note

Promote this rule into future benchmarks when MODEL-007 or later tasks include routed tubes, elbows, hydraulic lines, exhaust pipes, or pipe assemblies. It should be combined with bbox and volume checks so an agent cannot satisfy topology by making a correctly connected but dimensionally wrong part.
