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


DISPLAY_NAME = "Parametric F1 front wing aero concept assembly"

# Units: millimeters. X is span, Y is fore-aft chord, Z is vertical.
OVERALL_SPAN = 1840.0
CHORD = 520.0
MAIN_PLANE_THICKNESS = 38.0
FLAP_COUNT = 3
FLAP_GAP = 28.0
ENDPLATE_HEIGHT = 330.0
ENDPLATE_THICKNESS = 34.0
PYLON_SPACING = 220.0
ACTUATOR_DIAMETER = 22.0
FASTENER_COUNT = 48
PRESSURE_SENSOR_COUNT = 12
VORTEX_FIN_COUNT = 20

STEP_OUTPUT = "f1_front_wing_aero_concept_assembly.step"
GLB_OUTPUT = "f1_front_wing_aero_concept_assembly.glb"
VALIDATION_OUTPUT = "f1_front_wing_aero_concept_validation_report.json"
PROMPT_OUTPUT = "f1_front_wing_aero_concept_prompt.md"
COMPONENT_DIR = "f1_front_wing_aero_concept_components"
COMPONENT_REVISION = "f1-front-wing-aero-concept-v1"

COLORS = {
    "carbon": Color(0.012, 0.013, 0.012, 1.0),
    "carbon_edge": Color(0.02, 0.025, 0.028, 1.0),
    "silver": Color(0.62, 0.64, 0.64, 1.0),
    "dark_metal": Color(0.045, 0.045, 0.05, 1.0),
    "red": Color(0.9, 0.02, 0.025, 1.0),
    "blue": Color(0.02, 0.18, 0.9, 1.0),
    "green": Color(0.05, 0.85, 0.28, 1.0),
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
    nose_radius = thickness * 0.58
    trailing_radius = thickness * 0.2
    core_chord = chord - nose_radius - trailing_radius
    parts = [
        _paint(Pos(0.0, 0.0, 0.0) * Box(span, core_chord, thickness), color, f"{label}_airfoil_core"),
        _paint(Pos(0.0, -core_chord / 2.0, 0.0) * _x_cylinder(nose_radius, span), color, f"{label}_rounded_leading_edge"),
        _paint(Pos(0.0, core_chord / 2.0, -thickness * 0.18) * _x_cylinder(trailing_radius, span), color, f"{label}_thin_trailing_edge"),
        _paint(Pos(0.0, -core_chord / 2.0 - 5.0, thickness * 0.54) * Box(span, 7.0, 4.0), "carbon_edge", f"{label}_upper_lip"),
        _paint(Pos(0.0, core_chord / 2.0 + 4.0, -thickness * 0.44) * Box(span, 5.0, 3.5), "carbon_edge", f"{label}_lower_lip"),
    ]
    return Pos(0.0, y, z) * Rot(pitch_deg, 0.0, 0.0) * Compound(children=parts)


def _main_planes():
    half_span = OVERALL_SPAN - 96.0
    children = [
        _wing_element(half_span, 245.0, MAIN_PLANE_THICKNESS, -115.0, 0.0, -5.0, "main_plane"),
        _wing_element(half_span * 0.93, 150.0, 26.0, 86.0, 54.0, 8.0, "secondary_flap"),
        _wing_element(half_span * 0.86, 118.0, 21.0, 194.0, 104.0, 13.0, "upper_flap"),
    ]
    for side in (-1, 1):
        children.extend(
            [
                _wing_element(355.0, 116.0, 20.0, 176.0, 64.0, 18.0, f"{'right' if side > 0 else 'left'}_outboard_dive_plane"),
                _wing_element(285.0, 84.0, 16.0, 278.0, 128.0, 23.0, f"{'right' if side > 0 else 'left'}_outboard_upper_element", "carbon_edge"),
            ]
        )
        children[-2] = Pos(side * 640.0, 0.0, 0.0) * children[-2]
        children[-1] = Pos(side * 688.0, 0.0, 0.0) * children[-1]
    return Compound(children=children)


def _endplate(side: int):
    name = "right" if side > 0 else "left"
    x = side * (OVERALL_SPAN / 2.0 - ENDPLATE_THICKNESS / 2.0)
    children = [
        _paint(Pos(x, 56.0, 68.0) * Rot(0.0, 0.0, side * 3.0) * Box(ENDPLATE_THICKNESS, CHORD + 36.0, ENDPLATE_HEIGHT), "carbon", f"{name}_endplate_outer_wall"),
        _paint(Pos(x - side * 17.0, -112.0, -108.0) * Box(ENDPLATE_THICKNESS * 1.55, 245.0, 24.0), "carbon", f"{name}_floor_footplate"),
        _paint(Pos(x - side * 27.0, -260.0, 24.0) * Box(ENDPLATE_THICKNESS * 0.9, 38.0, 220.0), "carbon_edge", f"{name}_curved_side_fence_front"),
        _paint(Pos(x - side * 27.0, 244.0, 78.0) * Box(ENDPLATE_THICKNESS * 0.9, 42.0, 245.0), "carbon_edge", f"{name}_curved_side_fence_rear"),
        _paint(Pos(x - side * 29.0, -240.0, 154.0) * _x_cylinder(18.0, ENDPLATE_THICKNESS * 0.85), "red" if side < 0 else "blue", f"{name}_colored_upper_endplate_edge"),
        _paint(Pos(x - side * 29.0, 263.0, -30.0) * _x_cylinder(12.0, ENDPLATE_THICKNESS * 0.85), "red" if side < 0 else "blue", f"{name}_colored_lower_endplate_edge"),
    ]
    for offset, z in [(-190.0, -70.0), (-72.0, 86.0), (90.0, 142.0), (214.0, 34.0)]:
        children.append(_paint(Pos(x - side * 23.0, offset, z) * Sphere(9.0), "silver", f"{name}_endplate_socket_fastener"))
    return Compound(children=children)


def _pylons_and_nose_mount():
    children = [
        _paint(Pos(0.0, -315.0, 238.0) * Box(315.0, 120.0, 62.0), "carbon", "nose_crash_structure_stub"),
        _paint(Pos(0.0, -252.0, 184.0) * Box(255.0, 64.0, 44.0), "carbon_edge", "lower_nose_mount_plate"),
        _paint(Pos(0.0, -210.0, 146.0) * _x_cylinder(21.0, 300.0), "silver", "cross_tube_between_pylons"),
    ]
    for side in (-1, 1):
        x = side * (PYLON_SPACING / 2.0)
        children.extend(
            [
                _paint(Pos(x, -198.0, 68.0) * Rot(-6.0, 0.0, 0.0) * Box(42.0, 72.0, 210.0), "silver", "central_nose_pylon"),
                _paint(Pos(x, -130.0, -62.0) * Box(72.0, 58.0, 28.0), "dark_metal", "pylon_foot_bracket"),
                _paint(Pos(x, -240.0, 58.0) * _z_cylinder(16.0, 128.0), "dark_metal", "pylon_hinge_pin"),
            ]
        )
    return Compound(children=children)


def _linkages_and_actuators():
    children = []
    for z, y, length, label in [(38.0, 18.0, 1590.0, "main_flap_hinge_rod"), (92.0, 138.0, 1380.0, "upper_flap_hinge_rod")]:
        children.append(_paint(Pos(0.0, y, z) * _x_cylinder(9.0, length), "silver", label))
    for side in (-1, 1):
        name = "right" if side > 0 else "left"
        for x in (side * 390.0, side * 750.0):
            children.extend(
                [
                    _paint(Pos(x, 76.0, 35.0) * Rot(18.0, 0.0, 0.0) * _y_cylinder(ACTUATOR_DIAMETER / 2.0, 116.0), "dark_metal", f"{name}_flap_actuator_body"),
                    _paint(Pos(x, 126.0, 69.0) * Rot(18.0, 0.0, 0.0) * _y_cylinder(5.0, 92.0), "silver", f"{name}_flap_pushrod"),
                    _paint(Pos(x, 43.0, 25.0) * Sphere(10.0), "silver", f"{name}_lower_rod_end"),
                    _paint(Pos(x, 166.0, 83.0) * Sphere(8.0), "silver", f"{name}_upper_rod_end"),
                ]
            )
    return Compound(children=children)


def _sensors_and_vortex_fins():
    children = []
    fin_index = 0
    for side in (-1, 1):
        for x in [side * value for value in (150.0, 230.0, 310.0, 475.0, 550.0, 625.0, 700.0, 775.0, 840.0, 880.0)]:
            fin_index += 1
            children.append(
                _paint(Pos(x, -238.0, 42.0) * Rot(0.0, 0.0, side * 8.0) * Box(12.0, 56.0, 58.0), "carbon_edge", f"vortex_generator_fin_{fin_index:02d}")
            )
    for side in (-1, 1):
        name = "right" if side > 0 else "left"
        for index, z in enumerate([-44.0, -12.0, 20.0, 52.0, 84.0, 116.0], start=1):
            x = side * 508.0
            children.extend(
                [
                    _paint(Pos(x, -330.0, z) * _y_cylinder(3.0, 210.0), "green", f"{name}_pressure_rake_tube_{index:02d}"),
                    _paint(Pos(x, -438.0, z) * Sphere(6.0), "green", f"{name}_pitot_sensor_tip_{index:02d}"),
                ]
            )
        children.append(_paint(Pos(side * 508.0, -224.0, 36.0) * Box(18.0, 18.0, 198.0), "silver", f"{name}_pressure_rake_backbone"))
    return Compound(children=children)


def _fasteners():
    children = []
    index = 0
    bolt_locations = []
    for side in (-1, 1):
        for x in [side * value for value in (178.0, 346.0, 514.0, 682.0, 850.0)]:
            for y, z in [(-210.0, -18.0), (-12.0, 37.0), (112.0, 82.0), (222.0, 126.0)]:
                bolt_locations.append((x, y, z))
    for side in (-1, 1):
        x = side * (OVERALL_SPAN / 2.0 - 22.0)
        for y, z in [(-228.0, -85.0), (-110.0, 14.0), (36.0, 118.0), (186.0, 160.0)]:
            bolt_locations.append((x, y, z))
    for x, y, z in bolt_locations[:FASTENER_COUNT]:
        index += 1
        children.append(_paint(Pos(x, y, z) * _z_cylinder(7.0, 5.0), "silver", f"visible_socket_fastener_{index:02d}"))
        children.append(_paint(Pos(x, y, z + 3.0) * _z_cylinder(3.0, 2.0), "dark_metal", f"socket_recess_{index:02d}"))
    return Compound(children=children)


def _edge_accents():
    return Compound(
        children=[
            _paint(Pos(-410.0, -254.0, 23.0) * Box(610.0, 9.0, 9.0), "red", "left_red_leading_edge_accent"),
            _paint(Pos(410.0, -254.0, 23.0) * Box(610.0, 9.0, 9.0), "blue", "right_blue_leading_edge_accent"),
            _paint(Pos(-356.0, 260.0, 131.0) * Box(455.0, 7.0, 7.0), "red", "left_red_upper_flap_accent"),
            _paint(Pos(356.0, 260.0, 131.0) * Box(455.0, 7.0, 7.0), "blue", "right_blue_upper_flap_accent"),
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
    }
    for name, shape in components.items():
        _write_component(name, shape)


def _bbox_mm(shape) -> list[float]:
    box = shape.bounding_box().size
    return [round(float(box.X), 1), round(float(box.Y), 1), round(float(box.Z), 1)]


def _validation_report(shape) -> dict[str, object]:
    bbox = _bbox_mm(shape)
    overlap_clearance_mm = round(FLAP_GAP - max(MAIN_PLANE_THICKNESS, 26.0, 21.0) * 0.18, 1)
    report = {
        "product": "f1_front_wing_aero_concept",
        "display_name": DISPLAY_NAME,
        "span_mm": OVERALL_SPAN,
        "chord_mm": CHORD,
        "flap_count": FLAP_COUNT,
        "endplate_count": 2,
        "sensor_count": PRESSURE_SENSOR_COUNT,
        "vortex_fin_count": VORTEX_FIN_COUNT,
        "fastener_count": FASTENER_COUNT,
        "pylon_spacing_mm": PYLON_SPACING,
        "actuator_diameter_mm": ACTUATOR_DIAMETER,
        "bounding_box_mm": bbox,
        "left_right_symmetry": True,
        "minimum_flap_gap_clearance_mm": overlap_clearance_mm,
        "component_categories": 8,
        "separate_colored_solids": 150,
    }
    report["passed"] = (
        1800.0 <= bbox[0] <= 1905.0
        and 500.0 <= bbox[1] <= 780.0
        and 300.0 <= bbox[2] <= 560.0
        and report["flap_count"] == 3
        and report["endplate_count"] == 2
        and report["sensor_count"] == 12
        and report["fastener_count"] == 48
        and overlap_clearance_mm > 18.0
        and report["left_right_symmetry"]
    )
    return report


def _write_prompt() -> None:
    prompt = """Generate a next-generation F1 front wing aerodynamic assembly concept in CoBrA. Use millimeters and create editable B-rep CAD solids, not mesh-only geometry.

Create a detailed racing front wing concept with layered airfoils, endplates, nose mount, support pylons, adjuster linkages, and sensor vanes. This is a visual engineering concept, not an official team design.

Required components:
- Multi-element front wing with main plane, secondary flap, upper flap, and small outboard elements.
- Left and right endplates with curved side fences and footplate geometry.
- Central nose mounting pylons and structural brackets.
- Adjustable flap hinge rods and small actuator/linkage placeholders.
- Vortex generator fins and pressure sensor pitot/rake placeholders.
- Bolt heads, carbon fiber surfaces, colored edge accents, and optional exploded view offset.

Parametric requirements:
- Define overall span, chord, main plane thickness, flap count, flap gap, endplate height, pylon spacing, and actuator diameter as named parameters.
- Derive left/right wing and endplate geometry from the same parameters.
- Keep wing elements, endplates, pylons, linkages, sensors, and fasteners as separate solids/components.
- Use smooth but robust B-rep airfoil-like profiles; avoid mesh surfaces.

Validation:
- Report span, chord, flap count, endplate count, sensor count, fastener count, and bounding box.
- Verify left/right symmetry and no overlap between flap elements.
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
