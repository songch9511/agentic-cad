# Case Study: MODEL-006 CAD to GD&T Drawing Rebuild

## User Feedback

The first drawing was rejected because it looked like a toy diagram rather than a real GD&T drawing. The major issue was not one missing tolerance; it was the absence of manufacturing drawing structure.

## Root Cause

The initial generator treated GD&T as visual decoration:

- It placed datum boxes and FCFs without enough drawing grammar.
- It did not separate section, front, top, and service-port views clearly.
- Callouts were crowded and some were cropped.
- The DXF/SVG output was generated from ad hoc primitives rather than a drawing intent model.

## Repair Applied

The preview generator was rebuilt around a more realistic review-drawing template:

- Landscape engineering sheet with border, zone marks, title block, revision/status, notes, and third-angle symbol.
- Primary section A-A with datum A/B/C structure.
- Front flange, top flange, and service-port views.
- Basic dimensions for bolt circle, top flange spacing, and key feature locations.
- Pattern FCFs for front flange, top flange, service port, plus profile/runout/perpendicularity proposals.
- Datum reference table explaining feature and function.
- Explicit `AUTO-PROPOSED GD&T - ENGINEERING REVIEW REQUIRED` status.

## Remaining Limitations

This is still a demo-quality auto-proposal, not a certified production drawing:

- Geometry is manually projected from known feature parameters, not extracted from a full drawing kernel.
- Tolerance values are plausible demo defaults, not validated by manufacturing process capability.
- ASME/ISO compliance still needs a human checker or a rule-based GD&T validator.
- DXF export remains less reliable than SVG/PDF preview because the local DXF viewer has limited text/dimension support.

## Next CoBrA Goal

Turn this into a benchmark that scores CAD-to-GD&T output on:

- datum-feature clarity,
- FCF attachment and readability,
- basic dimension coverage,
- pattern callout grouping,
- title block completeness,
- visual overlap/cropping failure.
