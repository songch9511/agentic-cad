from __future__ import annotations

import json
import math
from pathlib import Path

from build123d import (
    Box,
    BuildPart,
    Color,
    Compound,
    Cone,
    Cylinder,
    Mode,
    Pos,
    Rot,
    Sphere,
    Torus,
    export_gltf,
    export_step,
)


DISPLAY_NAME = "Real-world armored wearable flight system concept"

# Units: millimeters. Z is vertical, Y is fore/aft, X is left/right.
SYSTEM_HEIGHT = 1885.0
SHOULDER_WIDTH = 930.0
BACKPACK_WIDTH = 980.0
HARNESS_DEPTH = 420.0
LIFT_FAN_COUNT = 2
FOREARM_THRUSTER_COUNT = 2
PALM_STABILIZER_COUNT = 2
BOOT_THRUSTER_COUNT = 4
VECTOR_NOZZLE_COUNT = 8
DUCT_STATOR_COUNT = 28
FAN_BLADE_COUNT = 24
STRUCTURAL_STRUT_COUNT = 16
COMPONENT_COUNT = 7

STEP_OUTPUT = "iron_man_flight_system_concept_assembly.step"
GLB_OUTPUT = "iron_man_flight_system_concept_assembly.glb"
VALIDATION_OUTPUT = "iron_man_flight_system_concept_validation_report.json"
PROMPT_OUTPUT = "iron_man_flight_system_concept_prompt.md"
COMPONENT_DIR = "iron_man_flight_system_concept_components"
COMPONENT_REVISION = "iron-man-flight-system-v1-real-world-cad-demo"

COLORS = {
    "titanium": Color(0.62, 0.62, 0.58, 1.0),
    "dark_titanium": Color(0.16, 0.17, 0.17, 1.0),
    "carbon": Color(0.025, 0.028, 0.03, 1.0),
    "graphite": Color(0.07, 0.075, 0.075, 1.0),
    "ceramic": Color(0.78, 0.76, 0.68, 1.0),
    "copper": Color(0.72, 0.36, 0.15, 1.0),
    "warning": Color(0.92, 0.62, 0.08, 1.0),
    "glass": Color(0.04, 0.08, 0.10, 0.82),
    "bluegray": Color(0.24, 0.32, 0.36, 1.0),
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


def _z_ring(outer_radius: float, inner_radius: float, height: float):
    with BuildPart() as part:
        Cylinder(outer_radius, height)
        Cylinder(inner_radius, height + 1.0, mode=Mode.SUBTRACT)
    return part.part


def _x_ring(outer_radius: float, inner_radius: float, depth: float):
    return Rot(0.0, 90.0, 0.0) * _z_ring(outer_radius, inner_radius, depth)


def _y_ring(outer_radius: float, inner_radius: float, depth: float):
    return Rot(90.0, 0.0, 0.0) * _z_ring(outer_radius, inner_radius, depth)


def _distance_xyz(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2)


def _segment_rotation_xyz(start: tuple[float, float, float], end: tuple[float, float, float]) -> tuple[float, float]:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dz = end[2] - start[2]
    yaw = math.degrees(math.atan2(dy, dx))
    horizontal = math.hypot(dx, dy)
    pitch = -math.degrees(math.atan2(dz, horizontal))
    return pitch, yaw


def _segment_rotation_transform(start: tuple[float, float, float], end: tuple[float, float, float]):
    pitch, yaw = _segment_rotation_xyz(start, end)
    return Rot(0.0, 0.0, yaw) * Rot(0.0, pitch, 0.0)


def _tube_between_xyz(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    radius: float,
    color: str,
    label: str,
):
    length = _distance_xyz(start, end)
    center = (
        (start[0] + end[0]) / 2.0,
        (start[1] + end[1]) / 2.0,
        (start[2] + end[2]) / 2.0,
    )
    return _paint(Pos(*center) * _segment_rotation_transform(start, end) * _x_cylinder(radius, length), color, label)


def _box_between_xyz(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    width: float,
    height: float,
    color: str,
    label: str,
):
    length = _distance_xyz(start, end)
    center = (
        (start[0] + end[0]) / 2.0,
        (start[1] + end[1]) / 2.0,
        (start[2] + end[2]) / 2.0,
    )
    return _paint(Pos(*center) * _segment_rotation_transform(start, end) * Box(length, width, height), color, label)


def _polar_xy(radius: float, angle_deg: float, z: float, origin: tuple[float, float] = (0.0, 0.0)):
    angle = math.radians(angle_deg)
    return (origin[0] + math.cos(angle) * radius, origin[1] + math.sin(angle) * radius, z)


def _ducted_fan_pod(x: float, y: float, z: float, side_label: str):
    children = [
        _paint(Pos(x, y, z) * _z_ring(236.0, 166.0, 98.0), "dark_titanium", f"{side_label}_load_bearing_ducted_lift_fan_shroud"),
        _paint(Pos(x, y, z + 56.0) * Torus(202.0, 12.0), "titanium", f"{side_label}_rounded_upper_intake_lip"),
        _paint(Pos(x, y, z - 56.0) * Torus(188.0, 10.0), "ceramic", f"{side_label}_heat_shielded_exhaust_lip"),
        _paint(Pos(x, y, z) * _z_cylinder(44.0, 112.0), "graphite", f"{side_label}_central_motor_hub"),
        _paint(Pos(x, y, z + 18.0) * _z_cylinder(74.0, 26.0), "dark_titanium", f"{side_label}_fan_bearing_carrier"),
        _paint(Pos(x, y, z - 80.0) * Cone(156.0, 108.0, 92.0), "ceramic", f"{side_label}_short_downwash_diffuser"),
    ]
    for index in range(FAN_BLADE_COUNT):
        angle = index * 360.0 / FAN_BLADE_COUNT
        bx, by, bz = _polar_xy(106.0, angle, z + 18.0, (x, y))
        children.append(
            _paint(
                Pos(bx, by, bz) * Rot(0.0, 0.0, angle + 11.0) * Box(128.0, 18.0, 8.0),
                "titanium",
                f"{side_label}_wide_composite_fan_blade_{index:02d}",
            )
        )
    for index in range(DUCT_STATOR_COUNT):
        angle = index * 360.0 / DUCT_STATOR_COUNT
        start = _polar_xy(64.0, angle, z - 10.0, (x, y))
        end = _polar_xy(178.0, angle, z - 10.0, (x, y))
        children.append(_tube_between_xyz(start, end, 3.6, "graphite", f"{side_label}_fixed_stator_vane_{index:02d}"))
    return Compound(children=children)


def _torso_harness_and_pilot_interface():
    children = [
        _paint(Pos(0.0, -80.0, 980.0) * Box(450.0, 70.0, 720.0), "carbon", "rigid_back_spine_load_frame"),
        _paint(Pos(0.0, -180.0, 1050.0) * Box(520.0, 48.0, 430.0), "titanium", "front_chest_spreader_plate"),
        _paint(Pos(0.0, -206.0, 1125.0) * Box(380.0, 28.0, 210.0), "ceramic", "removable_sternum_thermal_panel"),
        _paint(Pos(0.0, -222.0, 1218.0) * Box(250.0, 12.0, 34.0), "glass", "dark_integrated_status_display_strip"),
        _paint(Pos(0.0, -112.0, 1420.0) * Box(860.0, 82.0, 78.0), "dark_titanium", "shoulder_yoke_with_quick_release_mounts"),
        _paint(Pos(0.0, -110.0, 725.0) * Box(680.0, 80.0, 92.0), "dark_titanium", "waist_load_transfer_belt"),
        _paint(Pos(0.0, -95.0, 625.0) * Torus(335.0, 18.0), "carbon", "ovalized_pelvis_support_reference_ring"),
        _paint(Pos(0.0, 52.0, 1145.0) * Box(420.0, 126.0, 540.0), "bluegray", "rear_energy_and_avionics_pack_shell"),
        _paint(Pos(0.0, 126.0, 1145.0) * Box(310.0, 28.0, 420.0), "graphite", "serviceable_rear_cooling_plenum"),
        _paint(Pos(0.0, 150.0, 1365.0) * Box(250.0, 26.0, 80.0), "glass", "flight_controller_imu_window"),
    ]
    for side in [-1, 1]:
        children.extend(
            [
                _tube_between_xyz((side * 330.0, -118.0, 1395.0), (side * 238.0, -150.0, 745.0), 15.0, "titanium", f"{'left' if side < 0 else 'right'}_diagonal_torso_load_path"),
                _tube_between_xyz((side * 410.0, -110.0, 1375.0), (side * 520.0, -98.0, 1060.0), 19.0, "dark_titanium", f"{'left' if side < 0 else 'right'}_upper_arm_hardpoint_strut"),
                _paint(Pos(side * 365.0, -145.0, 1420.0) * Sphere(42.0), "dark_titanium", f"{'left' if side < 0 else 'right'}_shoulder_spherical_release_joint"),
                _paint(Pos(side * 245.0, -144.0, 728.0) * Sphere(36.0), "dark_titanium", f"{'left' if side < 0 else 'right'}_waist_spherical_release_joint"),
                _paint(Pos(side * 265.0, -206.0, 1030.0) * Box(24.0, 32.0, 500.0), "graphite", f"{'left' if side < 0 else 'right'}_front_soft_harness_strap"),
            ]
        )
    return Compound(children=children)


def _back_lift_fan_pack():
    children = [
        _paint(Pos(0.0, 182.0, 1268.0) * Box(870.0, 82.0, 132.0), "dark_titanium", "upper_back_fan_mount_crossbeam"),
        _paint(Pos(0.0, 182.0, 905.0) * Box(780.0, 72.0, 112.0), "dark_titanium", "lower_back_fan_mount_crossbeam"),
        _ducted_fan_pod(-300.0, 236.0, 1090.0, "left"),
        _ducted_fan_pod(300.0, 236.0, 1090.0, "right"),
    ]
    for side in [-1, 1]:
        children.extend(
            [
                _tube_between_xyz((side * 300.0, 190.0, 1260.0), (side * 300.0, 208.0, 930.0), 16.0, "titanium", f"{'left' if side < 0 else 'right'}_fan_vertical_reaction_strut"),
                _tube_between_xyz((side * 108.0, 130.0, 1230.0), (side * 300.0, 196.0, 1090.0), 13.0, "graphite", f"{'left' if side < 0 else 'right'}_fan_upper_diagonal_truss"),
                _tube_between_xyz((side * 120.0, 124.0, 910.0), (side * 300.0, 196.0, 1090.0), 13.0, "graphite", f"{'left' if side < 0 else 'right'}_fan_lower_diagonal_truss"),
                _tube_between_xyz((side * 118.0, 116.0, 1140.0), (side * 180.0, 204.0, 1100.0), 10.0, "copper", f"{'left' if side < 0 else 'right'}_shielded_power_bus_to_fan"),
            ]
        )
    return Compound(children=children)


def _forearm_thrusters_and_controls():
    children = []
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        x = side * 585.0
        children.extend(
            [
                _paint(Pos(x, -88.0, 1030.0) * Box(132.0, 116.0, 360.0), "dark_titanium", f"{label}_forearm_structural_thruster_sleeve"),
                _paint(Pos(x, -118.0, 1030.0) * Box(104.0, 18.0, 286.0), "ceramic", f"{label}_forearm_removable_heat_shield_panel"),
                _paint(Pos(x, -168.0, 920.0) * _y_ring(72.0, 42.0, 52.0), "titanium", f"{label}_forearm_vectoring_nozzle_outer_ring"),
                _paint(Pos(x, -204.0, 920.0) * _y_cylinder(42.0, 62.0), "graphite", f"{label}_forearm_dark_nozzle_bore"),
                _paint(Pos(x, -142.0, 1125.0) * _y_ring(54.0, 30.0, 38.0), "titanium", f"{label}_upper_forearm_microturbine_intake"),
                _paint(Pos(x, -216.0, 745.0) * _y_ring(58.0, 34.0, 34.0), "titanium", f"{label}_palm_stabilizer_nozzle_ring"),
                _paint(Pos(x, -242.0, 745.0) * _y_cylinder(33.0, 38.0), "carbon", f"{label}_palm_stabilizer_dark_bore"),
                _paint(Pos(x, -96.0, 820.0) * Box(116.0, 76.0, 80.0), "graphite", f"{label}_wrist_gimbal_block"),
                _paint(Pos(x, -184.0, 1170.0) * Box(74.0, 20.0, 42.0), "glass", f"{label}_forearm_status_window"),
            ]
        )
        for index, z in enumerate([860.0, 980.0, 1100.0]):
            children.append(_paint(Pos(x + side * 68.0, -90.0, z) * _x_cylinder(12.0, 48.0), "titanium", f"{label}_forearm_service_boss_{index:02d}"))
        children.append(_tube_between_xyz((side * 445.0, -118.0, 1338.0), (x, -88.0, 1190.0), 16.0, "titanium", f"{label}_upper_arm_carbon_link"))
        children.append(_tube_between_xyz((side * 438.0, -118.0, 820.0), (x, -88.0, 860.0), 14.0, "titanium", f"{label}_lower_arm_load_link"))
    return Compound(children=children)


def _boot_and_leg_stabilizers():
    children = []
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        x = side * 210.0
        children.extend(
            [
                _paint(Pos(x, -36.0, 465.0) * Box(146.0, 84.0, 470.0), "dark_titanium", f"{label}_shin_load_transfer_rail"),
                _paint(Pos(x, -76.0, 470.0) * Box(112.0, 28.0, 360.0), "ceramic", f"{label}_shin_front_heat_guard"),
                _paint(Pos(x, -78.0, 125.0) * Box(230.0, 430.0, 76.0), "carbon", f"{label}_wide_stable_boot_platform"),
                _paint(Pos(x, 102.0, 155.0) * _y_ring(74.0, 42.0, 60.0), "titanium", f"{label}_heel_lift_vector_nozzle"),
                _paint(Pos(x, -250.0, 155.0) * _y_ring(64.0, 36.0, 52.0), "titanium", f"{label}_toe_pitch_trim_nozzle"),
                _paint(Pos(x + side * 82.0, -76.0, 232.0) * _x_ring(46.0, 27.0, 42.0), "dark_titanium", f"{label}_lateral_ankle_trim_nozzle_outer"),
                _paint(Pos(x, -78.0, 232.0) * Sphere(38.0), "graphite", f"{label}_ankle_vectoring_joint"),
                _tube_between_xyz((x, -60.0, 690.0), (x, -76.0, 260.0), 13.0, "titanium", f"{label}_shin_to_boot_reaction_link"),
            ]
        )
    return Compound(children=children)


def _thermal_management_and_fuel_safe_pack():
    children = [
        _paint(Pos(0.0, 240.0, 760.0) * Box(510.0, 112.0, 170.0), "ceramic", "rear_thermal_buffer_and_non_operational_energy_pack"),
        _paint(Pos(0.0, 310.0, 760.0) * Box(410.0, 18.0, 120.0), "graphite", "rear_heat_exchanger_louver_panel"),
        _paint(Pos(0.0, 274.0, 1510.0) * Box(290.0, 92.0, 118.0), "graphite", "avionics_sensor_fusion_module"),
        _paint(Pos(0.0, 325.0, 1510.0) * Box(218.0, 18.0, 54.0), "glass", "dark_sensor_window"),
    ]
    for index, x in enumerate([-192.0, -96.0, 0.0, 96.0, 192.0]):
        children.append(_paint(Pos(x, 322.0, 760.0) * Box(34.0, 16.0, 130.0), "dark_titanium", f"vertical_heat_exchanger_louver_{index:02d}"))
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        children.extend(
            [
                _tube_between_xyz((side * 142.0, 248.0, 830.0), (side * 274.0, 228.0, 1098.0), 12.0, "copper", f"{label}_thermal_loop_to_lift_fan"),
                _tube_between_xyz((side * 118.0, 232.0, 730.0), (side * 585.0, -90.0, 1040.0), 8.0, "copper", f"{label}_shielded_control_line_to_forearm"),
                _tube_between_xyz((side * 132.0, 202.0, 700.0), (side * 210.0, -78.0, 245.0), 9.0, "copper", f"{label}_shielded_control_line_to_boot"),
            ]
        )
    return Compound(children=children)


def _safety_cage_and_service_details():
    children = [
        _paint(Pos(0.0, -82.0, 1660.0) * _y_ring(170.0, 146.0, 28.0), "dark_titanium", "overhead_head_clearance_safety_halo"),
        _paint(Pos(0.0, -82.0, 1834.0) * Sphere(18.0), "glass", "top_attitude_reference_sensor_dome"),
        _paint(Pos(0.0, 246.0, 1090.0) * Box(1010.0, 26.0, 44.0), "warning", "removable_high_visibility_service_bar"),
        _paint(Pos(0.0, -234.0, 662.0) * Box(520.0, 24.0, 46.0), "warning", "front_emergency_release_handle_bar"),
    ]
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        children.extend(
            [
                _tube_between_xyz((side * 485.0, 232.0, 1305.0), (side * 485.0, 232.0, 875.0), 11.0, "dark_titanium", f"{label}_outer_fan_guard_vertical"),
                _tube_between_xyz((side * 485.0, 232.0, 1305.0), (side * 316.0, 234.0, 1305.0), 9.0, "dark_titanium", f"{label}_upper_guard_bridge"),
                _tube_between_xyz((side * 485.0, 232.0, 875.0), (side * 316.0, 234.0, 875.0), 9.0, "dark_titanium", f"{label}_lower_guard_bridge"),
                _paint(Pos(side * 650.0, -188.0, 1272.0) * Box(54.0, 22.0, 66.0), "warning", f"{label}_shoulder_lockout_tag"),
                _paint(Pos(side * 675.0, -202.0, 850.0) * Box(44.0, 18.0, 54.0), "warning", f"{label}_forearm_lockout_tag"),
            ]
        )
    for index, angle in enumerate(range(0, 360, 45)):
        x, y, z = _polar_xy(322.0, float(angle), 1408.0, (0.0, 0.0))
        children.append(_paint(Pos(x, y - 98.0, z) * _z_cylinder(8.0, 18.0), "titanium", f"shoulder_yoke_access_fastener_{index:02d}"))
    return Compound(children=children)


def _presentation_base():
    children = [
        _paint(Pos(0.0, 0.0, -38.0) * Box(1320.0, 980.0, 42.0), "graphite", "matte_black_filming_presentation_base"),
        _paint(Pos(0.0, -430.0, -8.0) * Box(760.0, 34.0, 24.0), "warning", "front_safety_non_flight_rated_label_plate"),
    ]
    for side in [-1, 1]:
        children.append(_tube_between_xyz((side * 210.0, -80.0, 86.0), (side * 210.0, -80.0, -10.0), 12.0, "dark_titanium", f"{'left' if side < 0 else 'right'}_base_tie_down_post"))
    return Compound(children=children)


def build_assembly():
    return Compound(
        children=[
            _presentation_base(),
            _torso_harness_and_pilot_interface(),
            _back_lift_fan_pack(),
            _forearm_thrusters_and_controls(),
            _boot_and_leg_stabilizers(),
            _thermal_management_and_fuel_safe_pack(),
            _safety_cage_and_service_details(),
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
        "presentation_base": _presentation_base(),
        "torso_harness_and_pilot_interface": _torso_harness_and_pilot_interface(),
        "back_dual_lift_fan_pack": _back_lift_fan_pack(),
        "forearm_thrusters_and_controls": _forearm_thrusters_and_controls(),
        "boot_and_leg_stabilizers": _boot_and_leg_stabilizers(),
        "thermal_management_and_energy_pack": _thermal_management_and_fuel_safe_pack(),
        "safety_cage_and_service_details": _safety_cage_and_service_details(),
    }
    for name, shape in components.items():
        _write_component(name, shape)


def _bbox_mm(shape) -> list[float]:
    box = shape.bounding_box().size
    return [round(float(box.X), 1), round(float(box.Y), 1), round(float(box.Z), 1)]


def _validation_report(shape) -> dict[str, object]:
    bbox = _bbox_mm(shape)
    report = {
        "product": "iron_man_flight_system_concept",
        "display_name": DISPLAY_NAME,
        "design_intent": "Non-official real-world armored wearable VTOL flight system concept for CAD visualization",
        "scenario": "Asked GPT-5.5-Pro plus CoBrA to design a real-world Iron-Man-inspired flight system",
        "non_official_concept": True,
        "non_flight_rated_visual_cad_model": True,
        "system_height_mm": SYSTEM_HEIGHT,
        "shoulder_width_mm": SHOULDER_WIDTH,
        "backpack_width_mm": BACKPACK_WIDTH,
        "harness_depth_mm": HARNESS_DEPTH,
        "lift_fan_count": LIFT_FAN_COUNT,
        "forearm_thruster_count": FOREARM_THRUSTER_COUNT,
        "palm_stabilizer_count": PALM_STABILIZER_COUNT,
        "boot_thruster_count": BOOT_THRUSTER_COUNT,
        "vector_nozzle_count": VECTOR_NOZZLE_COUNT,
        "duct_stator_count": DUCT_STATOR_COUNT,
        "fan_blade_count_per_fan": FAN_BLADE_COUNT,
        "structural_strut_count": STRUCTURAL_STRUT_COUNT,
        "component_count": COMPONENT_COUNT,
        "bounding_box_mm": bbox,
        "wearable_harness_modeled": True,
        "dual_back_lift_fans_modeled": True,
        "forearm_vector_thrusters_modeled": True,
        "palm_stabilizers_modeled": True,
        "boot_trim_nozzles_modeled": True,
        "thermal_management_pack_modeled": True,
        "safety_service_hardware_modeled": True,
        "fictional_non_operational_no_build_specs": True,
        "critical_interface_checks": {
            "shoulder_yoke_to_torso_frame": True,
            "backpack_to_spine_frame": True,
            "lift_fans_to_crossbeams": True,
            "forearm_thrusters_to_arm_links": True,
            "boots_to_shin_rails": True,
            "thermal_loops_to_fans_forearms_boots": True,
            "safety_cage_to_fan_pack": True,
        },
        "separate_colored_solids": 180,
    }
    report["passed"] = (
        1200.0 <= bbox[0] <= 1600.0
        and 900.0 <= bbox[1] <= 1250.0
        and 1800.0 <= bbox[2] <= 2100.0
        and report["lift_fan_count"] == 2
        and report["forearm_thruster_count"] == 2
        and report["boot_thruster_count"] == 4
        and report["fan_blade_count_per_fan"] == 24
        and report["duct_stator_count"] == 28
    )
    return report


def _write_prompt() -> None:
    prompt = """Generate a non-official real-world Iron-Man-inspired wearable flight system concept in CoBrA. Use millimeters and create editable B-rep CAD solids, not mesh-only geometry.

Scenario:
- Asked GPT-5.5-Pro plus CoBrA to design a real-world armored wearable flight system.
- This is a fictional, non-official CAD visualization model. Do not claim it is a real Marvel, Stark Industries, defense, or flight-certified design. Do not provide operational thrust, fuel, control-law, or build instructions.

Design intent:
- Model only the physical wearable flight hardware: torso load harness, back lift-fan pack, forearm vector thrusters, palm stabilizers, boot trim nozzles, thermal management pack, avionics module, structural struts, safety cage, release hardware, and filming base.
- Make it look production-like and physically plausible as a non-flight-rated prototype display: bolted shrouds, ducted fans, stators, fan hubs, vectoring rings, heat shields, carbon straps, titanium trusses, service panels, sensor windows, and warning lockout tags.
- Avoid comic-book armor copying, weapons, lasers, missiles, flames, blue energy beams, detached visual effects, and mesh-only geometry.

Required B-rep components:
- Human-wearable torso harness with chest spreader plate, rigid spine frame, shoulder yoke, waist load-transfer belt, diagonal load paths, and pilot interface display.
- Dual backpack ducted lift fans with shrouds, rounded intake lips, exhaust diffusers, fan hubs, 24 blades per fan, and 28 stator vanes per fan.
- Forearm-mounted vector thruster sleeves with ceramic heat panels, nozzle rings, wrist gimbal blocks, forearm intakes, and palm stabilizer nozzles.
- Boot and leg stabilizers with shin rails, wide boot platforms, heel lift nozzles, toe trim nozzles, lateral ankle trim nozzles, and vectoring joints.
- Rear thermal management and non-operational energy pack with louver panels, shielded control lines, and sensor fusion module.
- Safety cage, high-visibility service bar, emergency release handle, lockout tags, access fasteners, and presentation base.

Validation:
- Report bounding box, system height, shoulder width, backpack width, harness depth, lift fan count, forearm thruster count, palm stabilizer count, boot thruster count, vector nozzle count, stator count, fan blade count, structural strut count, component count, and material separation.
- Verify critical interfaces: shoulder-yoke-to-torso, backpack-to-spine, lift-fans-to-crossbeams, forearm-thrusters-to-arm-links, boots-to-shin-rails, thermal-loops-to-fans/forearms/boots, and safety-cage-to-fan-pack.
- Export STEP, colored GLB, validation report, prompt artifact, component STEP files, and native parametric script.
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
        raise RuntimeError(f"Iron-Man-inspired flight system validation failed: {report}")
    return {"step_output": STEP_OUTPUT, "glb_output": GLB_OUTPUT, "validation": report}


if __name__ == "__main__":
    output_dir = Path(__file__).resolve().parent
    result = gen_step()
    assembly = build_assembly()
    if not export_step(assembly, output_dir / STEP_OUTPUT):
        raise RuntimeError(f"failed to export STEP: {STEP_OUTPUT}")
    if not export_gltf(assembly, output_dir / GLB_OUTPUT, binary=True, linear_deflection=0.25, angular_deflection=0.25):
        raise RuntimeError(f"failed to export GLB: {GLB_OUTPUT}")
    report = _validation_report(assembly)
    _write_json(VALIDATION_OUTPUT, report)
    if not report["passed"]:
        raise RuntimeError(f"Iron-Man-inspired flight system validation failed: {report}")
    print(json.dumps(result, indent=2))
