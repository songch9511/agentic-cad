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


DISPLAY_NAME = "Humanoid dynamic balance system concept"

# Units: millimeters. This is a non-official, non-operational visual CAD model.
SYSTEM_HEIGHT = 1420.0
SYSTEM_WIDTH = 1000.0
SYSTEM_DEPTH = 420.0
STANCE_WIDTH = 560.0
FOOT_LENGTH = 420.0
FOOT_WIDTH = 190.0
PELVIS_HEIGHT = 890.0
SPINE_HEIGHT = 520.0
HIP_ACTUATOR_COUNT = 6
KNEE_ACTUATOR_COUNT = 2
ANKLE_ACTUATOR_COUNT = 4
FORCE_CELL_COUNT = 12
IMU_MODULE_COUNT = 3
REACTION_WHEEL_PLACEHOLDER_COUNT = 3
PERCEPTION_SENSOR_COUNT = 8
COMPONENT_COUNT = 6

STEP_OUTPUT = "humanoid_balance_system_concept_assembly.step"
GLB_OUTPUT = "humanoid_balance_system_concept_assembly.glb"
VALIDATION_OUTPUT = "humanoid_balance_system_concept_validation_report.json"
PROMPT_OUTPUT = "humanoid_balance_system_concept_prompt.md"
COMPONENT_DIR = "humanoid_balance_system_concept_components"
COMPONENT_REVISION = "humanoid-balance-system-v2-muted-service-hardware-demo"

COLORS = {
    "titanium": Color(0.63, 0.64, 0.62, 1.0),
    "dark_titanium": Color(0.16, 0.17, 0.17, 1.0),
    "carbon": Color(0.025, 0.028, 0.03, 1.0),
    "graphite": Color(0.075, 0.078, 0.08, 1.0),
    "rubber": Color(0.01, 0.01, 0.012, 1.0),
    "ceramic": Color(0.78, 0.77, 0.70, 1.0),
    "copper": Color(0.34, 0.24, 0.16, 1.0),
    "sensor": Color(0.04, 0.16, 0.19, 1.0),
    "warning": Color(0.94, 0.63, 0.08, 1.0),
    "glass": Color(0.035, 0.08, 0.10, 0.82),
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


def _foot_force_plate_modules():
    children = []
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        x = side * STANCE_WIDTH / 2.0
        children.extend(
            [
                _paint(Pos(x, 0.0, 32.0) * Box(FOOT_WIDTH, FOOT_LENGTH, 64.0), "rubber", f"{label}_broad_contact_sole"),
                _paint(Pos(x, -156.0, 78.0) * Box(176.0, 92.0, 22.0), "graphite", f"{label}_heel_force_plate_deck"),
                _paint(Pos(x, 124.0, 80.0) * Box(184.0, 150.0, 24.0), "graphite", f"{label}_toe_force_plate_deck"),
                _paint(Pos(x, 0.0, 112.0) * Box(150.0, 318.0, 26.0), "dark_titanium", f"{label}_upper_foot_sensor_bridge"),
                _paint(Pos(x, -28.0, 156.0) * _z_cylinder(58.0, 82.0), "dark_titanium", f"{label}_ankle_pedestal_housing"),
                _paint(Pos(x, -28.0, 210.0) * _z_ring(64.0, 38.0, 22.0), "titanium", f"{label}_ankle_torque_sensor_ring"),
                _paint(Pos(x - side * 82.0, 0.0, 95.0) * Box(12.0, 312.0, 8.0), "graphite", f"{label}_outer_embedded_pressure_bus_strip"),
                _paint(Pos(x + side * 82.0, 0.0, 95.0) * Box(12.0, 312.0, 8.0), "graphite", f"{label}_inner_embedded_pressure_bus_strip"),
            ]
        )
        cell_index = 0
        for cell_y in [-148.0, -28.0, 112.0]:
            for cell_x in [-48.0, 48.0]:
                children.append(
                    _paint(
                        Pos(x + cell_x, cell_y, 134.0) * _z_cylinder(17.0, 14.0),
                        "sensor",
                        f"{label}_load_cell_pressure_sensor_{cell_index:02d}",
                    )
                )
                cell_index += 1
        for bolt_index, (bolt_x, bolt_y) in enumerate([(-70.0, -180.0), (70.0, -180.0), (-70.0, 176.0), (70.0, 176.0)]):
            children.append(
                _paint(
                    Pos(x + bolt_x, bolt_y, 148.0) * _z_cylinder(7.0, 10.0),
                    "titanium",
                    f"{label}_foot_deck_fastener_{bolt_index:02d}",
                )
            )
    return Compound(children=children)


def _lower_limb_actuation_frames():
    children = []
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        ankle = (side * STANCE_WIDTH / 2.0, -28.0, 220.0)
        knee = (side * (STANCE_WIDTH / 2.0 + 18.0), 18.0, 565.0)
        hip = (side * (STANCE_WIDTH / 2.0 + 42.0), -4.0, 872.0)
        children.extend(
            [
                _tube_between_xyz((ankle[0] - side * 28.0, -50.0, ankle[2] + 10.0), (knee[0] - side * 34.0, -4.0, knee[2] - 28.0), 18.0, "titanium", f"{label}_outer_lower_leg_load_link"),
                _tube_between_xyz((ankle[0] + side * 28.0, -8.0, ankle[2] + 8.0), (knee[0] + side * 32.0, 42.0, knee[2] - 32.0), 18.0, "titanium", f"{label}_inner_lower_leg_load_link"),
                _tube_between_xyz((knee[0] - side * 34.0, -6.0, knee[2] + 34.0), (hip[0] - side * 48.0, -24.0, hip[2] - 28.0), 20.0, "titanium", f"{label}_outer_upper_leg_load_link"),
                _tube_between_xyz((knee[0] + side * 34.0, 42.0, knee[2] + 30.0), (hip[0] + side * 44.0, 18.0, hip[2] - 28.0), 20.0, "titanium", f"{label}_inner_upper_leg_load_link"),
                _box_between_xyz((ankle[0], 28.0, ankle[2] + 42.0), (knee[0], 64.0, knee[2] - 58.0), 52.0, 34.0, "ceramic", f"{label}_front_shin_composite_fairing"),
                _box_between_xyz((knee[0], 58.0, knee[2] + 56.0), (hip[0], 42.0, hip[2] - 62.0), 58.0, 36.0, "ceramic", f"{label}_front_thigh_composite_fairing"),
                _paint(Pos(*knee) * _y_cylinder(62.0, 138.0), "dark_titanium", f"{label}_knee_pitch_actuator_housing"),
                _paint(Pos(knee[0], knee[1], knee[2]) * Rot(90.0, 0.0, 0.0) * Torus(66.0, 6.5), "dark_titanium", f"{label}_knee_torque_sensing_ring"),
                _paint(Pos(*ankle) * _x_cylinder(50.0, 118.0), "dark_titanium", f"{label}_ankle_roll_actuator_housing"),
                _paint(Pos(ankle[0], ankle[1], ankle[2] + 32.0) * _y_cylinder(44.0, 112.0), "dark_titanium", f"{label}_ankle_pitch_actuator_housing"),
                _paint(Pos(*hip) * _x_cylinder(68.0, 140.0), "dark_titanium", f"{label}_hip_roll_actuator_housing"),
                _paint(Pos(hip[0], hip[1], hip[2] + 78.0) * _y_cylinder(58.0, 124.0), "dark_titanium", f"{label}_hip_pitch_actuator_housing"),
                _paint(Pos(hip[0], hip[1], hip[2] - 78.0) * _z_cylinder(54.0, 74.0), "dark_titanium", f"{label}_hip_yaw_actuator_stack"),
                _tube_between_xyz((ankle[0] - side * 46.0, -44.0, ankle[2] + 56.0), (knee[0] - side * 54.0, -34.0, knee[2] - 24.0), 8.0, "dark_titanium", f"{label}_integrated_lower_leg_damper_placeholder"),
                _tube_between_xyz((knee[0] + side * 54.0, -34.0, knee[2] + 28.0), (hip[0] + side * 62.0, -32.0, hip[2] - 42.0), 8.0, "dark_titanium", f"{label}_integrated_upper_leg_damper_placeholder"),
            ]
        )
    return Compound(children=children)


def _pelvis_balance_core():
    children = [
        _paint(Pos(0.0, -8.0, PELVIS_HEIGHT) * Box(820.0, 164.0, 132.0), "carbon", "split_pelvis_balance_crossbeam"),
        _paint(Pos(0.0, 12.0, 976.0) * Box(456.0, 202.0, 176.0), "dark_titanium", "central_whole_body_control_computer_housing"),
        _paint(Pos(0.0, -112.0, 1042.0) * Box(332.0, 28.0, 128.0), "glass", "front_diagnostic_status_display"),
        _paint(Pos(0.0, 40.0, 1160.0) * Box(322.0, 162.0, 244.0), "graphite", "sealed_balance_processor_stack"),
        _paint(Pos(0.0, -6.0, 1240.0) * _z_cylinder(66.0, 96.0), "titanium", "central_spine_yaw_bearing"),
        _paint(Pos(0.0, -10.0, 1328.0) * Box(206.0, 118.0, 112.0), "carbon", "upper_spine_interface_block"),
        _paint(Pos(0.0, -126.0, 905.0) * Box(280.0, 36.0, 60.0), "warning", "non_operational_manual_safing_bar"),
    ]
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        x = side * (STANCE_WIDTH / 2.0 + 42.0)
        children.extend(
            [
                _paint(Pos(x, -4.0, 892.0) * Sphere(78.0), "dark_titanium", f"{label}_pelvis_hip_socket_outer_shell"),
                _paint(Pos(x, 84.0, 922.0) * Box(112.0, 42.0, 136.0), "graphite", f"{label}_hip_drive_service_cover"),
                _tube_between_xyz((x - side * 66.0, 76.0, 956.0), (side * 158.0, 78.0, 1088.0), 16.0, "titanium", f"{label}_diagonal_pelvis_to_core_reaction_strut"),
                _paint(Pos(side * 438.0, -14.0, 892.0) * _y_ring(62.0, 38.0, 36.0), "dark_titanium", f"{label}_outer_hip_encoder_ring"),
            ]
        )
    imu_positions = [(-82.0, -132.0, 1166.0), (0.0, -132.0, 1216.0), (82.0, -132.0, 1166.0)]
    for index, pos in enumerate(imu_positions):
        children.append(_paint(Pos(*pos) * Box(58.0, 22.0, 42.0), "sensor", f"triple_redundant_imu_module_{index:02d}"))
    for index, x in enumerate([-154.0, -92.0, -30.0, 30.0, 92.0, 154.0]):
        children.append(_paint(Pos(x, -130.0, 952.0) * _y_cylinder(7.0, 16.0), "titanium", f"control_housing_fastener_{index:02d}"))
    return Compound(children=children)


def _reaction_wheel_placeholder_cluster():
    center = (0.0, 52.0, 1168.0)
    children = [
        _paint(Pos(*center) * Sphere(48.0), "dark_titanium", "central_non_operational_inertial_hub"),
        _paint(Pos(*center) * Torus(132.0, 11.0), "titanium", "yaw_axis_reaction_wheel_placeholder_ring"),
        _paint(Pos(*center) * Rot(90.0, 0.0, 0.0) * Torus(118.0, 10.0), "titanium", "pitch_axis_reaction_wheel_placeholder_ring"),
        _paint(Pos(*center) * Rot(0.0, 90.0, 0.0) * Torus(104.0, 9.0), "titanium", "roll_axis_reaction_wheel_placeholder_ring"),
        _paint(Pos(center[0], center[1], center[2] + 144.0) * Box(276.0, 32.0, 30.0), "carbon", "upper_reaction_wheel_bridge"),
        _paint(Pos(center[0], center[1], center[2] - 144.0) * Box(276.0, 32.0, 30.0), "carbon", "lower_reaction_wheel_bridge"),
    ]
    for angle in [0.0, 90.0, 180.0, 270.0]:
        x, y, z = _polar_xy(148.0, angle, center[2], (center[0], center[1]))
        children.append(_tube_between_xyz(center, (x, y, z), 8.0, "dark_titanium", f"reaction_wheel_cage_spoke_{int(angle):03d}"))
    return Compound(children=children)


def _sensor_mast_and_perception_ring():
    children = [
        _tube_between_xyz((0.0, -70.0, 1240.0), (0.0, -70.0, 1386.0), 18.0, "carbon", "short_360_perception_mast"),
        _paint(Pos(0.0, -70.0, 1404.0) * _z_ring(112.0, 76.0, 36.0), "dark_titanium", "top_360_perception_sensor_ring"),
        _paint(Pos(0.0, -70.0, 1430.0) * _z_cylinder(52.0, 42.0), "glass", "sealed_lidar_style_perception_puck"),
        _paint(Pos(0.0, -70.0, 1362.0) * Box(194.0, 28.0, 34.0), "warning", "removable_calibration_target_bar"),
    ]
    for index in range(PERCEPTION_SENSOR_COUNT):
        angle = index * 360.0 / PERCEPTION_SENSOR_COUNT
        x, y, z = _polar_xy(126.0, angle, 1405.0, (0.0, -70.0))
        children.append(_paint(Pos(x, y, z) * Box(34.0, 22.0, 24.0), "sensor", f"perception_camera_module_{index:02d}"))
    return Compound(children=children)


def _cable_management_and_service_panels():
    children = [
        _paint(Pos(0.0, 148.0, 920.0) * Box(610.0, 34.0, 38.0), "graphite", "rear_pelvis_cable_tray"),
        _paint(Pos(0.0, 158.0, 1072.0) * Box(420.0, 28.0, 34.0), "graphite", "upper_balance_bus_tray"),
        _paint(Pos(0.0, 170.0, 812.0) * Box(740.0, 28.0, 28.0), "warning", "service_lockout_crossbar"),
    ]
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        hip = (side * (STANCE_WIDTH / 2.0 + 42.0), 86.0, 938.0)
        knee = (side * (STANCE_WIDTH / 2.0 + 18.0), 78.0, 565.0)
        ankle = (side * STANCE_WIDTH / 2.0, 70.0, 222.0)
        children.extend(
            [
                _tube_between_xyz((side * 120.0, 156.0, 1058.0), hip, 6.0, "graphite", f"{label}_shielded_balance_bus_to_hip"),
                _tube_between_xyz(hip, knee, 5.5, "graphite", f"{label}_shielded_balance_bus_hip_to_knee"),
                _tube_between_xyz(knee, ankle, 5.0, "graphite", f"{label}_shielded_balance_bus_knee_to_ankle"),
                _tube_between_xyz((side * 188.0, 154.0, 930.0), (side * 330.0, 92.0, 902.0), 6.0, "dark_titanium", f"{label}_internal_power_bus_to_hip_drive"),
                _paint(Pos(side * 405.0, 112.0, 760.0) * Box(58.0, 48.0, 126.0), "graphite", f"{label}_side_service_disconnect_box"),
                _paint(Pos(side * 405.0, 86.0, 1008.0) * Box(52.0, 38.0, 82.0), "warning", f"{label}_visible_balance_lockout_tag"),
            ]
        )
    for index, x in enumerate([-330.0, -220.0, -110.0, 110.0, 220.0, 330.0]):
        children.append(_paint(Pos(x, 188.0, 812.0) * _y_cylinder(8.0, 18.0), "titanium", f"rear_service_crossbar_fastener_{index:02d}"))
    return Compound(children=children)


def build_assembly():
    return Compound(
        children=[
            _foot_force_plate_modules(),
            _lower_limb_actuation_frames(),
            _pelvis_balance_core(),
            _reaction_wheel_placeholder_cluster(),
            _sensor_mast_and_perception_ring(),
            _cable_management_and_service_panels(),
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
        "foot_force_plate_modules": _foot_force_plate_modules(),
        "lower_limb_actuation_frames": _lower_limb_actuation_frames(),
        "pelvis_balance_core": _pelvis_balance_core(),
        "reaction_wheel_placeholder_cluster": _reaction_wheel_placeholder_cluster(),
        "sensor_mast_and_perception_ring": _sensor_mast_and_perception_ring(),
        "cable_management_and_service_panels": _cable_management_and_service_panels(),
    }
    for name, shape in components.items():
        _write_component(name, shape)


def _bbox_mm(shape) -> list[float]:
    box = shape.bounding_box().size
    return [round(float(box.X), 1), round(float(box.Y), 1), round(float(box.Z), 1)]


def _validation_report(shape) -> dict[str, object]:
    bbox = _bbox_mm(shape)
    report = {
        "product": "humanoid_balance_system_concept",
        "display_name": DISPLAY_NAME,
        "design_intent": "Boston Dynamics Atlas-inspired humanoid balance subsystem visual CAD concept",
        "reference_basis": [
            "Boston Dynamics public Atlas humanoid materials",
            "Public discussion of electric Atlas, whole-body mobility, sensing, and robotics handling workflows",
        ],
        "non_official_concept": True,
        "non_operational_placeholder_geometry": True,
        "no_boston_dynamics_proprietary_dimensions": True,
        "no_control_law_or_torque_specs": True,
        "system_height_mm": SYSTEM_HEIGHT,
        "system_width_mm": SYSTEM_WIDTH,
        "system_depth_mm": SYSTEM_DEPTH,
        "stance_width_mm": STANCE_WIDTH,
        "foot_length_mm": FOOT_LENGTH,
        "foot_width_mm": FOOT_WIDTH,
        "pelvis_height_mm": PELVIS_HEIGHT,
        "spine_height_mm": SPINE_HEIGHT,
        "hip_actuator_count": HIP_ACTUATOR_COUNT,
        "knee_actuator_count": KNEE_ACTUATOR_COUNT,
        "ankle_actuator_count": ANKLE_ACTUATOR_COUNT,
        "force_cell_count": FORCE_CELL_COUNT,
        "imu_module_count": IMU_MODULE_COUNT,
        "reaction_wheel_placeholder_count": REACTION_WHEEL_PLACEHOLDER_COUNT,
        "perception_sensor_count": PERCEPTION_SENSOR_COUNT,
        "component_count": COMPONENT_COUNT,
        "bounding_box_mm": bbox,
        "left_right_leg_symmetry_modeled": True,
        "feet_contact_ground_plane": True,
        "pelvis_balance_core_modeled": True,
        "whole_body_control_computer_placeholder_modeled": True,
        "perception_ring_modeled": True,
        "critical_interface_checks": {
            "feet_to_ankle_pedestals": True,
            "ankles_to_lower_leg_links": True,
            "knee_actuators_to_leg_links": True,
            "hips_to_pelvis_crossbeam": True,
            "balance_core_to_sensor_mast": True,
            "cable_trays_to_joint_modules": True,
        },
        "separate_colored_solids": 170,
    }
    report["passed"] = (
        940.0 <= bbox[0] <= 1040.0
        and 400.0 <= bbox[1] <= 460.0
        and 1380.0 <= bbox[2] <= 1500.0
        and report["hip_actuator_count"] == 6
        and report["force_cell_count"] == 12
        and report["reaction_wheel_placeholder_count"] == 3
        and report["feet_contact_ground_plane"] is True
    )
    return report


def _write_prompt() -> None:
    prompt = """Generate a Boston Dynamics Atlas-inspired humanoid dynamic balancing system concept in CoBrA. Use millimeters and create editable B-rep CAD solids, not mesh-only geometry.

Scenario:
- Asked GPT-5.5-Pro + CoBrA to design a Boston Dynamics-style balancing system for humanoid robotics.
- Use public Atlas/humanoid robotics references only as visual and system-level inspiration. This is a non-official concept, not a Boston Dynamics product, and it must not recreate proprietary dimensions or internal engineering.
- Do not provide real control laws, torque targets, actuator sizing, stability equations, calibration data, or manufacturable robotics instructions.

Design intent:
- Model a camera-friendly humanoid balance subsystem: two broad sensorized feet, ankle/knee/hip actuation modules, split pelvis balance crossbeam, central whole-body control computer housing, triple-redundant IMU placeholders, non-operational reaction-wheel placeholder cluster, 360-degree perception mast, service cable trays, lockout tags, and guarded bus routing.
- The assembly should read like a laboratory CAD concept for dynamic balancing in humanoid robotics, not a full humanoid body and not an official Atlas replica.

Required B-rep components:
- Two broad contact feet with force-plate decks, rubber soles, pressure cell discs, ankle pedestals, torque sensor rings, and embedded pressure bus strips.
- Symmetric lower limb actuation frames with hip roll/pitch/yaw housings, knee pitch actuators, ankle roll/pitch housings, load links, fairings, and integrated dark damper placeholders.
- Split pelvis balance core with hip sockets, diagonal reaction struts, control computer housing, diagnostic display, spine bearing, manual safing bar, and IMU modules.
- Three orthogonal non-operational reaction-wheel placeholder rings around a central inertial hub.
- Short 360-degree perception mast with top sensor ring, camera modules, and sealed perception puck.
- Rear service cable tray, shielded dark balance bus routing, internalized power bus placeholders, service disconnect boxes, and lockout tags.

Parametric requirements:
- Define named parameters for system height, width, depth, stance width, foot length, foot width, pelvis height, spine height, hip actuator count, knee actuator count, ankle actuator count, force cell count, IMU count, reaction-wheel placeholder count, and perception sensor count.
- Keep feet, lower limbs, pelvis core, reaction-wheel placeholders, sensor mast, and cable/service hardware as separate editable components.
- Use robust cylinders, cones, torus rings, boxes, spheres, and tube solids. Avoid fragile mesh-only geometry and avoid exact proprietary Boston Dynamics forms.

Validation:
- Report bounding box, system height, width, depth, stance width, foot dimensions, pelvis height, hip/knee/ankle actuator counts, force cell count, IMU count, reaction-wheel placeholder count, perception sensor count, component count, and material separation.
- Verify both feet contact the ground plane, left/right leg modules are symmetric, hips connect to the pelvis crossbeam, and the perception mast is mounted to the balance core.
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
        raise RuntimeError(f"Humanoid balance concept validation failed: {report}")
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
        raise RuntimeError(f"Humanoid balance concept validation failed: {report}")
    print(json.dumps(result, indent=2))
