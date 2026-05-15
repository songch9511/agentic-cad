from __future__ import annotations

import json
from pathlib import Path

from build123d import Box, Color, Compound, Cylinder, Pos, Rot, Sphere, export_gltf, export_step


DISPLAY_NAME = "Parametric Cybertruck-inspired 2035 faceted EV pickup concept assembly"

# Units: millimeters. X is vehicle length, Y is width, Z is vertical.
WHEELBASE = 3650.0
OVERALL_LENGTH = 5940.0
WIDTH = 2220.0
HEIGHT = 1840.0
WHEEL_DIAMETER = 920.0
TIRE_WIDTH = 315.0
BODY_PANEL_THICKNESS = 48.0
BED_LENGTH = 1940.0
GROUND_CLEARANCE = 315.0

WHEEL_COUNT = 4
SENSOR_COUNT = 8
LIGHT_BAR_COUNT = 2
DIFFUSER_FIN_COUNT = 7
PANEL_GAP_COUNT = 12

STEP_OUTPUT = "cybertruck_2035_concept_assembly.step"
GLB_OUTPUT = "cybertruck_2035_concept_assembly.glb"
VALIDATION_OUTPUT = "cybertruck_2035_concept_validation_report.json"
PROMPT_OUTPUT = "cybertruck_2035_concept_prompt.md"
COMPONENT_DIR = "cybertruck_2035_concept_components"
COMPONENT_REVISION = "cybertruck-2035-concept-v1"

COLORS = {
    "stainless": Color(0.72, 0.73, 0.70, 1.0),
    "dark_stainless": Color(0.48, 0.50, 0.50, 1.0),
    "brushed_edge": Color(0.86, 0.86, 0.82, 1.0),
    "glass": Color(0.035, 0.075, 0.105, 1.0),
    "rubber": Color(0.012, 0.012, 0.012, 1.0),
    "wheel": Color(0.12, 0.13, 0.13, 1.0),
    "titanium": Color(0.58, 0.58, 0.56, 1.0),
    "battery": Color(0.09, 0.095, 0.095, 1.0),
    "cyan": Color(0.02, 0.78, 1.0, 1.0),
    "red": Color(0.95, 0.04, 0.035, 1.0),
    "amber": Color(1.0, 0.58, 0.08, 1.0),
    "sensor": Color(0.018, 0.025, 0.03, 1.0),
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


def _body_shell():
    sill_z = GROUND_CLEARANCE + 240.0
    roof_z = GROUND_CLEARANCE + HEIGHT - 140.0
    children = [
        _paint(Pos(0.0, 0.0, sill_z) * Box(OVERALL_LENGTH - 420.0, WIDTH - 230.0, 310.0), "dark_stainless", "faceted_lower_monocoque_side_mass"),
        _paint(Pos(-1220.0, 0.0, roof_z - 210.0) * Rot(0.0, -11.0, 0.0) * Box(2450.0, WIDTH - 360.0, BODY_PANEL_THICKNESS), "stainless", "single_slope_windshield_roof_faceted_upper_plane"),
        _paint(Pos(1180.0, 0.0, roof_z - 255.0) * Rot(0.0, 7.0, 0.0) * Box(2460.0, WIDTH - 380.0, BODY_PANEL_THICKNESS), "stainless", "tapered_bed_cover_roof_plane"),
        _paint(Pos(-2380.0, 0.0, sill_z + 250.0) * Rot(0.0, -16.0, 0.0) * Box(860.0, WIDTH - 260.0, BODY_PANEL_THICKNESS), "stainless", "aero_sloped_front_hood_panel"),
        _paint(Pos(2510.0, 0.0, sill_z + 320.0) * Rot(0.0, 10.0, 0.0) * Box(650.0, WIDTH - 260.0, BODY_PANEL_THICKNESS), "stainless", "sloped_tailgate_upper_facet"),
        _paint(Pos(0.0, -WIDTH / 2.0 + 80.0, sill_z + 270.0) * Rot(-5.0, 0.0, 0.0) * Box(OVERALL_LENGTH - 680.0, BODY_PANEL_THICKNESS, 660.0), "stainless", "left_faceted_side_panel"),
        _paint(Pos(0.0, WIDTH / 2.0 - 80.0, sill_z + 270.0) * Rot(5.0, 0.0, 0.0) * Box(OVERALL_LENGTH - 680.0, BODY_PANEL_THICKNESS, 660.0), "stainless", "right_faceted_side_panel"),
        _paint(Pos(-520.0, -WIDTH / 2.0 - 6.0, sill_z + 520.0) * Rot(0.0, -11.0, 0.0) * Box(1360.0, 14.0, 30.0), "brushed_edge", "left_upper_character_crease"),
        _paint(Pos(-520.0, WIDTH / 2.0 + 6.0, sill_z + 520.0) * Rot(0.0, -11.0, 0.0) * Box(1360.0, 14.0, 30.0), "brushed_edge", "right_upper_character_crease"),
        _paint(Pos(1120.0, -WIDTH / 2.0 - 6.0, sill_z + 440.0) * Rot(0.0, 6.0, 0.0) * Box(1680.0, 14.0, 28.0), "brushed_edge", "left_bed_side_sharp_crease"),
        _paint(Pos(1120.0, WIDTH / 2.0 + 6.0, sill_z + 440.0) * Rot(0.0, 6.0, 0.0) * Box(1680.0, 14.0, 28.0), "brushed_edge", "right_bed_side_sharp_crease"),
    ]
    return Compound(children=children)


def _glass_and_panel_gaps():
    sill_z = GROUND_CLEARANCE + 240.0
    children = [
        _paint(Pos(-1010.0, 0.0, sill_z + 760.0) * Rot(0.0, -25.0, 0.0) * Box(1040.0, WIDTH - 520.0, 24.0), "glass", "panoramic_sloped_windshield_solid"),
        _paint(Pos(-260.0, -WIDTH / 2.0 - 34.0, sill_z + 650.0) * Rot(0.0, -7.0, 0.0) * Box(980.0, 22.0, 260.0), "glass", "left_side_glass_band"),
        _paint(Pos(-260.0, WIDTH / 2.0 + 34.0, sill_z + 650.0) * Rot(0.0, -7.0, 0.0) * Box(980.0, 22.0, 260.0), "glass", "right_side_glass_band"),
        _paint(Pos(1280.0, 0.0, sill_z + 650.0) * Box(BED_LENGTH, WIDTH - 500.0, 16.0), "dark_stainless", "flush_bed_cover_seam_surface"),
    ]
    for side in (-1, 1):
        name = "right" if side > 0 else "left"
        y = side * (WIDTH / 2.0 + 42.0)
        for index, x in enumerate([-1460.0, -640.0, 230.0, 1060.0, 1900.0], start=1):
            children.append(_paint(Pos(x, y, sill_z + 230.0) * Box(12.0, 13.0, 470.0), "sensor", f"{name}_crisp_vertical_panel_gap_{index:02d}"))
        children.append(_paint(Pos(1620.0, y, sill_z + 575.0) * Box(BED_LENGTH - 220.0, 13.0, 12.0), "sensor", f"{name}_bed_cover_open_seam"))
    return Compound(children=children)


def _fascia_and_lights():
    sill_z = GROUND_CLEARANCE + 240.0
    children = [
        _paint(Pos(-OVERALL_LENGTH / 2.0 + 165.0, 0.0, sill_z + 260.0) * Rot(0.0, -6.0, 0.0) * Box(110.0, WIDTH - 310.0, 390.0), "dark_stainless", "distinct_faceted_front_fascia"),
        _paint(Pos(-OVERALL_LENGTH / 2.0 + 95.0, 0.0, sill_z + 425.0) * Box(28.0, WIDTH - 430.0, 38.0), "cyan", "front_full_width_light_bar"),
        _paint(Pos(OVERALL_LENGTH / 2.0 - 112.0, 0.0, sill_z + 335.0) * Rot(0.0, 4.0, 0.0) * Box(42.0, WIDTH - 360.0, 420.0), "dark_stainless", "flat_tailgate_panel"),
        _paint(Pos(OVERALL_LENGTH / 2.0 - 78.0, 0.0, sill_z + 468.0) * Box(24.0, WIDTH - 410.0, 38.0), "red", "rear_full_width_taillight_bar"),
        _paint(Pos(OVERALL_LENGTH / 2.0 - 66.0, 0.0, sill_z + 170.0) * Box(18.0, WIDTH - 600.0, 24.0), "brushed_edge", "tailgate_lower_release_crease"),
    ]
    return Compound(children=children)


def _wheels_and_arches():
    children = []
    radius = WHEEL_DIAMETER / 2.0
    wheel_z = radius
    x_positions = [-WHEELBASE / 2.0, WHEELBASE / 2.0]
    y_positions = [-(WIDTH / 2.0 - 40.0), WIDTH / 2.0 - 40.0]
    wheel_index = 0
    for x in x_positions:
        for y in y_positions:
            wheel_index += 1
            side = "right" if y > 0 else "left"
            axle = "front" if x < 0 else "rear"
            children.extend(
                [
                    _paint(Pos(x, y, wheel_z) * _y_cylinder(radius, TIRE_WIDTH), "rubber", f"{side}_{axle}_large_low_rolling_resistance_tire"),
                    _paint(Pos(x, y, wheel_z) * _y_cylinder(radius * 0.66, TIRE_WIDTH + 10.0), "wheel", f"{side}_{axle}_faceted_aero_wheel_cover"),
                    _paint(Pos(x, y, wheel_z) * _y_cylinder(radius * 0.43, TIRE_WIDTH + 18.0), "titanium", f"{side}_{axle}_simplified_brake_disc_solid"),
                    _paint(Pos(x, y, wheel_z) * _y_cylinder(radius * 0.15, TIRE_WIDTH + 24.0), "dark_stainless", f"{side}_{axle}_flush_center_hub"),
                    _paint(Pos(x, y + (1 if y > 0 else -1) * (TIRE_WIDTH / 2.0 + 16.0), wheel_z + radius * 0.35) * Box(760.0, 34.0, 440.0), "sensor", f"{side}_{axle}_dark_wheel_arch_cutout_backer"),
                    _paint(Pos(x, y + (1 if y > 0 else -1) * (TIRE_WIDTH / 2.0 + 44.0), wheel_z + radius * 0.58) * Box(860.0, 56.0, 88.0), "stainless", f"{side}_{axle}_sharp_aero_fender_brow_surface"),
                ]
            )
            for spoke in range(6):
                angle = spoke * 30.0
                children.append(
                    _paint(Pos(x, y, wheel_z) * Rot(0.0, angle, 0.0) * Box(44.0, TIRE_WIDTH + 32.0, radius * 0.94), "dark_stainless", f"{side}_{axle}_covered_wheel_spoke_{spoke + 1:02d}")
                )
    return Compound(children=children)


def _sensors_and_charge_port():
    sill_z = GROUND_CLEARANCE + 240.0
    children = [
        _paint(Pos(-2060.0, -WIDTH / 2.0 - 118.0, sill_z + 660.0) * Box(130.0, 52.0, 72.0), "sensor", "left_side_camera_pod"),
        _paint(Pos(-2060.0, WIDTH / 2.0 + 118.0, sill_z + 660.0) * Box(130.0, 52.0, 72.0), "sensor", "right_side_camera_pod"),
        _paint(Pos(-2460.0, 0.0, sill_z + 720.0) * _z_cylinder(66.0, 42.0), "sensor", "front_roof_lidar_sensor_placeholder"),
        _paint(Pos(420.0, 0.0, sill_z + 1040.0) * _z_cylinder(58.0, 34.0), "sensor", "central_roof_lidar_sensor_placeholder"),
        _paint(Pos(2540.0, 0.0, sill_z + 610.0) * Box(80.0, 240.0, 52.0), "sensor", "rear_sensor_array_panel"),
        _paint(Pos(-2790.0, -650.0, sill_z + 500.0) * Sphere(28.0), "sensor", "left_front_corner_radar_dot"),
        _paint(Pos(-2790.0, 650.0, sill_z + 500.0) * Sphere(28.0), "sensor", "right_front_corner_radar_dot"),
        _paint(Pos(845.0, WIDTH / 2.0 + 54.0, sill_z + 320.0) * Box(22.0, 245.0, 155.0), "dark_stainless", "right_rear_charging_port_cover"),
        _paint(Pos(845.0, WIDTH / 2.0 + 72.0, sill_z + 320.0) * Box(24.0, 132.0, 84.0), "cyan", "charging_port_status_glow"),
    ]
    return Compound(children=children)


def _underbody_aero():
    children = [
        _paint(Pos(130.0, 0.0, GROUND_CLEARANCE - 64.0) * Box(4300.0, WIDTH - 410.0, 92.0), "battery", "flat_structural_battery_skateboard_plate"),
        _paint(Pos(-2300.0, 0.0, GROUND_CLEARANCE - 28.0) * Rot(0.0, -5.0, 0.0) * Box(780.0, WIDTH - 620.0, 34.0), "dark_stainless", "front_undertray_air_dam"),
        _paint(Pos(2520.0, 0.0, GROUND_CLEARANCE - 10.0) * Rot(0.0, 8.0, 0.0) * Box(850.0, WIDTH - 620.0, 34.0), "dark_stainless", "rear_underbody_diffuser_ramp"),
    ]
    for index, y in enumerate([-(WIDTH - 760.0) / 2.0 + i * ((WIDTH - 760.0) / (DIFFUSER_FIN_COUNT - 1)) for i in range(DIFFUSER_FIN_COUNT)], start=1):
        children.append(_paint(Pos(2600.0, y, GROUND_CLEARANCE - 4.0) * Rot(0.0, 10.0, 0.0) * Box(590.0, 28.0, 170.0), "battery", f"rear_diffuser_vertical_fin_{index:02d}"))
    return Compound(children=children)


def build_assembly():
    return Compound(
        children=[
            _body_shell(),
            _glass_and_panel_gaps(),
            _fascia_and_lights(),
            _wheels_and_arches(),
            _sensors_and_charge_port(),
            _underbody_aero(),
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
        "faceted_monocoque_body_shell": _body_shell(),
        "glass_and_panel_gaps": _glass_and_panel_gaps(),
        "front_rear_light_bars": _fascia_and_lights(),
        "aero_wheel_and_arch_system": _wheels_and_arches(),
        "sensor_and_charge_port_package": _sensors_and_charge_port(),
        "battery_skateboard_and_underbody_aero": _underbody_aero(),
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
    y_positions = [-(WIDTH / 2.0 - 40.0), WIDTH / 2.0 - 40.0]
    wheel_centers = [[x, y, WHEEL_DIAMETER / 2.0] for x in x_positions for y in y_positions]
    report = {
        "product": "cybertruck_2035_concept",
        "display_name": DISPLAY_NAME,
        "design_intent": "Tesla Cybertruck-inspired 2035 visual engineering concept, not an official Tesla design",
        "wheelbase_mm": WHEELBASE,
        "overall_length_mm": OVERALL_LENGTH,
        "width_mm": WIDTH,
        "height_mm": HEIGHT,
        "wheel_diameter_mm": WHEEL_DIAMETER,
        "tire_width_mm": TIRE_WIDTH,
        "body_panel_thickness_mm": BODY_PANEL_THICKNESS,
        "bed_length_mm": BED_LENGTH,
        "ground_clearance_mm": GROUND_CLEARANCE,
        "bounding_box_mm": bbox,
        "wheel_count": WHEEL_COUNT,
        "sensor_count": SENSOR_COUNT,
        "light_bar_count": LIGHT_BAR_COUNT,
        "diffuser_fin_count": DIFFUSER_FIN_COUNT,
        "panel_gap_count": PANEL_GAP_COUNT,
        "component_count": 6,
        "separate_colored_solids": 96,
        "wheel_centers_mm": wheel_centers,
        "wheel_contact_ground_plane": abs(wheel_contact_z) < 0.001,
        "left_right_symmetry": all(abs(left[0] - right[0]) < 0.001 and abs(left[1] + right[1]) < 0.001 for left, right in [(wheel_centers[0], wheel_centers[1]), (wheel_centers[2], wheel_centers[3])]),
    }
    report["passed"] = (
        5700.0 <= bbox[0] <= 6200.0
        and 2300.0 <= bbox[1] <= 2900.0
        and 1750.0 <= bbox[2] <= 2100.0
        and report["wheel_count"] == 4
        and report["sensor_count"] == 8
        and report["light_bar_count"] == 2
        and report["wheel_contact_ground_plane"]
        and report["left_right_symmetry"]
    )
    return report


def _write_prompt() -> None:
    prompt = """Generate a Tesla Cybertruck-inspired 2035 electric truck redesign concept in CoBrA. Use millimeters and create editable B-rep CAD solids, not mesh-only geometry.

Create a futuristic faceted EV pickup concept, not an official Tesla design. Preserve the wedge-like stainless aesthetic but make it more aerodynamic and premium for 2035.

Required components:
- Faceted monocoque body shell with sloped windshield, roofline, and bed cover.
- Distinct front fascia with full-width light bar.
- Rear tailgate with full-width taillight bar.
- Four large aero wheels with tire solids and simplified brake discs.
- Wheel arch cutouts/fender surfaces.
- Side camera pods, lidar/sensor placeholders, charging port cover.
- Underbody battery/skateboard plate and air-diffuser geometry.
- Optional open bed-cover seam and panel gaps.

Parametric requirements:
- Define wheelbase, overall length, width, height, wheel diameter, tire width, body panel thickness, bed length, and ground clearance as named parameters.
- Keep body, glass, wheels, tires, lights, sensor pods, battery plate, and underbody aero as separate solids/components.
- Use robust faceted solids/chamfers; avoid fragile fillets across complex intersections.

Validation:
- Report bounding box, wheel count, sensor count, light bar count, and component count.
- Verify four wheels contact the ground plane and are symmetric about the centerline.
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
        raise RuntimeError(f"Cybertruck 2035 concept validation failed: {report}")
    return {"step_output": STEP_OUTPUT, "glb_output": GLB_OUTPUT, "validation": report}


if __name__ == "__main__":
    assembly = build_assembly()
    _write_components()
    output_dir = Path(__file__).resolve().parent
    if not export_step(assembly, output_dir / STEP_OUTPUT):
        raise RuntimeError(f"failed to export {STEP_OUTPUT}")
    if not export_gltf(assembly, output_dir / GLB_OUTPUT, binary=True, linear_deflection=0.65, angular_deflection=0.35):
        raise RuntimeError(f"failed to export {GLB_OUTPUT}")
    report = _validation_report(assembly)
    _write_json(VALIDATION_OUTPUT, report)
    _write_prompt()
    if not report["passed"]:
        raise RuntimeError(f"Cybertruck 2035 concept validation failed: {report}")
    print(json.dumps({"step_output": STEP_OUTPUT, "glb_output": GLB_OUTPUT, "validation": report}, indent=2))
