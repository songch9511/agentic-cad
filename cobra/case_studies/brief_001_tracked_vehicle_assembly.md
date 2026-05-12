# BRIEF-001 tracked vehicle assembly hierarchy case study

## Brief/input

Create a compact tracked concept vehicle as an editable CAD assembly with lower hull, left/right track modules, multiple road wheels, an upper body, and a top turret or sensor module. The object should read as a tracked vehicle and preserve reusable parts/subassemblies rather than a single fused body.

## Generated CAD hierarchy

Existing BRIEF-001 artifacts expose an assembly manifest with:

- top-level modules: `chassis_module`, `upper_body_module`, `turret_sensor_module`
- nested modules: `left_track_module`, `right_track_module`
- leaf parts: 2 `track_body` occurrences, 10 `road_wheel` occurrences, 4 `drive_sprocket` occurrences, `lower_hull`, `upper_hull`, `commander_hatch`, `top_sensor_pod`, `front_optic_block`, and `antenna_mast`

## Structural failure / evaluator gap

The benchmark could pass with generic geometry checks only: STEP/GLB/topology existence, valid shape, bbox, selector counts, cylinder count, and volume. Those checks did not prove named hierarchy, reused wheels/sprockets, or left/right module structure.

## Root cause

The evaluator treated `kind: assembly` like a geometry-only part. It did not inspect `topology.json["assembly"]["root"]`, so a monolithic but bbox-correct model could satisfy BRIEF-001 without demonstrating brief-to-hierarchy reasoning.

## Repair / evaluator patch

Added manifest-only assembly checks in `benchmarks/evaluator.py`:

- `assembly_occurrence_count` for top-level, leaf, and all occurrence counts
- `named_occurrence_contains` for required module/part labels
- `repeated_component_count` for reused leaf components such as road wheels and drive sprockets

Updated `benchmarks/tasks/brief_001_tracked_vehicle_assembly.json` to require semantic assembly checks and `benchmarks/README.md` to document the new check types.

## Evaluator delta

Before: BRIEF-001 passed at 100% using only geometry/topology checks, but hierarchy semantics were untested.

After: BRIEF-001 still passes at 100%, now with manifest evidence for 3 top-level modules, 22 leaf occurrences, required module names, 10 road wheels, and 4 drive sprockets.

## Generalized rule

Brief-driven CAD generation must be evaluated as a hierarchy: brief -> reusable atomic parts -> named subassemblies -> final assembly -> semantic recognizability. Geometry existence remains necessary, but assembly benchmarks should reject anonymous monolithic outputs that fail occurrence/name/reuse checks.

## Remaining evaluator gaps

Future evaluator work should add bbox relationship checks for mirrored left/right modules, upper/lower module placement, recognizable vehicle proportions, and major part intersection/floating limits.

## Visual recognizability upgrade case note

Chain: brief/input -> generated CAD hierarchy -> visual/structural failure -> root cause -> repair/evaluator patch -> evaluator delta -> generalized rule

- Brief/input: compact tracked concept vehicle assembly with lower hull, left/right track modules, road wheels, upper body, and turret/sensor module.
- Generated CAD hierarchy before this pass: benchmark-compliant but visually sparse; only basic track bodies, wheels, hull blocks, and sensor pod were present.
- Visual/structural failure: evaluator success did not guarantee that the model read clearly as a capable tracked concept vehicle from isometric inspection.
- Root cause: the first BRIEF-001 assembly emphasized semantic occurrence counts and bbox compliance over detailed track-system vocabulary, deck/turret details, and repeated visible components.
- Repair patch: kept the same assembly generator contract but added segmented track-belt detail, sprocket teeth, side guards, sloped hull plates, deck detail, hatch, optic block, and antenna mast. Benchmark-critical road wheels and drive sprockets remain explicit repeated assembly occurrences; smaller track/guard details are integrated into reusable component geometry to avoid assembly export timeout.
- Evaluator delta: full benchmark remains passing at 100.0% after regeneration; semantic assembly counts preserve required names and repeated road wheel/sprocket counts while keeping generation within the 300 second timeout.
- Generalized rule: brief-to-assembly benchmarks should pair manifest-level hierarchy checks with visible repeated component vocabulary so a pass represents both editable structure and recognizable CAD form.
