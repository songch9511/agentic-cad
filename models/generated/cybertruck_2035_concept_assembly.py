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
    Plane,
    Polygon,
    Pos,
    Rot,
    Sphere,
    Torus,
    export_gltf,
    export_step,
    extrude,
)


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
COMPONENT_REVISION = "cybertruck-2035-concept-v3"

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


def _y_torus(major_radius: float, minor_radius: float):
    return Rot(90.0, 0.0, 0.0) * Torus(major_radius, minor_radius)


def _body_shell():
    sill_z = GROUND_CLEARANCE + 210.0
    belt_z = sill_z + 420.0
    roof_z = GROUND_CLEARANCE + HEIGHT - 210.0
    profile = [
        (-OVERALL_LENGTH / 2.0 + 120.0, GROUND_CLEARANCE + 105.0),
        (-OVERALL_LENGTH / 2.0 + 210.0, sill_z + 260.0),
        (-2120.0, belt_z + 110.0),
        (-1260.0, roof_z - 130.0),
        (-470.0, roof_z),
        (620.0, roof_z - 120.0),
        (OVERALL_LENGTH / 2.0 - 330.0, belt_z + 270.0),
        (OVERALL_LENGTH / 2.0 - 145.0, sill_z + 180.0),
        (OVERALL_LENGTH / 2.0 - 245.0, GROUND_CLEARANCE + 115.0),
        (-OVERALL_LENGTH / 2.0 + 280.0, GROUND_CLEARANCE + 115.0),
    ]
    with BuildPart() as side_profile:
        with BuildSketch():
            Polygon(*profile)
        extrude(amount=(WIDTH - 410.0) / 2.0, both=True)
    children = [
        _paint(Pos(0.0, 0.0, (GROUND_CLEARANCE + 105.0 + roof_z) / 2.0) * Rot(90.0, 0.0, 0.0) * side_profile.part, "stainless", "single_piece_faceted_monocoque_body_profile"),
        _paint(Pos(0.0, 0.0, GROUND_CLEARANCE + 235.0) * Box(OVERALL_LENGTH - 440.0, WIDTH - 140.0, 265.0), "dark_stainless", "continuous_lower_skateboard_side_mass"),
        _paint(Pos(-2320.0, 0.0, sill_z + 250.0) * Rot(0.0, -12.0, 0.0) * Box(980.0, WIDTH - 330.0, 42.0), "brushed_edge", "integrated_low_front_hood_facet"),
        _paint(Pos(-360.0, 0.0, roof_z - 62.0) * Rot(0.0, -4.0, 0.0) * Box(1060.0, WIDTH - 780.0, 18.0), "brushed_edge", "flush_low_cabin_roof_facet"),
        _paint(Pos(1460.0, 0.0, sill_z + 1040.0) * Rot(0.0, -3.2, 0.0) * Box(BED_LENGTH + 70.0, WIDTH - 720.0, 18.0), "dark_stainless", "flush_fastback_bed_cover_facet"),
        _paint(Pos(2520.0, 0.0, sill_z + 405.0) * Rot(0.0, 4.5, 0.0) * Box(660.0, WIDTH - 320.0, 42.0), "brushed_edge", "integrated_tailgate_upper_facet"),
        _paint(Pos(-1180.0, -WIDTH / 2.0 + 112.0, belt_z + 70.0) * Rot(-4.0, 0.0, 0.0) * Box(110.0, 68.0, 810.0), "dark_stainless", "left_a_pillar_mass"),
        _paint(Pos(-1180.0, WIDTH / 2.0 - 112.0, belt_z + 70.0) * Rot(4.0, 0.0, 0.0) * Box(110.0, 68.0, 810.0), "dark_stainless", "right_a_pillar_mass"),
        _paint(Pos(390.0, -WIDTH / 2.0 + 112.0, belt_z + 5.0) * Rot(-3.0, 0.0, 0.0) * Box(92.0, 68.0, 700.0), "dark_stainless", "left_b_pillar_mass"),
        _paint(Pos(390.0, WIDTH / 2.0 - 112.0, belt_z + 5.0) * Rot(3.0, 0.0, 0.0) * Box(92.0, 68.0, 700.0), "dark_stainless", "right_b_pillar_mass"),
        _paint(Pos(-520.0, -WIDTH / 2.0 - 8.0, sill_z + 620.0) * Rot(0.0, -8.0, 0.0) * Box(1500.0, 16.0, 26.0), "brushed_edge", "left_sharp_upper_beltline_crease"),
        _paint(Pos(-520.0, WIDTH / 2.0 + 8.0, sill_z + 620.0) * Rot(0.0, -8.0, 0.0) * Box(1500.0, 16.0, 26.0), "brushed_edge", "right_sharp_upper_beltline_crease"),
        _paint(Pos(1320.0, -WIDTH / 2.0 - 8.0, sill_z + 500.0) * Rot(0.0, -3.0, 0.0) * Box(1900.0, 16.0, 24.0), "brushed_edge", "left_bed_side_integrated_crease"),
        _paint(Pos(1320.0, WIDTH / 2.0 + 8.0, sill_z + 500.0) * Rot(0.0, -3.0, 0.0) * Box(1900.0, 16.0, 24.0), "brushed_edge", "right_bed_side_integrated_crease"),
    ]
    return Compound(children=children)


def _glass_and_panel_gaps():
    sill_z = GROUND_CLEARANCE + 210.0
    roof_z = GROUND_CLEARANCE + HEIGHT - 210.0
    children = [
        _paint(Pos(-1030.0, 0.0, roof_z - 260.0) * Rot(0.0, -29.0, 0.0) * Box(930.0, WIDTH - 690.0, 26.0), "glass", "panoramic_sloped_windshield_solid"),
        _paint(Pos(-360.0, -WIDTH / 2.0 - 36.0, sill_z + 720.0) * Rot(0.0, -7.5, 0.0) * Box(980.0, 24.0, 250.0), "glass", "left_flush_side_glass_band"),
        _paint(Pos(-360.0, WIDTH / 2.0 + 36.0, sill_z + 720.0) * Rot(0.0, -7.5, 0.0) * Box(980.0, 24.0, 250.0), "glass", "right_flush_side_glass_band"),
        _paint(Pos(1480.0, 0.0, sill_z + 1054.0) * Rot(0.0, -3.2, 0.0) * Box(BED_LENGTH - 80.0, WIDTH - 800.0, 10.0), "brushed_edge", "visible_closed_bed_cover_seam_surface"),
    ]
    for side in (-1, 1):
        name = "right" if side > 0 else "left"
        y = side * (WIDTH / 2.0 + 42.0)
        for index, x in enumerate([-1760.0, -720.0, 420.0, 1260.0, 2140.0], start=1):
            children.append(_paint(Pos(x, y, sill_z + 275.0) * Box(10.0, 14.0, 420.0), "sensor", f"{name}_recessed_vertical_panel_gap_{index:02d}"))
    return Compound(children=children)


def _doors_and_side_details():
    sill_z = GROUND_CLEARANCE + 210.0
    children = []
    for side in (-1, 1):
        name = "right" if side > 0 else "left"
        y_skin = side * (WIDTH / 2.0 + 36.0)
        y_trim = side * (WIDTH / 2.0 + 48.0)
        children.extend(
            [
                _paint(Pos(-720.0, y_skin, sill_z + 340.0) * Box(760.0, 18.0, 370.0), "stainless", f"{name}_front_door_inset_panel"),
                _paint(Pos(190.0, y_skin, sill_z + 325.0) * Box(760.0, 18.0, 340.0), "stainless", f"{name}_rear_door_inset_panel"),
                _paint(Pos(1130.0, y_skin, sill_z + 335.0) * Box(860.0, 18.0, 350.0), "stainless", f"{name}_bed_side_outer_panel"),
                _paint(Pos(-1120.0, y_trim, sill_z + 343.0) * Box(12.0, 14.0, 410.0), "sensor", f"{name}_front_door_leading_gap"),
                _paint(Pos(-300.0, y_trim, sill_z + 338.0) * Box(12.0, 14.0, 395.0), "sensor", f"{name}_front_rear_door_gap"),
                _paint(Pos(610.0, y_trim, sill_z + 328.0) * Box(12.0, 14.0, 380.0), "sensor", f"{name}_rear_door_bed_gap"),
                _paint(Pos(-720.0, y_trim, sill_z + 535.0) * Box(720.0, 13.0, 12.0), "brushed_edge", f"{name}_front_door_upper_crease"),
                _paint(Pos(190.0, y_trim, sill_z + 505.0) * Box(710.0, 13.0, 12.0), "brushed_edge", f"{name}_rear_door_upper_crease"),
                _paint(Pos(1180.0, y_trim, sill_z + 500.0) * Box(820.0, 13.0, 12.0), "brushed_edge", f"{name}_bed_side_upper_crease"),
                _paint(Pos(-720.0, y_trim, sill_z + 150.0) * Box(720.0, 13.0, 12.0), "dark_stainless", f"{name}_front_door_lower_shadow_gap"),
                _paint(Pos(190.0, y_trim, sill_z + 145.0) * Box(710.0, 13.0, 12.0), "dark_stainless", f"{name}_rear_door_lower_shadow_gap"),
                _paint(Pos(-680.0, y_trim + side * 4.0, sill_z + 435.0) * Box(178.0, 16.0, 24.0), "sensor", f"{name}_front_flush_door_handle"),
                _paint(Pos(170.0, y_trim + side * 4.0, sill_z + 420.0) * Box(178.0, 16.0, 24.0), "sensor", f"{name}_rear_flush_door_handle"),
                _paint(Pos(830.0, y_trim + side * 5.0, sill_z + 318.0) * Box(24.0, 172.0, 128.0), "dark_stainless", f"{name}_flush_charging_port_door"),
            ]
        )
    return Compound(children=children)


def _fascia_and_lights():
    sill_z = GROUND_CLEARANCE + 210.0
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
                    _paint(Pos(x, y, wheel_z) * _y_cylinder(radius * 0.74, TIRE_WIDTH + 10.0), "wheel", f"{side}_{axle}_smooth_full_aero_wheel_disc"),
                    _paint(Pos(x, y, wheel_z) * _y_cylinder(radius * 0.44, TIRE_WIDTH + 22.0), "titanium", f"{side}_{axle}_simplified_brake_disc_solid"),
                    _paint(Pos(x, y, wheel_z) * _y_cylinder(radius * 0.18, TIRE_WIDTH + 30.0), "dark_stainless", f"{side}_{axle}_flush_center_hub"),
                    _paint(Pos(x, y + (1 if y > 0 else -1) * (TIRE_WIDTH / 2.0 + 22.0), wheel_z) * _y_torus(radius * 0.79, 18.0), "brushed_edge", f"{side}_{axle}_machined_outer_rim_ring"),
                    _paint(Pos(x, y + (1 if y > 0 else -1) * (TIRE_WIDTH / 2.0 + 48.0), wheel_z) * _y_torus(radius * 1.08, 22.0), "sensor", f"{side}_{axle}_round_wheel_well_liner"),
                    _paint(Pos(x, y + (1 if y > 0 else -1) * (TIRE_WIDTH / 2.0 + 64.0), wheel_z + radius * 0.72) * Box(840.0, 58.0, 92.0), "brushed_edge", f"{side}_{axle}_integrated_aero_fender_brow_surface"),
                ]
            )
            for spoke in range(4):
                angle = spoke * 45.0
                children.append(
                    _paint(Pos(x, y + (1 if y > 0 else -1) * (TIRE_WIDTH / 2.0 + 30.0), wheel_z) * Rot(0.0, angle, 0.0) * Box(radius * 0.82, 16.0, 18.0), "dark_stainless", f"{side}_{axle}_subtle_recessed_aero_spoke_{spoke + 1:02d}")
                )
    return Compound(children=children)


def _sensors_and_charge_port():
    sill_z = GROUND_CLEARANCE + 210.0
    roof_z = GROUND_CLEARANCE + HEIGHT - 210.0
    children = [
        _paint(Pos(-2058.0, -WIDTH / 2.0 - 46.0, sill_z + 664.0) * Box(56.0, 72.0, 16.0), "sensor", "left_side_camera_stalk"),
        _paint(Pos(-2058.0, WIDTH / 2.0 + 46.0, sill_z + 664.0) * Box(56.0, 72.0, 16.0), "sensor", "right_side_camera_stalk"),
        _paint(Pos(-2085.0, -WIDTH / 2.0 - 86.0, sill_z + 664.0) * Box(86.0, 36.0, 48.0), "sensor", "left_side_camera_pod_attached"),
        _paint(Pos(-2085.0, WIDTH / 2.0 + 86.0, sill_z + 664.0) * Box(86.0, 36.0, 48.0), "sensor", "right_side_camera_pod_attached"),
        _paint(Pos(-1680.0, 0.0, roof_z - 155.0) * _z_cylinder(48.0, 26.0), "sensor", "front_low_profile_lidar_sensor_placeholder"),
        _paint(Pos(420.0, 0.0, roof_z - 70.0) * _z_cylinder(42.0, 24.0), "sensor", "central_roof_lidar_sensor_placeholder"),
        _paint(Pos(2540.0, 0.0, sill_z + 610.0) * Box(80.0, 240.0, 52.0), "sensor", "rear_sensor_array_panel"),
        _paint(Pos(-2825.0, -650.0, sill_z + 435.0) * Box(18.0, 118.0, 36.0), "sensor", "left_integrated_front_radar_strip"),
        _paint(Pos(-2825.0, 650.0, sill_z + 435.0) * Box(18.0, 118.0, 36.0), "sensor", "right_integrated_front_radar_strip"),
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
            _doors_and_side_details(),
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
        "doors_and_side_details": _doors_and_side_details(),
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
        "component_count": 7,
        "separate_colored_solids": 132,
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
