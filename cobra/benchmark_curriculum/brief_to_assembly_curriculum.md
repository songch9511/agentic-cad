# Brief-to-assembly CAD curriculum

## Purpose

This curriculum step moves beyond single-part drawing reconstruction. A brief-driven CAD agent must decompose intent into editable atomic parts, reusable mid-level modules, and a recognizable final assembly.

## BRIEF-001: compact tracked concept vehicle

Input brief:

> Create a compact tracked concept vehicle as an editable CAD assembly. It should have a lower hull, left and right track modules, multiple road wheels, an upper body, and a top turret or sensor module. The final object should read clearly as a tracked vehicle from 3D inspection. Keep it parametric and organized into reusable parts/subassemblies.

### Required decomposition

- Atomic parts:
  - lower hull
  - upper hull
  - track body reused by left/right modules
  - road wheel reused at least five times per side
  - drive sprocket/end wheel reused front/rear and left/right
  - top turret or sensor module
- Mid-level subassemblies:
  - left track module
  - right track module
  - chassis module
  - upper body module
  - turret/sensor module
- Full assembly:
  - final vehicle assembled from the modules with explicit transforms and selector-safe occurrence names

### Geometry envelope

Suggested target dimensions are approximately `120 x 70 x 55 mm` with loose `±5 mm` tolerance for the first brief-driven benchmark. The model should use robust BREP solids from build123d/OpenCascade and avoid mesh-only visual tricks.

### Evaluation progression

The initial runnable task uses existing harness checks: STEP/GLB/topology existence, `valid_shape`, bbox size, occurrence/shape/face/cylinder sanity, and broad volume range. The evaluator rule proposal `cobra/evaluator_rules/assembly_hierarchy_recognizability_contract.md` defines the missing semantic checks that should become first-class evaluator support:

- minimum top-level and leaf occurrence count,
- named occurrence/module presence,
- left/right mirrored module bbox placement,
- repeated component count for road wheels,
- module-above-module relationships,
- part-intersection/floating-component limits,
- recognizable tracked-vehicle proportions.

## Promotion rule

A future brief-driven benchmark should only be promoted when it tests at least one hierarchy behavior that cannot be satisfied by a single anonymous fused solid. BRIEF-001 establishes the baseline hierarchy contract; BRIEF-002 should add mating faces, fastener alignment, hole patterns, or assembly constraints.
