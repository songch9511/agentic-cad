Generate a fully parametric B-rep CAD assembly of a compact quadrotor drone from a single prompt. Use millimeters. Build editable solid CAD geometry, not mesh-only geometry.

Core design:
- Product: compact camera-ready quadrotor drone assembly generated from one prompt
- Overall style: premium lightweight consumer/prosumer drone, manufacturable, clean technical design
- Airframe: X-layout quadrotor with a two-plate center frame, standoffs, and detachable arms
- Electronics architecture: LiPo battery feeds a central power distribution board, four ESCs mounted on the arms, a flight controller on vibration pads, and a radio receiver near the controller
- Materials: matte black carbon-fiber-style frame, dark graphite molded body shell, brushed aluminum motor cans, translucent smoke propellers, black ESC heat-shrink modules, dark lithium-polymer battery pack
- Size target: approximately 260 mm motor-to-motor diagonal, compact enough for a desk demo

Global parameters:
- motor_to_motor_diagonal = 260 mm
- arm_length = 92 mm
- arm_width = 12 mm
- arm_height = 5 mm
- center_body_length = 76 mm
- center_body_width = 56 mm
- body_shell_height = 16 mm
- motor_can_diameter = 24 mm
- motor_can_height = 10 mm
- propeller_diameter = 118 mm
- propeller_blade_width = 12 mm
- propeller_thickness = 1.8 mm
- battery_length = 62 mm
- battery_width = 34 mm
- battery_height = 13 mm
- landing_skid_height = 28 mm
- camera_gimbal_width = 24 mm
- camera_lens_diameter = 10 mm
- esc_length = 32 mm
- esc_width = 13 mm
- pdb_size = 34 mm x 28 mm
- flight_controller_size = 30 mm x 30 mm
- receiver_size = 28 mm x 16 mm

Assembly parts:
1. Central lower carbon frame plate.
2. Upper electronics cover plate or shell separated by standoffs.
3. Four carbon arms in X-layout, derived from the motor center positions.
4. Four cylindrical brushless motor placeholders.
5. Four simplified two-blade propellers, alternating CW/CCW orientation.
6. Underslung battery pack with small retention straps.
7. Four ESC modules strapped near the midpoint of each arm.
8. Central power distribution board with battery lead pads.
9. Flight-controller stack on vibration isolation pads with a forward arrow.
10. Radio receiver with antenna pair.
11. Front camera module with gimbal yoke and circular lens.
12. Four landing legs and two skid rails.
13. Small screw heads or fasteners at arm roots and motor mounts.
14. Simplified red/black/signal wire bundles running battery-to-PDB, PDB-to-ESC, and ESC-to-motor.

Parametric requirements:
- Derive motor positions from motor_to_motor_diagonal.
- Derive arm length and ESC placement from motor positions.
- Keep all parts separate in the assembly tree.
- Use named parameters and simple construction helpers.
- Avoid fragile decorative details or expensive boolean operations.
- Use simple B-rep solids: boxes, cylinders, chamfered boxes, and simplified propeller blade solids.
- Changing diagonal, arm length, motor can size, propeller diameter, or landing skid height must regenerate cleanly.

Validation:
- Verify exactly 4 motors, 4 propeller assemblies, 4 arms, and 4 landing legs.
- Verify exactly 4 ESC modules and one flight controller.
- Verify CW/CCW propeller orientation alternates across diagonal motor pairs.
- Verify propeller disks do not intersect the central body envelope.
- Verify battery clears landing skids.
- Report final bounding box dimensions.
- Export a linked assembly STEP file and keep the native parametric CAD script.
