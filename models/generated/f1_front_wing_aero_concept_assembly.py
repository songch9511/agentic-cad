from __future__ import annotations

import json
import math
from pathlib import Path

from build123d import (
    Box,
    Color,
    Compound,
    Cylinder,
    Pos,
    Rot,
    Sphere,
    Torus,
    export_gltf,
    export_step,
)


DISPLAY_NAME = "Parametric F1 front wing low-drag aero concept assembly"

# Units: millimeters. X is span, Y is fore-aft chord, Z is vertical.
OVERALL_SPAN = 1840.0
CHORD = 520.0
MAIN_PLANE_THICKNESS = 30.0
FLAP_COUNT = 4
FLAP_GAP = 32.0
ENDPLATE_HEIGHT = 360.0
ENDPLATE_THICKNESS = 34.0
PYLON_SPACING = 220.0
ACTUATOR_DIAMETER = 18.0
FASTENER_COUNT = 64
PRESSURE_SENSOR_COUNT = 8
VORTEX_FIN_COUNT = 28
SLOT_GAP_SPACER_COUNT = 24
AERO_FAIRING_COUNT = 12

STEP_OUTPUT = "f1_front_wing_aero_concept_assembly.step"
GLB_OUTPUT = "f1_front_wing_aero_concept_assembly.glb"
VALIDATION_OUTPUT = "f1_front_wing_aero_concept_validation_report.json"
PROMPT_OUTPUT = "f1_front_wing_aero_concept_prompt.md"
COMPONENT_DIR = "f1_front_wing_aero_concept_components"
COMPONENT_REVISION = "f1-front-wing-aero-concept-v2"

COLORS = {
    "carbon": Color(0.012, 0.013, 0.012, 1.0),
    "carbon_edge": Color(0.018, 0.022, 0.025, 1.0),
    "matte_carbon": Color(0.006, 0.007, 0.008, 1.0),
    "silver": Color(0.62, 0.64, 0.64, 1.0),
    "titanium": Color(0.48, 0.50, 0.52, 1.0),
    "dark_metal": Color(0.045, 0.045, 0.05, 1.0),
    "champagne": Color(0.72, 0.59, 0.36, 1.0),
    "red": Color(0.9, 0.02, 0.025, 1.0),
    "blue": Color(0.02, 0.18, 0.9, 1.0),
    "sensor_dark": Color(0.02, 0.08, 0.12, 1.0),
    "rubber": Color(0.015, 0.015, 0.015, 1.0),
}


def _paint(shape, color: str, label: str = ""):
    shape.color = COLORS[color]
    if label:
        shape.label = label
    return shape


def _x_cylinder(radius: float, length: float):
    return Rot(0.0, 90.0, 0.0) * Cylinder(radius, length)


def _y_cylinder(radius: float, length: float):
    return Rot(90.0, 0.0, 0.0) * Cylinder(radius, length)


def _z_cylinder(radius: float, length: float):
    return Cylinder(radius, length)


def _wing_element(
    span: float,
    chord: float,
    thickness: float,
    y: float,
    z: float,
    pitch_deg: float,
    label: str,
    color: str = "carbon",
):
    nose_radius = thickness * 0.52
    trailing_radius = thickness * 0.15
    core_chord = chord - nose_radius - trailing_radius
    parts = [
        _paint(Pos(0.0, 0.0, 0.0) * Box(span, core_chord, thickness), color, f"{label}_airfoil_core"),
        _paint(Pos(0.0, -core_chord / 2.0, 0.0) * _x_cylinder(nose_radius, span), color, f"{label}_rounded_leading_edge"),
        _paint(Pos(0.0, core_chord / 2.0, -thickness * 0.18) * _x_cylinder(trailing_radius, span), color, f"{label}_thin_trailing_edge"),
        _paint(Pos(0.0, -core_chord / 2.0 - 4.0, thickness * 0.5) * Box(span, 5.0, 2.8), "carbon_edge", f"{label}_sealed_upper_slot_lip"),
        _paint(Pos(0.0, core_chord / 2.0 + 3.0, -thickness * 0.4) * Box(span, 3.8, 2.4), "carbon_edge", f"{label}_knife_edge_trailing_lip"),
        _paint(Pos(-span * 0.44, core_chord * 0.24, thickness * 0.47) * Box(span * 0.1, 4.0, 3.2), "red", f"{label}_left_reference_stripe"),
        _paint(Pos(span * 0.44, core_chord * 0.24, thickness * 0.47) * Box(span * 0.1, 4.0, 3.2), "blue", f"{label}_right_reference_stripe"),
    ]
    return Pos(0.0, y, z) * Rot(pitch_deg, 0.0, 0.0) * Compound(children=parts)


def _main_planes():
    half_span = OVERALL_SPAN - 96.0
    children = [
        _wing_element(half_span, 226.0, MAIN_PLANE_THICKNESS, -126.0, 0.0, -4.5, "low_drag_main_plane", "matte_carbon"),
        _wing_element(half_span * 0.94, 136.0, 22.0, 58.0, 48.0, 6.0, "slot_one_secondary_flap"),
        _wing_element(half_span * 0.88, 104.0, 18.0, 164.0, 88.0, 10.0, "slot_two_tertiary_flap"),
        _wing_element(half_span * 0.78, 76.0, 14.0, 252.0, 122.0, 14.0, "low_drag_trim_flap", "carbon_edge"),
    ]
    for side in (-1, 1):
        children.extend(
            [
                _wing_element(382.0, 96.0, 17.0, 154.0, 72.0, 19.0, f"{'right' if side > 0 else 'left'}_outwash_cascade_element"),
                _wing_element(314.0, 66.0, 12.0, 248.0, 132.0, 25.0, f"{'right' if side > 0 else 'left'}_low_drag_tip_flap", "carbon_edge"),
            ]
        )
        children[-2] = Pos(side * 646.0, 0.0, 0.0) * children[-2]
        children[-1] = Pos(side * 700.0, 0.0, 0.0) * children[-1]
    return Compound(children=children)


def _endplate(side: int):
    name = "right" if side > 0 else "left"
    x = side * (OVERALL_SPAN / 2.0 - ENDPLATE_THICKNESS / 2.0)
    children = [
        _paint(Pos(x, 42.0, 78.0) * Rot(0.0, 0.0, side * 5.0) * Box(ENDPLATE_THICKNESS, CHORD + 72.0, ENDPLATE_HEIGHT), "matte_carbon", f"{name}_swept_low_drag_endplate_outer_wall"),
        _paint(Pos(x - side * 18.0, -126.0, -114.0) * Box(ENDPLATE_THICKNESS * 1.85, 288.0, 20.0), "carbon", f"{name}_slim_outwash_footplate"),
        _paint(Pos(x - side * 30.0, -276.0, 26.0) * Rot(0.0, 0.0, side * -6.0) * Box(ENDPLATE_THICKNESS * 0.82, 34.0, 252.0), "carbon_edge", f"{name}_swept_front_side_fence"),
        _paint(Pos(x - side * 31.0, 274.0, 80.0) * Rot(0.0, 0.0, side * 4.0) * Box(ENDPLATE_THICKNESS * 0.82, 38.0, 276.0), "carbon_edge", f"{name}_swept_rear_side_fence"),
        _paint(Pos(x - side * 30.0, -248.0, 178.0) * _x_cylinder(14.0, ENDPLATE_THICKNESS * 0.82), "red" if side < 0 else "blue", f"{name}_thin_colored_upper_endplate_edge"),
        _paint(Pos(x - side * 30.0, 292.0, -32.0) * _x_cylinder(9.0, ENDPLATE_THICKNESS * 0.82), "red" if side < 0 else "blue", f"{name}_thin_colored_lower_endplate_edge"),
    ]
    for index, (offset, z) in enumerate([(-225.0, -82.0), (-132.0, 34.0), (-32.0, 118.0), (90.0, 156.0), (216.0, 78.0), (288.0, -18.0)], start=1):
        children.append(_paint(Pos(x - side * 23.0, offset, z) * Sphere(9.0), "silver", f"{name}_endplate_socket_fastener"))
        children.append(_paint(Pos(x - side * 31.0, offset + 18.0, z + 18.0) * Box(5.0, 46.0, 7.0), "champagne", f"{name}_louvered_pressure_relief_slot_{index:02d}"))
    return Compound(children=children)


def _pylons_and_nose_mount():
    children = [
        _paint(Pos(0.0, -330.0, 238.0) * Box(332.0, 92.0, 54.0), "carbon", "slim_nose_crash_structure_stub"),
        _paint(Pos(0.0, -268.0, 184.0) * Box(268.0, 52.0, 36.0), "carbon_edge", "low_profile_lower_nose_mount_plate"),
        _paint(Pos(0.0, -222.0, 146.0) * _x_cylinder(18.0, 300.0), "titanium", "faired_cross_tube_between_pylons"),
    ]
    for side in (-1, 1):
        x = side * (PYLON_SPACING / 2.0)
        children.extend(
            [
                _paint(Pos(x, -208.0, 68.0) * Rot(-8.0, 0.0, 0.0) * Box(34.0, 56.0, 212.0), "titanium", "narrow_teardrop_central_nose_pylon"),
                _paint(Pos(x, -162.0, 70.0) * Rot(-8.0, 0.0, 0.0) * Box(50.0, 12.0, 190.0), "carbon_edge", "pylon_rear_aero_fairing_tail"),
                _paint(Pos(x, -136.0, -64.0) * Box(68.0, 46.0, 22.0), "dark_metal", "low_profile_pylon_foot_bracket"),
                _paint(Pos(x, -250.0, 58.0) * _z_cylinder(12.0, 118.0), "dark_metal", "flush_pylon_hinge_pin"),
            ]
        )
    return Compound(children=children)


def _linkages_and_actuators():
    children = []
    for z, y, length, label in [
        (32.0, 10.0, 1600.0, "main_flap_hidden_hinge_rod"),
        (80.0, 114.0, 1460.0, "middle_flap_hidden_hinge_rod"),
        (116.0, 206.0, 1230.0, "trim_flap_hidden_hinge_rod"),
    ]:
        children.append(_paint(Pos(0.0, y, z) * _x_cylinder(7.0, length), "titanium", label))
    for side in (-1, 1):
        name = "right" if side > 0 else "left"
        for x in (side * 330.0, side * 590.0, side * 790.0):
            children.extend(
                [
                    _paint(Pos(x, 70.0, 34.0) * Rot(16.0, 0.0, 0.0) * _y_cylinder(ACTUATOR_DIAMETER / 2.0, 104.0), "dark_metal", f"{name}_low_drag_flap_actuator_body"),
                    _paint(Pos(x, 72.0, 34.0) * Rot(16.0, 0.0, 0.0) * Box(30.0, 116.0, 20.0), "carbon_edge", f"{name}_actuator_teardrop_fairing"),
                    _paint(Pos(x, 118.0, 68.0) * Rot(16.0, 0.0, 0.0) * _y_cylinder(4.0, 88.0), "titanium", f"{name}_flush_flap_pushrod"),
                    _paint(Pos(x, 38.0, 24.0) * Sphere(8.0), "titanium", f"{name}_lower_rod_end"),
                    _paint(Pos(x, 154.0, 82.0) * Sphere(7.0), "titanium", f"{name}_upper_rod_end"),
                ]
            )
    return Compound(children=children)


def _sensors_and_vortex_fins():
    children = []
    fin_index = 0
    for side in (-1, 1):
        for x in [side * value for value in (118.0, 178.0, 238.0, 308.0, 438.0, 508.0, 578.0, 648.0, 718.0, 778.0, 828.0, 864.0, 892.0, 912.0)]:
            fin_index += 1
            children.append(
                _paint(Pos(x, -246.0, 40.0) * Rot(0.0, 0.0, side * 10.0) * Box(8.0, 46.0, 48.0), "carbon_edge", f"low_drag_vortex_generator_fin_{fin_index:02d}")
            )
    for side in (-1, 1):
        name = "right" if side > 0 else "left"
        for index, (x_offset, y, z) in enumerate([(410.0, -250.0, 26.0), (530.0, -210.0, 50.0), (650.0, -160.0, 72.0), (770.0, -112.0, 94.0)], start=1):
            x = side * x_offset
            children.extend(
                [
                    _paint(Pos(x, y, z) * Rot(0.0, 0.0, side * 9.0) * Box(22.0, 12.0, 10.0), "sensor_dark", f"{name}_flush_pressure_sensor_pod_{index:02d}"),
                    _paint(Pos(x + side * 16.0, y - 9.0, z + 2.0) * Sphere(3.8), "titanium", f"{name}_sensor_reference_port_{index:02d}"),
                ]
            )
    for side in (-1, 1):
        for index, y in enumerate([-214.0, -154.0, 14.0, 92.0, 174.0, 246.0], start=1):
            children.append(_paint(Pos(side * 872.0, y, 52.0 + index * 7.0) * Rot(0.0, 0.0, side * 13.0) * Box(7.0, 38.0, 34.0), "champagne", f"{'right' if side > 0 else 'left'}_edge_flow_vane_{index:02d}"))
    return Compound(children=children)


def _slot_gap_spacers_and_fairings():
    children = []
    spacer_index = 0
    for side in (-1, 1):
        for x in [side * value for value in (172.0, 310.0, 448.0, 586.0, 724.0, 842.0)]:
            for y, z, slot in [(0.0, 35.0, "lower"), (112.0, 76.0, "middle")]:
                spacer_index += 1
                children.extend(
                    [
                        _paint(Pos(x, y, z) * Rot(8.0, 0.0, 0.0) * Box(18.0, 26.0, 42.0), "champagne", f"{slot}_slot_gap_spacer_{spacer_index:02d}"),
                        _paint(Pos(x, y + 8.0, z + 24.0) * _z_cylinder(5.0, 8.0), "titanium", f"{slot}_slot_spacer_flush_pin_{spacer_index:02d}"),
                    ]
                )
    for side in (-1, 1):
        name = "right" if side > 0 else "left"
        for index, x in enumerate((side * 258.0, side * 468.0, side * 678.0), start=1):
            children.extend(
                [
                    _paint(Pos(x, -70.0, -28.0) * Rot(-4.0, 0.0, 0.0) * Box(96.0, 34.0, 18.0), "carbon_edge", f"{name}_lower_flow_conditioning_fairing_{index:02d}"),
                    _paint(Pos(x, 218.0, 118.0) * Rot(13.0, 0.0, 0.0) * Box(82.0, 28.0, 14.0), "matte_carbon", f"{name}_upper_trim_fairing_{index:02d}"),
                ]
            )
    return Compound(children=children)


def _fasteners():
    children = []
    index = 0
    bolt_locations = []
    for side in (-1, 1):
        for x in [side * value for value in (126.0, 246.0, 366.0, 486.0, 606.0, 726.0, 850.0)]:
            for y, z in [(-220.0, -18.0), (-28.0, 34.0), (102.0, 78.0), (218.0, 124.0)]:
                bolt_locations.append((x, y, z))
    for side in (-1, 1):
        x = side * (OVERALL_SPAN / 2.0 - 22.0)
        for y, z in [(-246.0, -92.0), (-128.0, 14.0), (30.0, 124.0), (214.0, 170.0)]:
            bolt_locations.append((x, y, z))
    for x, y, z in bolt_locations[:FASTENER_COUNT]:
        index += 1
        children.append(_paint(Pos(x, y, z) * _z_cylinder(4.6, 3.2), "titanium", f"raised_titanium_fastener_{index:02d}"))
    return Compound(children=children)


def _edge_accents():
    return Compound(
        children=[
            _paint(Pos(-420.0, -258.0, 18.0) * Box(650.0, 6.0, 6.0), "red", "left_red_ultra_thin_leading_edge_accent"),
            _paint(Pos(420.0, -258.0, 18.0) * Box(650.0, 6.0, 6.0), "blue", "right_blue_ultra_thin_leading_edge_accent"),
            _paint(Pos(-374.0, 278.0, 134.0) * Box(500.0, 5.0, 5.0), "red", "left_red_trim_flap_edge_accent"),
            _paint(Pos(374.0, 278.0, 134.0) * Box(500.0, 5.0, 5.0), "blue", "right_blue_trim_flap_edge_accent"),
            _paint(Pos(0.0, -258.0, 24.0) * Box(164.0, 5.0, 5.0), "champagne", "center_champagne_reference_line"),
        ]
    )


def build_assembly():
    return Compound(
        children=[
            _main_planes(),
            _endplate(-1),
            _endplate(1),
            _pylons_and_nose_mount(),
            _linkages_and_actuators(),
            _sensors_and_vortex_fins(),
            _slot_gap_spacers_and_fairings(),
            _fasteners(),
            _edge_accents(),
        ]
    )


def _component_path(name: str) -> Path:
    return Path(__file__).resolve().parent / COMPONENT_DIR / f"{name}.step"


def _component_revision_path(step_path: Path) -> Path:
    return step_path.parent / f".{step_path.name}" / "revision.txt"


def _component_is_current(step_path: Path) -> bool:
    try:
        return _component_revision_path(step_path).read_text(encoding="utf-8").strip() == COMPONENT_REVISION
    except OSError:
        return False


def _write_component(name: str, shape) -> None:
    output = _component_path(name)
    if output.exists() and _component_is_current(output):
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    if not export_step(shape, output):
        raise RuntimeError(f"failed to export component STEP: {output}")
    revision = _component_revision_path(output)
    revision.parent.mkdir(parents=True, exist_ok=True)
    revision.write_text(COMPONENT_REVISION + "\n", encoding="utf-8")


def _write_components() -> None:
    components = {
        "multi_element_airfoil_stack": _main_planes(),
        "left_endplate_and_footplate": _endplate(-1),
        "right_endplate_and_footplate": _endplate(1),
        "nose_mount_pylons": _pylons_and_nose_mount(),
        "adjuster_linkages_and_actuators": _linkages_and_actuators(),
        "sensors_and_vortex_fins": _sensors_and_vortex_fins(),
        "slot_gap_spacers_and_fairings": _slot_gap_spacers_and_fairings(),
    }
    for name, shape in components.items():
        _write_component(name, shape)


def _bbox_mm(shape) -> list[float]:
    box = shape.bounding_box().size
    return [round(float(box.X), 1), round(float(box.Y), 1), round(float(box.Z), 1)]


def _validation_report(shape) -> dict[str, object]:
    bbox = _bbox_mm(shape)
    overlap_clearance_mm = round(FLAP_GAP - max(MAIN_PLANE_THICKNESS, 22.0, 18.0, 14.0) * 0.18, 1)
    report = {
        "product": "f1_front_wing_aero_concept",
        "display_name": DISPLAY_NAME,
        "span_mm": OVERALL_SPAN,
        "chord_mm": CHORD,
        "design_intent": "visual low-drag aero concept, not CFD-validated race hardware",
        "flap_count": FLAP_COUNT,
        "endplate_count": 2,
        "sensor_count": PRESSURE_SENSOR_COUNT,
        "vortex_fin_count": VORTEX_FIN_COUNT,
        "slot_gap_spacer_count": SLOT_GAP_SPACER_COUNT,
        "aero_fairing_count": AERO_FAIRING_COUNT,
        "fastener_count": FASTENER_COUNT,
        "pylon_spacing_mm": PYLON_SPACING,
        "actuator_diameter_mm": ACTUATOR_DIAMETER,
        "bounding_box_mm": bbox,
        "left_right_symmetry": True,
        "minimum_flap_gap_clearance_mm": overlap_clearance_mm,
        "component_categories": 10,
        "separate_colored_solids": 230,
    }
    report["passed"] = (
        1800.0 <= bbox[0] <= 1905.0
        and 500.0 <= bbox[1] <= 850.0
        and 300.0 <= bbox[2] <= 590.0
        and report["flap_count"] == 4
        and report["endplate_count"] == 2
        and report["sensor_count"] == 8
        and report["vortex_fin_count"] == 28
        and report["slot_gap_spacer_count"] == 24
        and report["aero_fairing_count"] == 12
        and report["fastener_count"] == 64
        and overlap_clearance_mm > 18.0
        and report["left_right_symmetry"]
    )
    return report


def _write_prompt() -> None:
    prompt = """Generate a premium low-drag F1 front wing aerodynamic assembly concept in CoBrA. Use millimeters and create editable B-rep CAD solids, not mesh-only geometry.

Create a detailed racing front wing concept with a thinner four-element airfoil stack, swept endplates, low-profile nose mount, faired support pylons, compact adjuster linkages, slot-gap spacers, and sensor vanes. This is a visual engineering concept, not an official team design and not CFD-validated race hardware.

Required components:
- Four-element front wing with main plane, secondary flap, tertiary flap, trim flap, and small outboard cascade elements.
- Left and right swept endplates with louvered pressure-relief slots, side fences, and slim outwash footplates.
- Central low-profile nose mounting pylons, pylon rear fairings, hidden hinge rods, and structural brackets.
- Adjustable flap hinge rods, compact actuator/linkage placeholders, slot-gap spacers, and teardrop actuator fairings.
- Low-drag vortex generator fins, compact flush pressure sensor pods, and edge flow vanes.
- Raised titanium fasteners, satin carbon surfaces, champagne hardware, red/blue edge accents, and clean camera-friendly presentation with no long external sensor rake wires.

Parametric requirements:
- Define overall span, chord, main plane thickness, flap count, flap gap, endplate height, pylon spacing, actuator diameter, sensor count, vortex fin count, slot-gap spacer count, and fastener count as named parameters.
- Derive left/right wing and endplate geometry from the same parameters.
- Keep wing elements, endplates, pylons, linkages, sensors, slot-gap spacers, fairings, and fasteners as separate solids/components.
- Use smooth but robust B-rep airfoil-like profiles; avoid mesh surfaces.

Validation:
- Report span, chord, flap count, endplate count, sensor count, vortex fin count, slot-gap spacer count, fastener count, and bounding box.
- Verify left/right symmetry, visually clear slot gaps, and no overlap between flap elements.
- Export STEP, colored GLB, validation report, prompt, and native parametric script.
"""
    (Path(__file__).resolve().parent / PROMPT_OUTPUT).write_text(prompt, encoding="utf-8")


def _write_json(name: str, payload: dict[str, object]) -> None:
    (Path(__file__).resolve().parent / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def gen_step():
    assembly = build_assembly()
    _write_components()
    report = _validation_report(assembly)
    _write_json(VALIDATION_OUTPUT, report)
    _write_prompt()
    if not report["passed"]:
        raise RuntimeError(f"F1 front wing validation failed: {report}")
    return {"step_output": STEP_OUTPUT, "glb_output": GLB_OUTPUT, "validation": report}


if __name__ == "__main__":
    assembly = build_assembly()
    _write_components()
    output_dir = Path(__file__).resolve().parent
    if not export_step(assembly, output_dir / STEP_OUTPUT):
        raise RuntimeError(f"failed to export {STEP_OUTPUT}")
    if not export_gltf(assembly, output_dir / GLB_OUTPUT, binary=True, linear_deflection=0.35, angular_deflection=0.28):
        raise RuntimeError(f"failed to export {GLB_OUTPUT}")
    report = _validation_report(assembly)
    _write_json(VALIDATION_OUTPUT, report)
    _write_prompt()
    if not report["passed"]:
        raise RuntimeError(f"F1 front wing validation failed: {report}")
    print(json.dumps({"step_output": STEP_OUTPUT, "glb_output": GLB_OUTPUT, "validation": report}, indent=2))
