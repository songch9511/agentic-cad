Generate a Tesla Optimus-inspired next-generation humanoid robotic finger actuator concept in CoBrA. Use millimeters and create editable B-rep CAD solids, not mesh-only geometry.

Design a premium engineering concept for a humanoid robotic hand focused on the fingers: four articulated fingers and one opposed thumb mounted to a compact palm rail. The model should look like a next-gen humanoid dexterous end-effector, but it must be a non-proprietary concept with placeholder mechanisms.

Required components:
- Four multi-link fingers with three phalanges each: proximal, middle, distal.
- One opposed thumb with two phalanges and an angled thumb base.
- Rounded joint knuckles at each MCP/PIP/DIP joint.
- Slim internal tendon-routing channels represented as colored guide tubes.
- Compact linear micro-actuator placeholders inside the palm.
- Tactile fingertip pad inserts in dark rubber.
- Small fasteners, hinge pins, cable exits, and service covers.
- Exploded optional pose with a few fingers slightly flexed.

Parametric requirements:
- Define finger count, phalanx lengths, joint spacing, finger pitch, palm width, palm depth, actuator diameter, tendon tube radius, and pad thickness as named parameters.
- Derive all finger positions from the finger pitch and palm coordinate system.
- Keep palm, each finger link set, joints, tendon guides, actuators, pads, and fasteners as separate solids/components.
- Avoid fragile small booleans and avoid over-detailed internals.

Validation:
- Report total fingers, total joints, total phalanges, actuator count, tendon guide count, and bounding box.
- Verify finger links are centered on their joint axes and do not overlap adjacent fingers at the neutral pose.
- Export STEP, colored GLB, validation report, prompt, and native parametric script.
