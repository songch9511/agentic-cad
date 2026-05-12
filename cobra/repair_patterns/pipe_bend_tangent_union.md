# Pipe bend tangent + union repair pattern

## Applies when

A CAD task contains a hollow pipe, tube elbow, swept bend, hose route, or conduit where straight pipe segments must join a curved section as one valid solid.

Typical symptoms:

- STEP exists but `valid_shape` fails.
- `shapeCount` / solid count is greater than `1`.
- A bend visually touches a straight pipe but has a kink, sliver, overlap, or gap at the seam.
- Expected torus/swept surfaces are missing because the model was made from intersecting cylinders instead of a true swept bend.
- Hole/surface counts change unexpectedly after boolean fuse/clean.

## Root cause pattern

The bend path was under-constrained. A generic radius arc or ad hoc overlap may place geometry near the intended endpoint, but it does not prove:

1. the bend start tangent matches the incoming pipe axis,
2. the bend end tangent matches the outgoing pipe axis,
3. the straight pipe begins exactly at the bend endpoint, and
4. the final boolean result is one valid solid.

## Repair pattern

1. Construct the bend with an explicit tangent contract. In build123d, prefer `JernArc` or an equivalent path where the start tangent, radius, and sweep angle are explicit.
2. Sweep the outer tube and inner bore along the same path so their torus-like surfaces remain concentric.
3. Start/end straight pipe runs at the bend endpoints. Avoid using overlap as the primary union mechanism.
4. Fuse/clean only after each source feature is parametrically aligned.
5. Regenerate derived STEP/GLB/topology with the repo CAD tools. Never hand-edit generated artifacts.

Example source-level shape contract:

```python
with BuildLine(Plane.XZ.shift_origin((start_x, y, start_z))) as path:
    JernArc((0, 0), (1, 0), bend_radius, 90)

with BuildSketch(Plane.YZ.shift_origin((start_x, y, start_z))) as section:
    Circle(tube_radius)

elbow = sweep(section.sketch, path.line)
```

For an x-to-z quarter bend using the above contract, the outgoing vertical pipe should start at `z = start_z + bend_radius` and `x = start_x + bend_radius`.

## Minimum verification

A pipe-bend repair is not accepted until the benchmark or local checks show:

- generation completed successfully,
- `valid_shape == true`,
- `shapeCount == 1` (or the task-specific single-solid equivalent),
- bbox is within task tolerance,
- volume is within range,
- expected torus/swept bend surface count is present,
- expected cylinder and bolt-hole counts are present, and
- no unrelated source files changed.

## Generalized rule

Pipe bend features must verify start/end tangent continuity and final single-solid validity. Future drawing-to-CAD tasks should score this explicitly rather than accepting a visually similar set of intersecting cylinders.
