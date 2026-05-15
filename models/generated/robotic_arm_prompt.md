Generate and simulate a six-axis industrial robotic arm assembly from a single prompt. Use millimeters and build editable B-rep CAD geometry, not mesh-only geometry.

Core design:
- Product: compact six-axis articulated robotic arm with parallel gripper
- Parts: base plate, rotary turntable, column, shoulder yoke, upper arm link, elbow joint, forearm link, wrist pitch/roll stack, tool flange, two-finger gripper, cable carrier, controller box, and work fixture
- Style: manufacturable AI-native engineering demo, clean industrial proportions, separate assembly components
- Simulation: deterministic forward-kinematics pose sweep for pick, clearance lift, and place states

Parametric requirements:
- Define link lengths, joint positions, nominal joint angles, and joint limits as named parameters.
- Derive shoulder, elbow, wrist, flange, and TCP positions from the kinematic layout.
- Keep all major parts as separate solids or components.
- Export assembled STEP, simulation sweep STEP, viewer GLB, source script, validation report, and simulation report.

Validation:
- Verify 6 axes, 10 component categories, gripper, cable carrier, controller fixture, 3 simulation frames, TCP positions, and bounding boxes.
