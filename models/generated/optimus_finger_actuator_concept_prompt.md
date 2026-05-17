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
- Clevis-style yoke brackets, bearing end caps, raised indexing rails, recessed service grooves, and joint clearance collars.
- Advanced flexed presentation pose where every phalanx link rotates from its own MCP/PIP/DIP joint axis with stronger cumulative local joint angles instead of being translated downward as a flat chain.

Parametric requirements:
- Define finger count, phalanx lengths, joint spacing, finger pitch, palm width, palm depth, actuator diameter, tendon tube radius, and pad thickness as named parameters.
- Derive all finger positions from the finger pitch and palm coordinate system.
- Derive each fingertip chain from named per-segment yaw angles and cumulative local joint flexion angles, so each downstream phalanx inherits the previous joint rotation and all link bodies/tendon tubes align to the true joint-to-joint vector.
- Add visible horizontal hinge-axis pins through the knuckles so the rotation axis is legible at each MCP/PIP/DIP joint.
- Use each phalanx segment's local along/side/top-normal frame for shell panels, tendon tubes, fasteners, fingertip pads, and distal carriers so details rotate in the same direction as the joint chain.
- Add paired side clevis brackets around each knuckle, bearing end caps on hinge pins, precision joint collars at phalanx ends, and longitudinal service rails/grooves on each link.
- Keep palm, each finger link set, joints, tendon guides, actuators, pads, and fasteners as separate solids/components.
- Avoid fragile small booleans and avoid over-detailed internals.

Validation:
- Report total fingers, total joints, total phalanges, actuator count, tendon guide count, and bounding box.
- Verify finger links are centered on their joint axes, cumulative joint-angle profiles are reported, horizontal hinge axes are modeled, clevis/bearing/link-service details are present, segment-local surface details are aligned, and adjacent fingers do not overlap at the neutral pose.
- Export STEP, colored GLB, validation report, prompt, and native parametric script.
