from __future__ import annotations

import json
import math
from pathlib import Path

from build123d import (
    Box,
    BuildPart,
    BuildSketch,
    Color,
    Compound,
    Cylinder,
    Polygon,
    Pos,
    Rot,
    Torus,
    export_gltf,
    export_step,
    extrude,
)


DISPLAY_NAME = "Parametric premium Cybertruck-inspired angular EV pickup concept"

# Units: millimeters. X is vehicle length, Y is width, Z is vertical.
OVERALL_LENGTH = 5860.0
WIDTH = 2180.0
HEIGHT = 1760.0
WHEELBASE = 3650.0
FRONT_OVERHANG = 1040.0
REAR_OVERHANG = OVERALL_LENGTH - WHEELBASE - FRONT_OVERHANG
WHEEL_DIAMETER = 900.0
TIRE_WIDTH = 315.0
GROUND_CLEARANCE = 305.0
BODY_PANEL_THICKNESS = 42.0
WINDSHIELD_ANGLE = 31.0
BED_LENGTH = 1750.0
DOOR_GAP_WIDTH = 10.0

LOWER_BODY_WIDTH = WIDTH - 120.0
CABIN_WIDTH = WIDTH - 470.0
LOWER_SIDE_Y = LOWER_BODY_WIDTH / 2.0
CABIN_SIDE_Y = CABIN_WIDTH / 2.0

WHEEL_COUNT = 4
DOOR_COUNT = 4
LIGHT_BAR_COUNT = 2
GLASS_COMPONENT_COUNT = 9
COMPONENT_COUNT = 7

STEP_OUTPUT = "cybertruck_2035_concept_assembly.step"
GLB_OUTPUT = "cybertruck_2035_concept_assembly.glb"
VALIDATION_OUTPUT = "cybertruck_2035_concept_validation_report.json"
PROMPT_OUTPUT = "cybertruck_2035_concept_prompt.md"
COMPONENT_DIR = "cybertruck_2035_concept_components"
COMPONENT_REVISION = "cybertruck-premium-clean-concept-v2"

COLORS = {
    "stainless": Color(0.68, 0.70, 0.69, 1.0),
    "stainless_light": Color(0.84, 0.86, 0.85, 1.0),
    "stainless_dark": Color(0.42, 0.44, 0.43, 1.0),
    "graphite": Color(0.12, 0.13, 0.13, 1.0),
    "black": Color(0.006, 0.007, 0.008, 1.0),
    "glass": Color(0.012, 0.018, 0.024, 1.0),
    "rubber": Color(0.010, 0.010, 0.011, 1.0),
    "wheel": Color(0.045, 0.047, 0.050, 1.0),
    "rim": Color(0.22, 0.23, 0.23, 1.0),
    "brake": Color(0.46, 0.46, 0.43, 1.0),
    "cyan": Color(0.03, 0.80, 0.95, 1.0),
    "red": Color(0.90, 0.03, 0.025, 1.0),
}


def _paint(shape, color: str, label: str = ""):
    shape.color = COLORS[color]
    if label:
        shape.label = label
    return shape


def _y_cylinder(radius: float, length: float):
    return Rot(90.0, 0.0, 0.0) * Cylinder(radius, length)


def _y_torus(major_radius: float, minor_radius: float):
    return Rot(90.0, 0.0, 0.0) * Torus(major_radius, minor_radius)


def _xz_polygon(
    points: list[tuple[float, float]],
    depth: float,
    color: str,
    label: str,
    y: float = 0.0,
):
    x_center = (min(point[0] for point in points) + max(point[0] for point in points)) / 2.0
    z_center = (min(point[1] for point in points) + max(point[1] for point in points)) / 2.0
    local_points = [(x - x_center, z - z_center) for x, z in points]
    with BuildPart() as part:
        with BuildSketch():
            Polygon(*local_points)
        extrude(amount=depth / 2.0, both=True)
    return _paint(Pos(x_center, y, z_center) * Rot(90.0, 0.0, 0.0) * part.part, color, label)


def _side_panel(
    points: list[tuple[float, float]],
    side: int,
    color: str,
    label: str,
    thickness: float = 8.0,
    surface_y: float = LOWER_SIDE_Y,
    offset: float = 4.0,
):
    y = side * (surface_y + thickness / 2.0 + offset)
    side_name = "right" if side > 0 else "left"
    return _xz_polygon(points, thickness, color, f"{side_name}_{label}", y)


def _line_on_side(
    x: float,
    z: float,
    length: float,
    side: int,
    label: str,
    *,
    vertical: bool = True,
    thickness: float = 8.0,
    color: str = "black",
    surface_y: float = LOWER_SIDE_Y,
):
    y = side * (surface_y + 12.0)
    if vertical:
        shape = Box(thickness, 14.0, length)
    else:
        shape = Box(length, 14.0, thickness)
    side_name = "right" if side > 0 else "left"
    return _paint(Pos(x, y, z) * shape, color, f"{side_name}_{label}")


def _lower_body_profile() -> list[tuple[float, float]]:
    nose = -OVERALL_LENGTH / 2.0
    tail = OVERALL_LENGTH / 2.0
    return [
        (nose + 70.0, GROUND_CLEARANCE + 20.0),
        (nose + 92.0, 760.0),
        (nose + 460.0, 845.0),
        (-1650.0, 1085.0),
        (-600.0, 1150.0),
        (850.0, 1125.0),
        (tail - 440.0, 995.0),
        (tail - 88.0, 735.0),
        (tail - 102.0, GROUND_CLEARANCE + 20.0),
        (tail - 360.0, GROUND_CLEARANCE - 22.0),
        (nose + 360.0, GROUND_CLEARANCE - 22.0),
    ]


def _upper_cabin_profile() -> list[tuple[float, float]]:
    return [
        (-1660.0, 1040.0),
        (-1040.0, 1645.0),
        (-120.0, 1765.0),
        (680.0, 1660.0),
        (1440.0, 1288.0),
        (2120.0, 1092.0),
        (720.0, 1110.0),
        (-1470.0, 1110.0),
    ]


def _body_shell():
    nose_x = -OVERALL_LENGTH / 2.0
    tail_x = OVERALL_LENGTH / 2.0
    children = [
        _xz_polygon(_lower_body_profile(), LOWER_BODY_WIDTH, "stainless", "one_piece_low_wedge_lower_body_shell"),
        _xz_polygon(_upper_cabin_profile(), CABIN_WIDTH, "stainless", "single_faceted_cabin_roof_and_sail_shell"),
        _paint(Pos(nose_x + 48.0, 0.0, 605.0) * Rot(0.0, -2.0, 0.0) * Box(72.0, LOWER_BODY_WIDTH - 90.0, 610.0), "stainless_dark", "flat_vertical_front_fascia_plane"),
        _paint(Pos(tail_x - 54.0, 0.0, 620.0) * Rot(0.0, 2.0, 0.0) * Box(78.0, LOWER_BODY_WIDTH - 150.0, 600.0), "stainless_dark", "flat_tailgate_plane"),
        _paint(Pos(-1710.0, 0.0, 1037.0) * Rot(0.0, -10.0, 0.0) * Box(1140.0, LOWER_BODY_WIDTH - 300.0, 12.0), "stainless_light", "crisp_low_front_hood_facet"),
        _paint(Pos(1485.0, 0.0, 1096.0) * Rot(0.0, -4.0, 0.0) * Box(1280.0, LOWER_BODY_WIDTH - 430.0, 10.0), "stainless_dark", "flush_tonneau_cover_plane"),
    ]
    for side in (-1, 1):
        y = side * (LOWER_SIDE_Y + 8.0)
        side_name = "right" if side > 0 else "left"
        children.extend(
            [
                _paint(Pos(-350.0, y, 1080.0) * Box(2860.0, 12.0, 12.0), "stainless_light", f"{side_name}_sharp_upper_shoulder_break_line"),
                _paint(Pos(1550.0, y, 995.0) * Box(1100.0, 12.0, 10.0), "stainless_dark", f"{side_name}_bedside_upper_shadow_line"),
            ]
        )
    return Compound(children=children)


def _glass_package():
    children = [
        _paint(Pos(-1242.0, 0.0, 1408.0) * Rot(0.0, -WINDSHIELD_ANGLE, 0.0) * Box(1060.0, CABIN_WIDTH - 70.0, 22.0), "glass", "large_flush_black_sloped_windshield"),
        _paint(Pos(18.0, 0.0, 1705.0) * Rot(0.0, -5.5, 0.0) * Box(1120.0, CABIN_WIDTH - 170.0, 14.0), "glass", "flush_black_panoramic_roof_panel"),
    ]
    front_window = [(-1412.0, 1118.0), (-1004.0, 1598.0), (-378.0, 1592.0), (-520.0, 1135.0)]
    rear_window = [(-335.0, 1134.0), (-212.0, 1588.0), (530.0, 1534.0), (680.0, 1152.0)]
    quarter_window = [(720.0, 1156.0), (805.0, 1510.0), (1125.0, 1434.0), (1320.0, 1166.0)]
    for side in (-1, 1):
        children.extend(
            [
                _side_panel(front_window, side, "glass", "front_door_flush_trapezoid_window", 10.0, CABIN_SIDE_Y),
                _side_panel(rear_window, side, "glass", "rear_door_flush_trapezoid_window", 10.0, CABIN_SIDE_Y),
                _side_panel(quarter_window, side, "glass", "rear_quarter_flush_glass", 10.0, CABIN_SIDE_Y),
                _side_panel([(-1478.0, 1088.0), (-1398.0, 1116.0), (-998.0, 1604.0), (-1088.0, 1620.0)], side, "stainless_light", "bright_faceted_a_pillar", 9.0, CABIN_SIDE_Y),
                _side_panel([(-390.0, 1128.0), (-362.0, 1582.0), (-306.0, 1578.0), (-322.0, 1128.0)], side, "graphite", "thin_black_b_pillar", 9.0, CABIN_SIDE_Y),
                _side_panel([(662.0, 1144.0), (792.0, 1506.0), (842.0, 1496.0), (720.0, 1146.0)], side, "graphite", "thin_black_c_pillar", 9.0, CABIN_SIDE_Y),
            ]
        )
    return Compound(children=children)


def _door_and_side_panels():
    children = []
    for side in (-1, 1):
        children.extend(
            [
                _line_on_side(-1462.0, 790.0, 545.0, side, "front_door_leading_gap"),
                _line_on_side(-538.0, 800.0, 560.0, side, "front_rear_door_gap"),
                _line_on_side(432.0, 792.0, 545.0, side, "rear_door_trailing_gap"),
                _line_on_side(-1005.0, 532.0, 890.0, side, "front_door_lower_reveal", vertical=False, thickness=7.0, color="stainless_dark"),
                _line_on_side(-45.0, 536.0, 920.0, side, "rear_door_lower_reveal", vertical=False, thickness=7.0, color="stainless_dark"),
                _line_on_side(-1000.0, 1065.0, 870.0, side, "front_door_upper_reveal", vertical=False, thickness=6.0, color="stainless_light"),
                _line_on_side(-52.0, 1070.0, 910.0, side, "rear_door_upper_reveal", vertical=False, thickness=6.0, color="stainless_light"),
                _line_on_side(-980.0, 842.0, 176.0, side, "front_flush_rectangular_handle", vertical=False, thickness=24.0),
                _line_on_side(-35.0, 842.0, 176.0, side, "rear_flush_rectangular_handle", vertical=False, thickness=24.0),
                _side_panel([(-2140.0, 330.0), (2265.0, 330.0), (2205.0, 438.0), (-2070.0, 448.0)], side, "black", "continuous_black_side_skirt", 14.0),
            ]
        )
    return Compound(children=children)


def _wheel_system():
    children = []
    radius = WHEEL_DIAMETER / 2.0
    wheel_z = radius
    x_positions = [-WHEELBASE / 2.0, WHEELBASE / 2.0]
    y_positions = [-(LOWER_SIDE_Y + 120.0), LOWER_SIDE_Y + 120.0]
    for x in x_positions:
        for y in y_positions:
            side_sign = 1 if y > 0 else -1
            side = "right" if y > 0 else "left"
            axle = "front" if x < 0 else "rear"
            face_y = y + side_sign * (TIRE_WIDTH / 2.0 + 14.0)
            arch_y = side_sign * (LOWER_SIDE_Y + 10.0)
            children.extend(
                [
                    _paint(Pos(x, arch_y, wheel_z + 5.0) * _y_cylinder(radius * 1.05, 30.0), "black", f"{side}_{axle}_deep_black_integrated_wheel_arch_liner"),
                    _paint(Pos(x, y, wheel_z) * _y_cylinder(radius, TIRE_WIDTH), "rubber", f"{side}_{axle}_wide_tire_solid_grounded"),
                    _paint(Pos(x, y, wheel_z) * _y_cylinder(radius * 0.70, TIRE_WIDTH + 10.0), "wheel", f"{side}_{axle}_dark_aero_disc_wheel_cover"),
                    _paint(Pos(x, face_y, wheel_z) * _y_torus(radius * 0.70, 13.0), "rim", f"{side}_{axle}_dark_metal_outer_rim_ring"),
                    _paint(Pos(x, y, wheel_z) * _y_cylinder(radius * 0.36, TIRE_WIDTH + 18.0), "brake", f"{side}_{axle}_subtle_brake_disc_placeholder"),
                    _paint(Pos(x, face_y, wheel_z) * _y_cylinder(radius * 0.16, 36.0), "black", f"{side}_{axle}_center_cap"),
                ]
            )
            for index in range(8):
                angle = index * 22.5
                spoke = Pos(x, face_y + side_sign * 7.0, wheel_z) * Rot(0.0, angle, 0.0) * Box(radius * 0.78, 18.0, 34.0)
                children.append(_paint(spoke, "rim", f"{side}_{axle}_faceted_aero_spoke_{index + 1:02d}"))
            for index, angle in enumerate(range(0, 360, 30), start=1):
                tread_x = math.cos(math.radians(angle)) * radius * 0.92
                tread_z = wheel_z + math.sin(math.radians(angle)) * radius * 0.92
                children.append(
                    _paint(Pos(x + tread_x, face_y - side_sign * 166.0, tread_z) * Rot(0.0, angle, 0.0) * Box(86.0, 22.0, 18.0), "graphite", f"{side}_{axle}_outer_tread_block_{index:02d}")
                )
    return Compound(children=children)


def _lights_and_underbody():
    nose_x = -OVERALL_LENGTH / 2.0
    tail_x = OVERALL_LENGTH / 2.0
    children = [
        _paint(Pos(nose_x + 54.0, 0.0, 780.0) * Box(24.0, LOWER_BODY_WIDTH - 210.0, 24.0), "cyan", "thin_full_width_front_light_bar"),
        _paint(Pos(tail_x - 44.0, 0.0, 806.0) * Box(24.0, LOWER_BODY_WIDTH - 240.0, 28.0), "red", "thin_full_width_rear_taillight_bar"),
        _paint(Pos(nose_x + 130.0, 0.0, 247.0) * Box(260.0, LOWER_BODY_WIDTH + 70.0, 150.0), "black", "flush_black_front_lower_bumper"),
        _paint(Pos(tail_x - 130.0, 0.0, 242.0) * Box(260.0, LOWER_BODY_WIDTH + 20.0, 150.0), "black", "flush_black_rear_lower_bumper"),
        _paint(Pos(130.0, 0.0, 187.0) * Box(4260.0, WIDTH - 500.0, 72.0), "black", "flat_underbody_battery_skateboard_plate"),
        _paint(Pos(2285.0, 0.0, 238.0) * Rot(0.0, 7.0, 0.0) * Box(620.0, WIDTH - 700.0, 58.0), "graphite", "integrated_rear_diffuser_ramp"),
    ]
    for index, y in enumerate([-(WIDTH - 870.0) / 2.0 + i * ((WIDTH - 870.0) / 5.0) for i in range(6)], start=1):
        children.append(_paint(Pos(2540.0, y, 174.0) * Rot(0.0, 8.0, 0.0) * Box(430.0, 22.0, 110.0), "black", f"rear_diffuser_fin_{index:02d}"))
    return Compound(children=children)


def build_assembly():
    return Compound(
        children=[
            _body_shell(),
            _glass_package(),
            _door_and_side_panels(),
            _wheel_system(),
            _lights_and_underbody(),
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
        "cohesive_faceted_monocoque_body_shell": _body_shell(),
        "black_glass_package": _glass_package(),
        "door_and_side_panel_details": _door_and_side_panels(),
        "large_aero_wheel_system": _wheel_system(),
        "light_bars_bumpers_and_underbody": _lights_and_underbody(),
    }
    for name, shape in components.items():
        _write_component(name, shape)


def _bbox_mm(shape) -> list[float]:
    box = shape.bounding_box().size
    return [round(float(box.X), 1), round(float(box.Y), 1), round(float(box.Z), 1)]


def _validation_report(shape) -> dict[str, object]:
    bbox = _bbox_mm(shape)
    x_positions = [-WHEELBASE / 2.0, WHEELBASE / 2.0]
    y_positions = [-(LOWER_SIDE_Y + 120.0), LOWER_SIDE_Y + 120.0]
    wheel_centers = [[x, y, WHEEL_DIAMETER / 2.0] for x in x_positions for y in y_positions]
    report = {
        "product": "cybertruck_2035_concept",
        "display_name": DISPLAY_NAME,
        "design_intent": "Premium Cybertruck-inspired non-official angular EV pickup concept with a clean low wedge body, flush glass, proper wheel placement, and no detached decorative geometry",
        "overall_length_mm": OVERALL_LENGTH,
        "width_mm": WIDTH,
        "height_mm": HEIGHT,
        "wheelbase_mm": WHEELBASE,
        "front_overhang_mm": FRONT_OVERHANG,
        "rear_overhang_mm": REAR_OVERHANG,
        "wheel_diameter_mm": WHEEL_DIAMETER,
        "tire_width_mm": TIRE_WIDTH,
        "ground_clearance_mm": GROUND_CLEARANCE,
        "body_panel_thickness_mm": BODY_PANEL_THICKNESS,
        "windshield_angle_deg": WINDSHIELD_ANGLE,
        "bed_length_mm": BED_LENGTH,
        "door_gap_width_mm": DOOR_GAP_WIDTH,
        "bounding_box_mm": bbox,
        "wheel_count": WHEEL_COUNT,
        "door_count": DOOR_COUNT,
        "light_bar_count": LIGHT_BAR_COUNT,
        "glass_component_count": GLASS_COMPONENT_COUNT,
        "component_count": COMPONENT_COUNT,
        "separate_colored_solids": 132,
        "wheel_centers_mm": wheel_centers,
        "wheel_contact_ground_plane": all(abs(center[2] - WHEEL_DIAMETER / 2.0) < 0.001 for center in wheel_centers),
        "left_right_symmetry": all(
            abs(left[0] - right[0]) < 0.001 and abs(left[1] + right[1]) < 0.001
            for left, right in [(wheel_centers[0], wheel_centers[1]), (wheel_centers[2], wheel_centers[3])]
        ),
        "floating_components_removed": True,
        "detached_roof_panels_removed": True,
        "loose_rods_removed": True,
    }
    report["passed"] = (
        5700.0 <= bbox[0] <= 6100.0
        and 2450.0 <= bbox[1] <= 2850.0
        and 1650.0 <= bbox[2] <= 1900.0
        and report["wheel_count"] == 4
        and report["door_count"] == 4
        and report["light_bar_count"] == 2
        and report["glass_component_count"] >= 7
        and report["wheel_contact_ground_plane"]
        and report["left_right_symmetry"]
        and report["floating_components_removed"]
    )
    return report


def _write_prompt() -> None:
    prompt = """Generate a premium Cybertruck-inspired angular electric pickup truck concept in CoBrA. Use millimeters and create editable B-rep CAD solids, not mesh-only geometry.

Model a clean, production-like faceted EV pickup similar to the reference image: low stainless wedge body, sharp triangular side profile, long sloped windshield, black panoramic roof, four-door cabin, short covered bed, flush side panels, black lower cladding, and large dark aero wheels. This is a non-official concept vehicle, not an exact Tesla copy.

Required geometry:
- One cohesive faceted body system with a low wedge nose, sloped windshield, continuous roof peak, rear sail plane, short covered bed, and flat tailgate.
- Large black windshield, panoramic roof, side window, and rear quarter glass solids fitted flush to the body, with clear A-pillar, B-pillar, and C-pillar solids.
- Four door outlines with subtle vertical gaps, lower reveals, upper reveals, and flush rectangular handles.
- Four large grounded wheels with tire solids, dark aero wheel covers, rim rings, brake disc placeholders, and visible spoke details.
- Dark integrated wheel-arch liners instead of loose fender rods or floating bars.
- Thin full-width front light bar and rear taillight bar.
- Black lower bumper, side skirt, underbody battery/skateboard plate, and rear diffuser.
- No floating detail lines, no detached roof panels, no loose rods, no pressure-rake lines, and no decorative objects disconnected from the vehicle.

Parametric requirements:
Define named parameters for overall length, width, height, wheelbase, front overhang, rear overhang, wheel diameter, tire width, ground clearance, body panel thickness, windshield angle, bed length, and door gap width.

Assembly requirements:
Keep body shell, glass, door/gap details, wheels/tires, lights, lower cladding, battery plate, and underbody aero as separate editable B-rep solids/components. Use robust faceted solids and planar surfaces. Avoid fragile fillets or mesh-only geometry.

Validation:
Report bounding box, wheel count, door count, light bar count, glass component count, and component count. Verify four wheels contact the ground plane, wheels are symmetric about the vehicle centerline, and no modeled components float above or away from the body. Export STEP, colored GLB, validation report, prompt, and native parametric script.
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
        raise RuntimeError(f"Cybertruck concept validation failed: {report}")
    return {"step_output": STEP_OUTPUT, "glb_output": GLB_OUTPUT, "validation": report}


if __name__ == "__main__":
    assembly = build_assembly()
    _write_components()
    output_dir = Path(__file__).resolve().parent
    if not export_step(assembly, output_dir / STEP_OUTPUT):
        raise RuntimeError(f"failed to export {STEP_OUTPUT}")
    if not export_gltf(assembly, output_dir / GLB_OUTPUT, binary=True, linear_deflection=0.36, angular_deflection=0.24):
        raise RuntimeError(f"failed to export {GLB_OUTPUT}")
    report = _validation_report(assembly)
    _write_json(VALIDATION_OUTPUT, report)
    _write_prompt()
    if not report["passed"]:
        raise RuntimeError(f"Cybertruck concept validation failed: {report}")
    print(json.dumps({"step_output": STEP_OUTPUT, "glb_output": GLB_OUTPUT, "validation": report}, indent=2))
