Generate only the hand-attached jet module from the provided jet-suit reference image in CoBrA. Use millimeters and create editable B-rep CAD solids, not mesh-only geometry.

Scenario:
- The user provided a side-view image of a wearable jet suit and asked for only the hand-mounted jet, not the full suit.
- This is a fictional, non-official, non-flight-rated CAD visualization model. Do not provide operational thrust, fuel, control-law, or build instructions.

Design intent:
- Model a compact wrist/forearm-mounted hand jet module inspired by the image: open forearm cuff rings, retention straps, hand grip, trigger guard, twin downward cylindrical jet pods, vectoring nozzle rings, side service canisters, shielded control lines, protective guard cage, heat panels, access fasteners, warning lockout tags, and a small filming base.
- Do not model a human body, full backpack, legs, boots, helmet, flames, weapons, missiles, lasers, or blue energy effects. The output should read as a single removable hand jet assembly.

Required B-rep components:
- Rear forearm cuff ring and front wrist cuff ring with four adjustable straps and quick-release buckles.
- Dorsal bridge plate, lower load spreader, and removable ceramic heat barrier panels.
- Twin compact downward thruster pods with upper intake rings, dark intake screens, turbine case ribs, external cooling bands, heat-shielded short nozzles, vectoring exit rings, and dark open nozzle bores.
- Transverse palm grip, internal grip spine, non-operational trigger paddle, protective trigger guard loop, and grip-to-thruster support arms.
- Four side service canisters, valve blocks, shielded control lines, front/rear service bars, longitudinal guard rails, lower nozzle guard rails, and access fasteners.
- Small matte display base only for filming and scale; no body or full suit components.

Validation:
- Report bounding box, module length, module width, module height, forearm cuff diameter, primary thruster count, vector nozzle count, intake ring count, strap count, guard rail count, service canister count, fastener count, component count, and material separation.
- Verify interfaces: cuff-to-load-spreader, grip-to-support-arms, thruster-pods-to-lower-plate, nozzles-to-thruster-pods, service-canisters-to-side-brackets, and guard-rails-to-posts.
- Verify that full suit, body, backpack, legs, helmet, flames, weapons, and blue energy effects are not modeled.
- Export STEP, colored GLB, validation report, prompt artifact, component STEP files, and native parametric script.
