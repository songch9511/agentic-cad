# Hierarchical assembly from brief repair pattern

## Applies when

A brief-driven CAD task asks for an object with multiple functional regions, repeated components, left/right symmetry, or named modules, but the generated result is a single anonymous solid or a visually plausible blob without editable assembly structure.

Typical symptoms:

- STEP exists but occurrence hierarchy is shallow or absent.
- The model is one fused body even though the brief names parts/subassemblies.
- Repeated components such as wheels are modeled as unrelated one-off solids.
- Left/right modules are manually duplicated with inconsistent dimensions or placement.
- The final object is dimensionally plausible but not semantically recognizable from topology/occurrence labels.

## Root cause pattern

The agent optimized for final silhouette instead of preserving the design decomposition implied by the brief. Single-part benchmarks allow this because they overweight geometry existence and under-test reusable parts, occurrence names, module symmetry, and relationships between modules.

## Repair pattern

1. Parse the brief into a part plan before modeling.
2. Define named dimensions and datum conventions for length/width/height and module offsets.
3. Build atomic parts as reusable BREP helpers or part sources.
4. Export or reference editable leaf components before composing the assembly.
5. Build mid-level subassemblies with selector-safe names and explicit transforms.
6. Reuse the same leaf part for repeated features when possible.
7. Mirror or symmetrically place left/right modules from the same parameters.
8. Assemble the full object from modules; avoid fusing unrelated modules into one anonymous solid.
9. Regenerate STEP/GLB/topology through the repo CAD tools only.
10. Verify both geometry and hierarchy: bbox, volume, validity, occurrence count, named modules, repeated components, symmetry, and recognizability proportions.

## Minimum verification

A brief-to-assembly repair is not accepted until evidence shows:

- generation completed through `gen_step_assembly`,
- STEP, GLB, and topology artifacts exist,
- the final shape is valid or passes the assembly-validity equivalent,
- top-level and leaf occurrences exceed the benchmark threshold,
- named left/right modules are present,
- repeated components meet the requested count,
- left/right module placement is symmetric within tolerance,
- bbox and volume are plausible for the brief,
- major modules are vertically ordered correctly, and
- no unrelated viewer or generated-artifact hand edits were made.

## Generalized rule

Brief-driven CAD generation must preserve the hierarchy chain:

`brief -> part plan -> reusable parts -> subassemblies -> final assembly -> semantic recognizability`

A benchmark should reject a monolithic body when the brief requires an editable assembly, even if the final silhouette looks acceptable.
