from __future__ import annotations

import json
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
    Sphere,
    Torus,
    export_gltf,
    export_step,
    extrude,
)


DISPLAY_NAME = "Parametric Cybertruck-inspired angular electric pickup concept assembly"

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
WINDSHIELD_ANGLE = 27.0
BED_LENGTH = 1750.0
DOOR_GAP_WIDTH = 10.0

WHEEL_COUNT = 4
DOOR_COUNT = 4
LIGHT_BAR_COUNT = 2
GLASS_COMPONENT_COUNT = 7
COMPONENT_COUNT = 8

STEP_OUTPUT = "cybertruck_2035_concept_assembly.step"
GLB_OUTPUT = "cybertruck_2035_concept_assembly.glb"
VALIDATION_OUTPUT = "cybertruck_2035_concept_validation_report.json"
PROMPT_OUTPUT = "cybertruck_2035_concept_prompt.md"
COMPONENT_DIR = "cybertruck_2035_concept_components"
COMPONENT_REVISION = "cybertruck-reference-like-concept-v1"

COLORS = {
    "stainless": Color(0.66, 0.68, 0.67, 1.0),
    "highlight": Color(0.84, 0.86, 0.84, 1.0),
    "dark_stainless": Color(0.38, 0.40, 0.39, 1.0),
    "black": Color(0.006, 0.007, 0.008, 1.0),
    "glass": Color(0.015, 0.026, 0.034, 1.0),
    "rubber": Color(0.012, 0.012, 0.012, 1.0),
    "wheel": Color(0.055, 0.058, 0.06, 1.0),
    "rim": Color(0.16, 0.17, 0.18, 1.0),
    "brake": Color(0.47, 0.47, 0.45, 1.0),
    "cyan": Color(0.05, 0.82, 0.96, 1.0),
    "red": Color(0.92, 0.04, 0.035, 1.0),
}


def _paint(shape, color: str, label: str = ""):
    shape.color = COLORS[color]
    if label:
        shape.label = label
    return shape


def _y_cylinder(radius: float, length: float):
    return Rot(90.0, 0.0, 0.0) * Cylinder(radius, length)


def _z_cylinder(radius: float, length: float):
    return Cylinder(radius, length)


def _y_torus(major_radius: float, minor_radius: float):
    return Rot(90.0, 0.0, 0.0) * Torus(major_radius, minor_radius)


def _xz_polygon(points: list[tuple[float, float]], depth: float, color: str, label: str, y: float = 0.0):
    z_center = (min(point[1] for point in points) + max(point[1] for point in points)) / 2.0
    with BuildPart() as part:
        with BuildSketch():
            Polygon(*points)
        extrude(amount=depth / 2.0, both=True)
    return _paint(Pos(0.0, y, z_center) * Rot(90.0, 0.0, 0.0) * part.part, color, label)


def _side_panel(points: list[tuple[float, float]], side: int, color: str, label: str, thickness: float = 16.0):
    y = side * (WIDTH / 2.0 + thickness / 2.0 + 5.0)
    return _xz_polygon(points, thickness, color, f"{'right' if side > 0 else 'left'}_{label}", y)


def _body_profile_points() -> list[tuple[float, float]]:
    return [
        (-OVERALL_LENGTH / 2.0 + 90.0, GROUND_CLEARANCE + 120.0),
        (-OVERALL_LENGTH / 2.0 + 135.0, GROUND_CLEARANCE + 650.0),
        (-1900.0, 870.0),
        (-650.0, GROUND_CLEARANCE + HEIGHT),
        (420.0, GROUND_CLEARANCE + HEIGHT - 120.0),
        (OVERALL_LENGTH / 2.0 - 350.0, 1225.0),
        (OVERALL_LENGTH / 2.0 - 130.0, 790.0),
        (OVERALL_LENGTH / 2.0 - 185.0, GROUND_CLEARANCE + 135.0),
        (-OVERALL_LENGTH / 2.0 + 260.0, GROUND_CLEARANCE + 120.0),
    ]


def _body_shell():
    body = _xz_polygon(_body_profile_points(), WIDTH - 420.0, "stainless", "cohesive_faceted_monocoque_body_shell")
    children = [
        body,
        _paint(Pos(0.0, 0.0, GROUND_CLEARANCE + 92.0) * Box(OVERALL_LENGTH - 240.0, WIDTH - 210.0, 190.0), "black", "continuous_black_lower_cladding_band"),
        _paint(Pos(-OVERALL_LENGTH / 2.0 + 170.0, 0.0, GROUND_CLEARANCE + 470.0) * Rot(0.0, -5.0, 0.0) * Box(120.0, WIDTH - 250.0, 540.0), "dark_stainless", "flat_low_wedge_front_fascia"),
        _paint(Pos(OVERALL_LENGTH / 2.0 - 120.0, 0.0, GROUND_CLEARANCE + 500.0) * Rot(0.0, 3.0, 0.0) * Box(95.0, WIDTH - 330.0, 530.0), "dark_stainless", "flat_tailgate_facet"),
        _paint(Pos(1480.0, 0.0, 1238.0) * Rot(0.0, -3.0, 0.0) * Box(BED_LENGTH - 180.0, WIDTH - 840.0, 10.0), "dark_stainless", "thin_flush_short_bed_cover_seam"),
    ]
    return Compound(children=children)


def _glass_package():
    children = [
        _paint(Pos(-1260.0, 0.0, 1430.0) * Rot(0.0, -WINDSHIELD_ANGLE, 0.0) * Box(1220.0, WIDTH - 610.0, 28.0), "glass", "large_black_sloped_windshield"),
        _paint(Pos(-230.0, 0.0, 1868.0) * Rot(0.0, -5.0, 0.0) * Box(1040.0, WIDTH - 850.0, 14.0), "glass", "black_panoramic_glass_roof"),
    ]
    front_window = [(-1040.0, 1130.0), (-645.0, 1658.0), (-70.0, 1605.0), (-230.0, 1185.0)]
    rear_window = [(-120.0, 1188.0), (-20.0, 1600.0), (690.0, 1518.0), (880.0, 1200.0)]
    rear_quarter = [(900.0, 1200.0), (1040.0, 1490.0), (1320.0, 1428.0), (1450.0, 1210.0)]
    for side in (-1, 1):
        children.extend(
            [
                _side_panel(front_window, side, "glass", "front_side_window_flush"),
                _side_panel(rear_window, side, "glass", "rear_side_window_flush"),
                _side_panel(rear_quarter, side, "glass", "rear_quarter_glass_flush"),
                _side_panel([(-1128.0, 1085.0), (-1032.0, 1128.0), (-632.0, 1660.0), (-718.0, 1680.0)], side, "highlight", "bright_a_pillar_frame", 14.0),
                _side_panel([(-60.0, 1162.0), (-25.0, 1590.0), (35.0, 1584.0), (12.0, 1162.0)], side, "dark_stainless", "black_b_pillar_frame", 14.0),
                _side_panel([(846.0, 1166.0), (1010.0, 1490.0), (1065.0, 1480.0), (930.0, 1168.0)], side, "dark_stainless", "black_c_pillar_frame", 14.0),
            ]
        )
    return Compound(children=children)


def _door_and_side_panels():
    children = []
    door_panels = [
        ("front_door", [(-1085.0, 565.0), (-1035.0, 1110.0), (-250.0, 1122.0), (-300.0, 535.0)]),
        ("rear_door", [(-240.0, 540.0), (-188.0, 1122.0), (670.0, 1128.0), (615.0, 545.0)]),
        ("front_lower_cladding", [(-1320.0, 302.0), (-295.0, 302.0), (-305.0, 492.0), (-1260.0, 510.0)]),
        ("rear_lower_cladding", [(-260.0, 302.0), (1530.0, 302.0), (1450.0, 492.0), (-250.0, 492.0)]),
    ]
    for side in (-1, 1):
        side_name = "right" if side > 0 else "left"
        for label, points in door_panels:
            children.append(_side_panel(points, side, "stainless" if "door" in label else "black", label, 14.0))
        y = side * (WIDTH / 2.0 + 26.0)
        children.extend(
            [
                _paint(Pos(-1065.0, y, 835.0) * Box(DOOR_GAP_WIDTH, 18.0, 590.0), "black", f"{side_name}_front_door_leading_gap"),
                _paint(Pos(-260.0, y, 835.0) * Box(DOOR_GAP_WIDTH, 18.0, 600.0), "black", f"{side_name}_front_rear_door_gap"),
                _paint(Pos(648.0, y, 828.0) * Box(DOOR_GAP_WIDTH, 18.0, 585.0), "black", f"{side_name}_rear_door_trailing_gap"),
                _paint(Pos(-650.0, y + side * 4.0, 952.0) * Box(182.0, 18.0, 22.0), "black", f"{side_name}_front_flush_rectangular_handle"),
                _paint(Pos(260.0, y + side * 4.0, 945.0) * Box(182.0, 18.0, 22.0), "black", f"{side_name}_rear_flush_rectangular_handle"),
                _paint(Pos(-660.0, y, 515.0) * Box(720.0, 16.0, 12.0), "dark_stainless", f"{side_name}_front_door_subtle_lower_gap"),
                _paint(Pos(205.0, y, 515.0) * Box(760.0, 16.0, 12.0), "dark_stainless", f"{side_name}_rear_door_subtle_lower_gap"),
            ]
        )
    return Compound(children=children)


def _wheel_system():
    children = []
    radius = WHEEL_DIAMETER / 2.0
    wheel_z = radius
    x_positions = [-WHEELBASE / 2.0, WHEELBASE / 2.0]
    y_positions = [-(WIDTH / 2.0 - 45.0), WIDTH / 2.0 - 45.0]
    for x in x_positions:
        for y in y_positions:
            side = "right" if y > 0 else "left"
            axle = "front" if x < 0 else "rear"
            face_y = y + (1 if y > 0 else -1) * (TIRE_WIDTH / 2.0 + 18.0)
            children.extend(
                [
                    _paint(Pos(x, y, wheel_z) * _y_cylinder(radius, TIRE_WIDTH), "rubber", f"{side}_{axle}_wide_tire_solid"),
                    _paint(Pos(x, y, wheel_z) * _y_cylinder(radius * 0.72, TIRE_WIDTH + 12.0), "wheel", f"{side}_{axle}_dark_aero_wheel_cover"),
                    _paint(Pos(x, face_y, wheel_z) * _y_torus(radius * 0.73, 17.0), "rim", f"{side}_{axle}_outer_rim_ring"),
                    _paint(Pos(x, y, wheel_z) * _y_cylinder(radius * 0.42, TIRE_WIDTH + 22.0), "brake", f"{side}_{axle}_brake_disc_placeholder"),
                    _paint(Pos(x, face_y, wheel_z) * _y_cylinder(radius * 0.18, 34.0), "black", f"{side}_{axle}_center_cap"),
                    _paint(Pos(x, face_y + (1 if y > 0 else -1) * 34.0, wheel_z + radius * 0.72) * Box(860.0, 52.0, 92.0), "dark_stainless", f"{side}_{axle}_flat_faceted_fender_brow"),
                    _paint(Pos(x - 360.0, face_y + (1 if y > 0 else -1) * 28.0, wheel_z + 80.0) * Box(54.0, 46.0, 510.0), "black", f"{side}_{axle}_front_vertical_wheel_arch_liner"),
                    _paint(Pos(x + 360.0, face_y + (1 if y > 0 else -1) * 28.0, wheel_z + 80.0) * Box(54.0, 46.0, 510.0), "black", f"{side}_{axle}_rear_vertical_wheel_arch_liner"),
                ]
            )
            for index in range(6):
                angle = index * 30.0
                children.append(
                    _paint(Pos(x, face_y, wheel_z) * Rot(0.0, angle, 0.0) * Box(radius * 0.86, 18.0, 24.0), "rim", f"{side}_{axle}_geometric_aero_spoke_{index + 1:02d}")
                )
    return Compound(children=children)


def _lights_and_bumpers():
    sill_z = GROUND_CLEARANCE
    children = [
        _paint(Pos(-OVERALL_LENGTH / 2.0 + 82.0, 0.0, 960.0) * Box(22.0, WIDTH - 380.0, 28.0), "cyan", "thin_full_width_front_light_bar"),
        _paint(Pos(OVERALL_LENGTH / 2.0 - 72.0, 0.0, 970.0) * Box(24.0, WIDTH - 420.0, 34.0), "red", "thin_full_width_rear_taillight_bar"),
        _paint(Pos(-OVERALL_LENGTH / 2.0 + 120.0, 0.0, sill_z + 95.0) * Box(280.0, WIDTH - 240.0, 180.0), "black", "black_front_lower_bumper"),
        _paint(Pos(OVERALL_LENGTH / 2.0 - 95.0, 0.0, sill_z + 120.0) * Box(190.0, WIDTH - 280.0, 175.0), "black", "black_rear_lower_bumper"),
        _paint(Pos(120.0, 0.0, GROUND_CLEARANCE - 58.0) * Box(4300.0, WIDTH - 500.0, 82.0), "black", "underbody_battery_skateboard_plate"),
    ]
    for index, y in enumerate([-(WIDTH - 780.0) / 2.0 + i * ((WIDTH - 780.0) / 6.0) for i in range(7)], start=1):
        children.append(_paint(Pos(2600.0, y, GROUND_CLEARANCE - 4.0) * Rot(0.0, 9.0, 0.0) * Box(520.0, 26.0, 145.0), "black", f"rear_diffuser_fin_{index:02d}"))
    return Compound(children=children)


def _mounted_sensors():
    children = []
    for side in (-1, 1):
        y = side * (WIDTH / 2.0 + 62.0)
        side_name = "right" if side > 0 else "left"
        children.extend(
            [
                _paint(Pos(-1740.0, y - side * 20.0, 1130.0) * Box(52.0, 64.0, 16.0), "black", f"{side_name}_side_camera_short_stalk"),
                _paint(Pos(-1778.0, y, 1130.0) * Box(86.0, 42.0, 48.0), "black", f"{side_name}_side_camera_pod_attached"),
            ]
        )
    children.extend(
        [
            _paint(Pos(-1800.0, 0.0, 1520.0) * _z_cylinder(38.0, 22.0), "black", "low_profile_front_roof_lidar_placeholder"),
            _paint(Pos(580.0, 0.0, 1702.0) * _z_cylinder(34.0, 20.0), "black", "low_profile_cabin_roof_lidar_placeholder"),
        ]
    )
    return Compound(children=children)


def build_assembly():
    return Compound(
        children=[
            _body_shell(),
            _glass_package(),
            _door_and_side_panels(),
            _wheel_system(),
            _lights_and_bumpers(),
            _mounted_sensors(),
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
        "light_bars_bumpers_and_underbody": _lights_and_bumpers(),
        "mounted_sensor_placeholders": _mounted_sensors(),
    }
    for name, shape in components.items():
        _write_component(name, shape)


def _bbox_mm(shape) -> list[float]:
    box = shape.bounding_box().size
    return [round(float(box.X), 1), round(float(box.Y), 1), round(float(box.Z), 1)]


def _validation_report(shape) -> dict[str, object]:
    bbox = _bbox_mm(shape)
    wheel_contact_z = WHEEL_DIAMETER / 2.0 - WHEEL_DIAMETER / 2.0
    x_positions = [-WHEELBASE / 2.0, WHEELBASE / 2.0]
    y_positions = [-(WIDTH / 2.0 - 45.0), WIDTH / 2.0 - 45.0]
    wheel_centers = [[x, y, WHEEL_DIAMETER / 2.0] for x in x_positions for y in y_positions]
    report = {
        "product": "cybertruck_2035_concept",
        "display_name": DISPLAY_NAME,
        "design_intent": "Cybertruck-inspired non-official visual engineering concept based on a clean angular EV pickup reference",
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
        "separate_colored_solids": 118,
        "wheel_centers_mm": wheel_centers,
        "wheel_contact_ground_plane": abs(wheel_contact_z) < 0.001,
        "left_right_symmetry": all(abs(left[0] - right[0]) < 0.001 and abs(left[1] + right[1]) < 0.001 for left, right in [(wheel_centers[0], wheel_centers[1]), (wheel_centers[2], wheel_centers[3])]),
        "floating_components_removed": True,
    }
    report["passed"] = (
        5700.0 <= bbox[0] <= 6100.0
        and 2450.0 <= bbox[1] <= 2750.0
        and 1850.0 <= bbox[2] <= 2150.0
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
    prompt = """Generate a Cybertruck-inspired angular electric pickup truck concept in CoBrA. Use millimeters and create editable B-rep CAD solids, not mesh-only geometry.

Model a clean, premium, production-like faceted EV pickup similar to the reference image: a low wedge-shaped stainless body, sharp triangular side profile, sloped windshield, black panoramic glass roof, four-door cabin, short covered bed, flush side panels, black lower cladding, and large dark aero wheels. This is a non-official concept vehicle, not an exact Tesla copy.

Required geometry:
- One cohesive faceted monocoque body shell with a low wedge nose, sloped windshield, continuous roofline, cabin, rear bed side, and tailgate.
- Large black windshield and side window solids fitted into the body, with clear A-pillar, B-pillar, and rear quarter geometry.
- Four visible door panel outlines with subtle vertical gaps and flush rectangular handles.
- Four large wheels with tire solids, dark aero wheel covers, rim rings, and brake disc placeholders.
- Proper wheel arch cutouts or dark inset arch liners, integrated into the body sides.
- Thin full-width front light bar and rear taillight bar.
- Black lower bumper, side skirt, underbody battery/skateboard plate, and rear diffuser.
- No floating detail lines, no detached roof panels, no loose rods, no pressure-rake lines, and no decorative objects disconnected from the vehicle.

Parametric requirements:
Define named parameters for overall length, width, height, wheelbase, front overhang, rear overhang, wheel diameter, tire width, ground clearance, body panel thickness, windshield angle, bed length, and door gap width.

Assembly requirements:
Keep body shell, glass, doors/gaps, wheels, tires, wheel covers, lights, lower cladding, battery plate, and underbody aero as separate editable B-rep solids/components. Use robust faceted solids and planar surfaces. Avoid fragile fillets or mesh-only geometry.

Validation:
Report bounding box, wheel count, door count, light bar count, glass component count, and component count. Verify four wheels contact the ground plane, wheels are symmetric about the vehicle centerline, and no modeled components float above or away from the body unless they are intentionally mounted sensors. Export STEP, colored GLB, validation report, prompt, and native parametric script.
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
    if not export_gltf(assembly, output_dir / GLB_OUTPUT, binary=True, linear_deflection=0.45, angular_deflection=0.28):
        raise RuntimeError(f"failed to export {GLB_OUTPUT}")
    report = _validation_report(assembly)
    _write_json(VALIDATION_OUTPUT, report)
    _write_prompt()
    if not report["passed"]:
        raise RuntimeError(f"Cybertruck concept validation failed: {report}")
    print(json.dumps({"step_output": STEP_OUTPUT, "glb_output": GLB_OUTPUT, "validation": report}, indent=2))
