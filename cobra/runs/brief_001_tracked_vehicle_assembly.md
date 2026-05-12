# BRIEF-001 tracked vehicle assembly run

## Scope

Follow-up evaluator implementation for the BRIEF-001 compact tracked concept vehicle assembly benchmark. Generated STEP/GLB/topology artifacts were regenerated only through the benchmark pipeline, not hand-edited.

## Files changed

- `benchmarks/evaluator.py`
- `benchmarks/README.md`
- `benchmarks/tasks/brief_001_tracked_vehicle_assembly.json`
- `benchmark-results/brief_001_tracked_vehicle_assembly.json`
- `cobra/evaluator_rules/assembly_hierarchy_recognizability_contract.md`
- `cobra/case_studies/brief_001_tracked_vehicle_assembly.md`
- `cobra/runs/brief_001_tracked_vehicle_assembly.md`

## Benchmark score

- Before follow-up: 100.0% with generic geometry/topology checks only.
- After follow-up: 100.0% with added manifest-only assembly hierarchy checks.

## Added checks

- `assembly_occurrence_count` top-level `min: 3`
- `assembly_occurrence_count` leaf `min: 18`
- `named_occurrence_contains` for chassis, left/right track, upper body, turret/sensor, lower hull, and upper hull labels
- `repeated_component_count` for `road_wheel >= 10`
- `repeated_component_count` for `drive_sprocket >= 4`

## Verification command

```bash
./.venv/bin/python benchmarks/run_benchmark.py benchmarks/tasks/brief_001_tracked_vehicle_assembly.json --skip-generate --json-out benchmark-results/brief_001_tracked_vehicle_assembly.json
```

Result: `Benchmark: 1/1 passed, average=100.0%`.

## Checks still failing

None in the current BRIEF-001 task.

## Evaluator gaps still open

- `mirrored_module_bbox`
- `module_above_module`
- `recognizable_vehicle_proportions`
- `part_intersection_limit`

## Next recommended benchmark

BRIEF-002 functional bracket or mechanism assembly, checking mating faces, fastener alignment, hole patterns, and assembly constraints.

## Visual/assembly quality upgrade pass

- Upgraded `models/benchmarks/brief_001_tracked_vehicle_assembly.py` from a minimal benchmark assembly to a richer recognizable tracked robotic platform while preserving the existing assembly envelope and semantic occurrence tree.
- Added reusable component geometry for segmented track belt detail, sprocket teeth, side-skirt-like guards, deck detail, hatch, optic block, and antenna mast. Road wheels and drive sprockets remain explicit repeated assembly occurrences; smaller track/guard details are integrated into reusable component geometry to keep full generation under the benchmark timeout.
- Preserved and expanded hierarchy: `chassis_module` contains mirrored `left_track_module`/`right_track_module` plus `lower_hull`; `upper_body_module` now includes a nested `deck_detail_module`; `turret_sensor_module` includes sensor pod, optic block, and mast.
- Generation issues encountered: `_lower_hull()` and `_turret_sensor_module()` produced `ShapeList` values when detail solids did not fuse. Repair was to return `Compound` objects for intentionally separate detail solids.
- Performance issue encountered: the first v4 recognizability pass made many small track-pad occurrences. The assembly exporter imports every occurrence, so full generation exceeded the 300 second benchmark timeout. Repair was to integrate small track/guard details into reusable component STEP geometry while keeping benchmark-critical road wheels and drive sprockets as explicit repeated occurrences.
- Harness issue encountered: assembly dependency expansion scanned the whole repo and tripped over unrelated invalid demo source metadata. Repair was to localize the CAD catalog scan from this generator to its benchmark directory before returning assembly paths.
- Bbox tuning: moved outer track detail inward so the richer side detail stayed within the existing `[120, 70, 55] +/- [5, 5, 5]` benchmark envelope.
- Verification: `./.venv/bin/python -m py_compile models/benchmarks/brief_001_tracked_vehicle_assembly.py` passed; full benchmark regenerated and passed at 100.0% in 38.2 seconds with bbox `[123.494826, 74.35, 58.65]`, occurrence count 376, assembly leaf count 22, shape count 190, face count 2060, road wheels 10, drive sprockets 4. A prior v5 attempt failed at 95.9% because the track modules pushed Y size to `75.55`, just outside the `[120, 70, 55] +/- [5, 5, 5]` bbox envelope; moving `TRACK_Y` from `28.0` to `27.4` fixed the envelope while preserving the visible track spacing.
