Generate an F1-style racing steering wheel in CoBrA from a single prompt. Use millimeters and create editable B-rep CAD solids, not mesh-only geometry.

Reference-driven design:
- Overall front envelope approximately 270 mm wide, 183 mm tall, and 67 mm deep.
- Flat carbon-composite face plate with large side hand openings.
- Left and right suede/alcantara grips with clamp blocks and socket screws.
- Central 96 x 46 mm LCD telemetry display with tachometer ruler and large numeric readouts.
- Four teal pushbuttons near the upper grip transitions.
- Four red pushbuttons on lower angled button pods.
- Eight small shift LEDs above the display.
- Rear quick-release steering column hub, rear electronics blocks, and two shift paddles.

Parametric requirements:
- Define width, height, depth, display size, grip size, button radius, and paddle offset as named parameters.
- Keep face plate, grips, display stack, controls, rear hub, and paddles as separate components.
- Use robust B-rep primitives and simple extruded outlines; avoid fragile decorative booleans.
- Export assembled STEP, colored viewer GLB, validation report, prompt, and native parametric script.

Validation:
- Verify 270 mm class width, 183 mm class height, and 67 mm class depth.
- Verify display, 4 teal buttons, 4 red buttons, 8 shift LEDs, visible screws, rear paddles, and quick-release hub.
