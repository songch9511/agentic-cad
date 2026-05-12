# Evaluator rule proposal: assembly hierarchy + recognizability contract

## Motivation

BRIEF-001 exposes a curriculum gap: part-level benchmarks can pass when a CAD agent produces a valid STEP but never demonstrates decomposition, part reuse, symmetry, assembly relationships, or semantic recognizability. Brief-driven CAD needs evaluator support for assembly structure, not only final BREP existence.

## Required baseline checks

Use existing evaluator checks where available:

```json
[
  {"type": "step_exists", "weight": 8},
  {"type": "topology_exists", "weight": 8},
  {"type": "glb_exists", "weight": 8},
  {"type": "valid_shape", "weight": 12},
  {"type": "bbox_size", "expected": [120, 70, 55], "tolerance": [5, 5, 5], "weight": 20},
  {"type": "selector_count", "selector": "occurrence", "min": 16, "weight": 16},
  {"type": "selector_count", "selector": "shape", "min": 12, "weight": 12},
  {"type": "surface_count", "surface_type": "cylinder", "min": 18, "weight": 8},
  {"type": "volume_range", "min": 90000, "max": 260000, "weight": 8}
]
```

These checks make BRIEF-001 runnable in the current harness, but they are still insufficient because they do not prove semantic module names, symmetry, wheel repetition, or vertical relationships.

## Proposed first-class check types

### `assembly_occurrence_count`

```json
{"type": "assembly_occurrence_count", "scope": "leaf|top_level|all", "min": 16, "weight": 10}
```

Counts occurrences from `topology.json.assembly.root`, not only flattened shapes.

### `named_occurrence_contains`

```json
{"type": "named_occurrence_contains", "names": ["left_track_module", "right_track_module", "upper_body_module"], "weight": 12}
```

Passes when selector-safe occurrence names or instance paths contain all required module labels.

### `repeated_component_count`

```json
{"type": "repeated_component_count", "name_contains": "road_wheel", "min": 10, "weight": 10}
```

Detects repeated leaf components and encourages part reuse instead of single monolithic modeling.

### `mirrored_module_bbox`

```json
{
  "type": "mirrored_module_bbox",
  "left": "left_track_module",
  "right": "right_track_module",
  "mirror_axis": "y",
  "center_tolerance": 1.0,
  "size_tolerance": 1.0,
  "weight": 12
}
```

Checks that left/right modules have matching bbox sizes and mirrored centers about the assembly datum.

### `module_above_module`

```json
{"type": "module_above_module", "upper": "turret_sensor_module", "lower": "upper_body_module", "axis": "z", "min_gap": -1.0, "weight": 8}
```

Rejects impossible stacked objects where the turret/sensor module floats far away or intersects below the hull.

### `recognizable_vehicle_proportions`

```json
{
  "type": "recognizable_vehicle_proportions",
  "length_axis": "x",
  "width_axis": "y",
  "height_axis": "z",
  "require_length_gt_width": true,
  "require_width_gt_height": true,
  "track_name_contains": ["left_track", "right_track"],
  "weight": 12
}
```

Combines bbox proportions and named track-module placement to catch non-vehicle shapes.

### `part_intersection_limit`

```json
{"type": "part_intersection_limit", "max_major_overlap_fraction": 0.08, "ignore_touching": true, "weight": 10}
```

Uses leaf occurrence bboxes or BREP intersections to reject impossible overlapping modules while allowing intentional contact/fastening.

## Generalized rule

Assembly benchmarks must evaluate hierarchy as data: occurrence tree, names, transforms, component reuse, relationships, and proportions. A final valid BREP is necessary but not sufficient for brief-driven CAD.

## Implemented manifest-only subset (BRIEF-001 follow-up)

The evaluator now implements the first safe assembly checks against `topology.json["assembly"]["root"]`:

- `assembly_occurrence_count` with `scope: "top_level" | "leaf" | "all"` and `min`/`max`/`equals` count comparators.
- `named_occurrence_contains`, matching required labels against assembly node `displayName` and `instancePath`.
- `repeated_component_count`, matching leaf components by `displayName`, `instancePath`, and/or `sourcePath`; BRIEF-001 uses it for `road_wheel >= 10` and `drive_sprocket >= 4`.

Remaining proposed checks are intentionally deferred because they require bbox relationship semantics or heavier geometry analysis: `mirrored_module_bbox`, `module_above_module`, `recognizable_vehicle_proportions`, and `part_intersection_limit`.
