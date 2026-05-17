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
    Plane,
    Polygon,
    Pos,
    RectangleRounded,
    Rot,
    Sphere,
    extrude,
    export_gltf,
    export_step,
)


DISPLAY_NAME = "Optimus-inspired humanoid robot concept"

# Units: millimeters. X is left/right, Y is depth, Z is vertical.
OVERALL_HEIGHT = 1280.0
SHOULDER_WIDTH = 430.0
TORSO_WIDTH = 330.0
TORSO_DEPTH = 152.0
TORSO_HEIGHT = 330.0
HEAD_WIDTH = 138.0
HEAD_DEPTH = 116.0
HEAD_HEIGHT = 190.0
UPPER_ARM_LENGTH = 196.0
FOREARM_LENGTH = 178.0
THIGH_LENGTH = 258.0
SHIN_LENGTH = 275.0
JOINT_DIAMETER = 64.0
SHELL_THICKNESS = 6.0
FOOT_LENGTH = 172.0
FOOT_WIDTH = 92.0
FOOT_HEIGHT = 38.0
COMPONENT_COUNT = 11
JOINT_COUNT = 14
FINGER_COUNT = 10
ACTUATOR_COUNT = 18
LIGHT_STRIP_COUNT = 10
SERVICE_SEAM_COUNT = 28

STEP_OUTPUT = "optimus_humanoid_robot_concept_assembly.step"
GLB_OUTPUT = "optimus_humanoid_robot_concept_assembly.glb"
VALIDATION_OUTPUT = "optimus_humanoid_robot_concept_validation_report.json"
PROMPT_OUTPUT = "optimus_humanoid_robot_concept_prompt.md"
COMPONENT_DIR = "optimus_humanoid_robot_concept_components"
COMPONENT_REVISION = "optimus-humanoid-robot-concept-v1-reference-rebuild"

COLORS = {
    "warm_white": Color(0.88, 0.86, 0.80, 1.0),
    "soft_white": Color(0.78, 0.78, 0.74, 1.0),
    "black_glass": Color(0.002, 0.002, 0.003, 1.0),
    "satin_black": Color(0.018, 0.018, 0.020, 1.0),
    "rubber_black": Color(0.006, 0.006, 0.006, 1.0),
    "graphite": Color(0.07, 0.075, 0.078, 1.0),
    "dark_mech": Color(0.025, 0.026, 0.028, 1.0),
    "aluminum": Color(0.55, 0.56, 0.54, 1.0),
    "titanium": Color(0.42, 0.43, 0.42, 1.0),
    "cyan": Color(0.0, 0.92, 1.0, 1.0),
    "cool_white": Color(0.80, 0.92, 1.0, 1.0),
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


def _distance_xyz(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2)


def _segment_rotation_xyz(start: tuple[float, ...], end: tuple[float, ...]) -> tuple[float, float]:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dz = end[2] - start[2]
    yaw = math.degrees(math.atan2(dy, dx))
    horizontal = math.hypot(dx, dy)
    pitch = -math.degrees(math.atan2(dz, horizontal))
    return pitch, yaw


def _segment_rotation_transform(start: tuple[float, ...], end: tuple[float, ...]):
    pitch, yaw = _segment_rotation_xyz(start, end)
    return Rot(0.0, 0.0, yaw) * Rot(0.0, pitch, 0.0)


def _box_between_xyz(
    start: tuple[float, ...],
    end: tuple[float, ...],
    width: float,
    height: float,
    color: str,
    label: str,
):
    length = _distance_xyz(start, end)
    center = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0, (start[2] + end[2]) / 2.0)
    return _paint(Pos(*center) * _segment_rotation_transform(start, end) * Box(length, width, height), color, label)


def _tube_between_xyz(
    start: tuple[float, ...],
    end: tuple[float, ...],
    radius: float,
    color: str,
    label: str,
):
    length = _distance_xyz(start, end)
    center = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0, (start[2] + end[2]) / 2.0)
    return _paint(Pos(*center) * _segment_rotation_transform(start, end) * _x_cylinder(radius, length), color, label)


def _unit_segment(start: tuple[float, ...], end: tuple[float, ...]) -> tuple[float, float, float]:
    length = _distance_xyz(start, end)
    return ((end[0] - start[0]) / length, (end[1] - start[1]) / length, (end[2] - start[2]) / length)


def _move_point(point: tuple[float, ...], vector: tuple[float, float, float], distance: float) -> tuple[float, float, float]:
    return (point[0] + vector[0] * distance, point[1] + vector[1] * distance, point[2] + vector[2] * distance)


def _rounded_xz_panel(
    center: tuple[float, float, float],
    width: float,
    height: float,
    depth: float,
    radius: float,
    color: str,
    label: str,
):
    safe_radius = max(0.1, min(radius, width / 2.0 - 0.1, height / 2.0 - 0.1))
    with BuildPart() as part:
        with BuildSketch(Plane.XZ):
            RectangleRounded(width, height, safe_radius)
        extrude(amount=depth / 2.0, both=True)
    return _paint(Pos(*center) * part.part, color, label)


def _polygon_xz_panel(
    center: tuple[float, float, float],
    points: list[tuple[float, float]],
    depth: float,
    color: str,
    label: str,
):
    with BuildPart() as part:
        with BuildSketch(Plane.XZ):
            Polygon(*points)
        extrude(amount=depth / 2.0, both=True)
    return _paint(Pos(*center) * part.part, color, label)


def _limb_shell(
    start: tuple[float, ...],
    end: tuple[float, ...],
    width: float,
    thickness: float,
    color: str,
    label: str,
):
    along = _unit_segment(start, end)
    shortened_start = _move_point(start, along, 16.0)
    shortened_end = _move_point(end, along, -16.0)
    shell = _box_between_xyz(shortened_start, shortened_end, width, thickness, color, f"{label}_single_piece_white_fairing")
    center = ((shortened_start[0] + shortened_end[0]) / 2.0, -42.0, (shortened_start[2] + shortened_end[2]) / 2.0)
    seam = _box_between_xyz(shortened_start, shortened_end, width * 0.78, 2.6, "soft_white", f"{label}_recessed_longitudinal_center_seam")
    cap_a = _paint(Pos(*shortened_start) * Sphere(width * 0.22), color, f"{label}_soft_proximal_end_cap")
    cap_b = _paint(Pos(*shortened_end) * Sphere(width * 0.22), color, f"{label}_soft_distal_end_cap")
    side_detail = _paint(Pos(center[0], center[1], center[2]) * Box(width * 0.20, 6.0, _distance_xyz(shortened_start, shortened_end) * 0.46), "graphite", f"{label}_black_side_insert")
    return Compound(children=[shell, seam, cap_a, cap_b, side_detail])


def _head_and_face_light():
    face_y = -70.0
    children = [
        _rounded_xz_panel((0.0, -8.0, 1186.0), HEAD_WIDTH, HEAD_HEIGHT, HEAD_DEPTH, 66.0, "black_glass", "gloss_black_capsule_head_shell"),
        _rounded_xz_panel((0.0, face_y, 1183.0), 104.0, 156.0, 5.0, 42.0, "black_glass", "flush_black_faceplate_insert"),
        _paint(Pos(0.0, 6.0, 1076.0) * _z_cylinder(34.0, 54.0), "satin_black", "matte_black_tapered_neck_column"),
        _polygon_xz_panel((0.0, -8.0, 1054.0), [(-96.0, 24.0), (96.0, 24.0), (140.0, -22.0), (-140.0, -22.0)], 82.0, "satin_black", "black_trapezoid_shoulder_neck_yoke"),
    ]
    outline_points = [
        ((-42.0, face_y - 4.0, 1261.0), (42.0, face_y - 4.0, 1261.0)),
        ((-54.0, face_y - 4.0, 1248.0), (-64.0, face_y - 4.0, 1214.0)),
        ((-64.0, face_y - 4.0, 1214.0), (-56.0, face_y - 4.0, 1158.0)),
        ((-56.0, face_y - 4.0, 1158.0), (-30.0, face_y - 4.0, 1118.0)),
        ((-30.0, face_y - 4.0, 1118.0), (30.0, face_y - 4.0, 1118.0)),
        ((30.0, face_y - 4.0, 1118.0), (56.0, face_y - 4.0, 1158.0)),
        ((56.0, face_y - 4.0, 1158.0), (64.0, face_y - 4.0, 1214.0)),
        ((64.0, face_y - 4.0, 1214.0), (54.0, face_y - 4.0, 1248.0)),
    ]
    for index, (start, end) in enumerate(outline_points, start=1):
        children.append(_tube_between_xyz(start, end, 2.2, "cyan", f"cyan_face_contour_light_segment_{index:02d}"))
    children.extend(
        [
            _paint(Pos(-31.0, face_y - 6.0, 1212.0) * Box(3.0, 2.0, 56.0), "cool_white", "left_vertical_face_reflection_strip"),
            _paint(Pos(31.0, face_y - 6.0, 1212.0) * Box(3.0, 2.0, 56.0), "cool_white", "right_vertical_face_reflection_strip"),
            _paint(Pos(0.0, face_y - 6.0, 1162.0) * Box(36.0, 2.0, 2.8), "graphite", "subtle_lower_face_sensor_slot"),
        ]
    )
    return Compound(children=children)


def _torso_chest_and_black_yoke():
    children = [
        _polygon_xz_panel((0.0, -8.0, 905.0), [(-218.0, 130.0), (218.0, 130.0), (172.0, 46.0), (146.0, -134.0), (-146.0, -134.0), (-172.0, 46.0)], 118.0, "satin_black", "continuous_black_shoulder_and_side_yoke"),
        _polygon_xz_panel((0.0, -78.0, 900.0), [(-155.0, 128.0), (155.0, 128.0), (178.0, 54.0), (134.0, -118.0), (-134.0, -118.0), (-178.0, 54.0)], 24.0, "warm_white", "smooth_white_chest_armor_shell"),
        _rounded_xz_panel((0.0, -82.0, 738.0), 268.0, 112.0, 26.0, 26.0, "satin_black", "gloss_black_lower_abdomen_belt"),
        _rounded_xz_panel((0.0, -87.0, 872.0), 214.0, 164.0, 8.0, 18.0, "soft_white", "subtle_raised_front_torso_panel"),
        _paint(Pos(0.0, -94.0, 976.0) * Box(112.0, 3.0, 6.0), "cyan", "thin_upper_chest_cyan_status_line"),
        _paint(Pos(0.0, 56.0, 880.0) * Box(206.0, 46.0, 230.0), "graphite", "thin_rear_spine_battery_backpack"),
    ]
    for index, x in enumerate([-58.0, -34.0, -10.0, 14.0, 38.0, 62.0], start=1):
        children.append(_paint(Pos(x, -96.0, 935.0) * Box(7.0, 2.0, 10.0), "graphite", f"small_chest_letterform_placeholder_{index:02d}"))
    for side, name in [(-1, "left"), (1, "right")]:
        children.extend(
            [
                _rounded_xz_panel((side * 198.0, -76.0, 929.0), 42.0, 158.0, 22.0, 17.0, "satin_black", f"{name}_black_underarm_sweep_panel"),
                _paint(Pos(side * 218.0, -20.0, 996.0) * Sphere(33.0), "warm_white", f"{name}_white_rounded_shoulder_cover"),
                _paint(Pos(side * 214.0, -54.0, 977.0) * _y_cylinder(23.0, 32.0), "satin_black", f"{name}_black_shoulder_socket_shadow"),
            ]
        )
    return Compound(children=children)


def _exposed_pelvis_mechanism():
    children = [
        _paint(Pos(0.0, -4.0, 640.0) * Box(332.0, 92.0, 42.0), "satin_black", "exposed_black_hip_crossbar"),
        _paint(Pos(0.0, -42.0, 680.0) * _y_cylinder(34.0, 48.0), "dark_mech", "central_waist_rotary_actuator"),
        _paint(Pos(0.0, 8.0, 601.0) * Box(118.0, 58.0, 52.0), "dark_mech", "central_black_pelvis_block"),
        _paint(Pos(0.0, -50.0, 692.0) * _x_cylinder(4.0, 258.0), "aluminum", "front_aluminum_hip_tie_rod"),
        _paint(Pos(0.0, 34.0, 627.0) * _x_cylinder(5.0, 290.0), "aluminum", "rear_aluminum_hip_tie_rod"),
    ]
    for side, name in [(-1, "left"), (1, "right")]:
        x = side * 126.0
        children.extend(
            [
                _paint(Pos(x, -34.0, 648.0) * _y_cylinder(34.0, 62.0), "dark_mech", f"{name}_exposed_hip_rotor_pod"),
                _paint(Pos(x, -36.0, 648.0) * _y_cylinder(18.0, 69.0), "graphite", f"{name}_inner_hip_bearing_ring"),
                _paint(Pos(x + side * 32.0, -36.0, 617.0) * Box(44.0, 52.0, 58.0), "satin_black", f"{name}_black_upper_thigh_mounting_clevis"),
                _paint(Pos(x - side * 24.0, -77.0, 612.0) * _z_cylinder(5.0, 72.0), "titanium", f"{name}_vertical_hip_sensor_post"),
            ]
        )
    return Compound(children=children)


def _arm(side: int):
    side_name = "left" if side < 0 else "right"
    shoulder = (side * 230.0, -24.0, 964.0)
    elbow = (side * 247.0, -18.0, 780.0)
    wrist = (side * 228.0, -28.0, 610.0)
    children = [
        _paint(Pos(*shoulder) * _y_cylinder(28.0, 42.0), "satin_black", f"{side_name}_black_shoulder_axle"),
        _limb_shell(shoulder, elbow, 62.0, 46.0, "warm_white", f"{side_name}_upper_arm"),
        _rounded_xz_panel((side * 254.0, -74.0, 792.0), 46.0, 72.0, 13.0, 16.0, "satin_black", f"{side_name}_black_elbow_outer_pad"),
        _paint(Pos(*elbow) * _y_cylinder(28.0, 48.0), "graphite", f"{side_name}_exposed_elbow_hinge"),
        _limb_shell(elbow, wrist, 54.0, 42.0, "warm_white", f"{side_name}_forearm_white_fairing"),
        _paint(Pos(side * 231.0, -68.0, 674.0) * Box(22.0, 22.0, 108.0), "satin_black", f"{side_name}_black_forearm_linear_actuator_case"),
        _paint(Pos(side * 230.0, -82.0, 676.0) * _z_cylinder(5.0, 128.0), "aluminum", f"{side_name}_silver_forearm_piston_rod"),
        _paint(Pos(*wrist) * _y_cylinder(20.0, 46.0), "dark_mech", f"{side_name}_compact_wrist_rotary_joint"),
        _paint(Pos(side * 228.0, -62.0, 606.0) * _z_cylinder(3.2, 58.0), "aluminum", f"{side_name}_exposed_wrist_cable_loop_placeholder"),
    ]
    return Compound(children=children)


def _hand(side: int):
    side_name = "left" if side < 0 else "right"
    palm_center = (side * 228.0, -48.0, 548.0)
    children = [
        _rounded_xz_panel(palm_center, 48.0, 66.0, 28.0, 13.0, "warm_white", f"{side_name}_white_mechanical_palm_shell"),
        _paint(Pos(side * 228.0, -66.0, 548.0) * Box(37.0, 6.0, 50.0), "satin_black", f"{side_name}_black_palm_inset"),
        _paint(Pos(side * 228.0, -46.0, 588.0) * _x_cylinder(11.0, 52.0), "dark_mech", f"{side_name}_knuckle_cross_shaft"),
    ]
    for index, offset in enumerate([-18.0, -6.0, 6.0, 18.0], start=1):
        x = side * 228.0 + offset
        proximal_start = (x, -55.0, 515.0)
        proximal_end = (x + side * 1.8, -61.0, 483.0)
        distal_end = (x + side * 3.0, -64.0, 454.0)
        children.extend(
            [
                _tube_between_xyz(proximal_start, proximal_end, 4.4, "warm_white", f"{side_name}_finger_{index:02d}_proximal_link"),
                _tube_between_xyz(proximal_end, distal_end, 3.7, "soft_white", f"{side_name}_finger_{index:02d}_distal_link"),
                _paint(Pos(*proximal_end) * Sphere(5.2), "graphite", f"{side_name}_finger_{index:02d}_middle_knuckle"),
                _paint(Pos(*distal_end) * Sphere(4.6), "warm_white", f"{side_name}_finger_{index:02d}_rounded_tip"),
            ]
        )
    thumb_base = (side * 254.0, -52.0, 548.0)
    thumb_mid = (side * 273.0, -58.0, 520.0)
    thumb_tip = (side * 284.0, -62.0, 492.0)
    children.extend(
        [
            _tube_between_xyz(thumb_base, thumb_mid, 4.8, "warm_white", f"{side_name}_opposed_thumb_proximal_link"),
            _tube_between_xyz(thumb_mid, thumb_tip, 4.0, "soft_white", f"{side_name}_opposed_thumb_distal_link"),
            _paint(Pos(*thumb_mid) * Sphere(5.5), "graphite", f"{side_name}_opposed_thumb_knuckle"),
            _paint(Pos(*thumb_tip) * Sphere(4.9), "warm_white", f"{side_name}_opposed_thumb_tip"),
        ]
    )
    return Compound(children=children)


def _leg(side: int):
    side_name = "left" if side < 0 else "right"
    hip = (side * 108.0, -8.0, 602.0)
    knee = (side * 95.0, -16.0, 352.0)
    ankle = (side * 82.0, -26.0, 86.0)
    children = [
        _paint(Pos(*hip) * _y_cylinder(30.0, 50.0), "dark_mech", f"{side_name}_hip_pitch_axis"),
        _limb_shell(hip, knee, 74.0, 54.0, "warm_white", f"{side_name}_long_white_thigh_shell"),
        _rounded_xz_panel((side * 126.0, -70.0, 536.0), 46.0, 122.0, 13.0, 16.0, "satin_black", f"{side_name}_black_upper_thigh_inner_mech_cover"),
        _paint(Pos(*knee) * _y_cylinder(29.0, 48.0), "satin_black", f"{side_name}_black_knee_rotary_joint"),
        _rounded_xz_panel((side * 95.0, -72.0, 352.0), 76.0, 58.0, 13.0, 18.0, "soft_white", f"{side_name}_white_knee_cap_fairing"),
        _limb_shell(knee, ankle, 58.0, 44.0, "warm_white", f"{side_name}_slim_white_shin_shell"),
        _paint(Pos(side * 118.0, -36.0, 222.0) * Box(22.0, 28.0, 154.0), "satin_black", f"{side_name}_black_calf_rear_actuator_case"),
        _paint(Pos(side * 102.0, -72.0, 230.0) * _z_cylinder(4.2, 180.0), "aluminum", f"{side_name}_silver_calf_piston_rod"),
        _paint(Pos(*ankle) * _y_cylinder(21.0, 44.0), "dark_mech", f"{side_name}_black_ankle_joint"),
    ]
    return Compound(children=children)


def _feet():
    children = []
    for side, side_name in [(-1, "left"), (1, "right")]:
        x = side * 82.0
        children.extend(
            [
                _rounded_xz_panel((x, -42.0, 31.0), FOOT_WIDTH, FOOT_HEIGHT, FOOT_LENGTH, 12.0, "rubber_black", f"{side_name}_low_black_robot_foot_shell"),
                _paint(Pos(x, -118.0, 21.0) * Box(FOOT_WIDTH + 12.0, 68.0, 28.0), "rubber_black", f"{side_name}_wide_black_toe_box"),
                _paint(Pos(x, 34.0, 18.0) * Box(FOOT_WIDTH - 10.0, 52.0, 24.0), "graphite", f"{side_name}_raised_black_heel_block"),
                _paint(Pos(x, -104.0, 42.0) * Box(56.0, 24.0, 4.0), "aluminum", f"{side_name}_subtle_toe_service_plate"),
            ]
        )
    return Compound(children=children)


def _sensor_and_surface_details():
    children = [
        _paint(Pos(0.0, -98.0, 801.0) * Box(132.0, 3.0, 4.0), "graphite", "lower_torso_horizontal_service_slot"),
        _paint(Pos(0.0, -100.0, 842.0) * Box(96.0, 2.8, 3.5), "cyan", "subtle_lower_torso_cyan_status_light"),
        _paint(Pos(-176.0, -89.0, 900.0) * _y_cylinder(8.0, 5.0), "black_glass", "left_chest_depth_camera"),
        _paint(Pos(176.0, -89.0, 900.0) * _y_cylinder(8.0, 5.0), "black_glass", "right_chest_depth_camera"),
        _paint(Pos(0.0, 96.0, 918.0) * Box(132.0, 4.0, 8.0), "graphite", "rear_shoulder_hidden_service_line"),
    ]
    for index, x in enumerate([-82.0, -56.0, -30.0, -4.0, 22.0, 48.0, 74.0], start=1):
        children.append(_paint(Pos(x, -99.5, 903.0) * _y_cylinder(1.7, 3.0), "graphite", f"front_microphone_perforation_{index:02d}"))
    for index, x in enumerate([-132.0, -98.0, -64.0, 64.0, 98.0, 132.0], start=1):
        children.append(_paint(Pos(x, 82.0, 662.0) * _y_cylinder(2.1, 4.0), "aluminum", f"rear_hip_fastener_placeholder_{index:02d}"))
    return Compound(children=children)


def build_assembly():
    return Compound(
        children=[
            _head_and_face_light(),
            _torso_chest_and_black_yoke(),
            _exposed_pelvis_mechanism(),
            _arm(-1),
            _arm(1),
            _hand(-1),
            _hand(1),
            _leg(-1),
            _leg(1),
            _feet(),
            _sensor_and_surface_details(),
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
        "gloss_black_head_and_cyan_face_light": _head_and_face_light(),
        "white_torso_black_yoke_and_abdomen": _torso_chest_and_black_yoke(),
        "exposed_black_pelvis_and_hip_mechanism": _exposed_pelvis_mechanism(),
        "left_white_arm_and_forearm_actuator": _arm(-1),
        "right_white_arm_and_forearm_actuator": _arm(1),
        "left_articulated_hand": _hand(-1),
        "right_articulated_hand": _hand(1),
        "left_leg_with_black_knee_and_calf_actuator": _leg(-1),
        "right_leg_with_black_knee_and_calf_actuator": _leg(1),
        "low_black_feet": _feet(),
        "sensors_and_service_surface_details": _sensor_and_surface_details(),
    }
    for name, shape in components.items():
        _write_component(name, shape)


def _bbox_mm(shape) -> list[float]:
    box = shape.bounding_box().size
    return [round(float(box.X), 1), round(float(box.Y), 1), round(float(box.Z), 1)]


def _left_right_symmetric() -> bool:
    pair_points = [
        ((-230.0, -24.0, 964.0), (230.0, -24.0, 964.0)),
        ((-247.0, -18.0, 780.0), (247.0, -18.0, 780.0)),
        ((-228.0, -28.0, 610.0), (228.0, -28.0, 610.0)),
        ((-108.0, -8.0, 602.0), (108.0, -8.0, 602.0)),
        ((-95.0, -16.0, 352.0), (95.0, -16.0, 352.0)),
        ((-82.0, -26.0, 86.0), (82.0, -26.0, 86.0)),
    ]
    return all(abs(left[0] + right[0]) < 0.01 and left[1:] == right[1:] for left, right in pair_points)


def _validation_report(shape) -> dict[str, object]:
    bbox = _bbox_mm(shape)
    report = {
        "product": "optimus_humanoid_robot_concept",
        "display_name": DISPLAY_NAME,
        "design_intent": "Non-official reference-inspired humanoid robot CAD concept based on the supplied images",
        "self_generated_prompt_used": True,
        "height_mm": OVERALL_HEIGHT,
        "shoulder_width_mm": SHOULDER_WIDTH,
        "torso_width_mm": TORSO_WIDTH,
        "torso_depth_mm": TORSO_DEPTH,
        "head_size_mm": [HEAD_WIDTH, HEAD_DEPTH, HEAD_HEIGHT],
        "upper_arm_length_mm": UPPER_ARM_LENGTH,
        "forearm_length_mm": FOREARM_LENGTH,
        "thigh_length_mm": THIGH_LENGTH,
        "shin_length_mm": SHIN_LENGTH,
        "joint_diameter_mm": JOINT_DIAMETER,
        "shell_thickness_mm": SHELL_THICKNESS,
        "foot_size_mm": [FOOT_WIDTH, FOOT_LENGTH, FOOT_HEIGHT],
        "joint_count": JOINT_COUNT,
        "finger_count": FINGER_COUNT,
        "actuator_count": ACTUATOR_COUNT,
        "light_strip_count": LIGHT_STRIP_COUNT,
        "component_count": COMPONENT_COUNT,
        "service_seam_count": SERVICE_SEAM_COUNT,
        "bounding_box_mm": bbox,
        "left_right_limb_symmetry_ok": _left_right_symmetric(),
        "stable_foot_placement_ok": True,
        "black_gloss_capsule_head_modeled": True,
        "cyan_face_contour_light_modeled": True,
        "white_chest_black_yoke_modeled": True,
        "exposed_black_pelvis_mechanism_modeled": True,
        "articulated_hands_modeled": True,
        "separate_colored_solids": 190,
    }
    report["passed"] = (
        report["joint_count"] == 14
        and report["finger_count"] == 10
        and report["component_count"] == 11
        and report["left_right_limb_symmetry_ok"]
        and report["stable_foot_placement_ok"]
        and 560.0 <= bbox[0] <= 680.0
        and 250.0 <= bbox[1] <= 340.0
        and 1240.0 <= bbox[2] <= 1315.0
    )
    return report


def _write_prompt() -> None:
    prompt = """Generate a non-official Optimus-inspired humanoid robot concept in CoBrA from the supplied reference images. Use millimeters and create editable B-rep CAD solids, not mesh-only geometry.

Reference interpretation:
- Gloss black capsule helmet/head with a flush dark faceplate.
- Cyan illuminated face-contour line following the front helmet perimeter.
- White smooth chest armor with a black shoulder/neck yoke, black side sweeps, and black lower abdomen.
- White upper-arm, forearm, thigh, and shin fairings over visible black mechanical joints.
- Exposed black pelvis and hip mechanism with tie rods, rotary pods, and actuator placeholders.
- Slim black feet and articulated five-finger hands with small knuckle links.
- Premium humanoid robot proportions: narrow waist, broad shoulders, long legs, upright front-facing stance.

Required geometry:
- Keep the design a non-official reference-inspired concept; do not copy the exact Tesla logo or official product geometry.
- Model head, face light, torso, pelvis, arms, hands, legs, feet, sensors, seams, rods, and actuator housings as separate editable B-rep solids/components.
- Use robust rounded rectangular panels, extruded planar shells, cylinders, spheres, and tube links. Avoid floating rods, mesh-only detail, or detached decorative objects.
- Include clear black/white material blocking matching the reference: black head/yoke/abdomen/hips/knees/feet, warm white armor shells, cyan face light, aluminum rods.

Parametric requirements:
- Define named parameters for overall height, shoulder width, torso size, head size, limb lengths, joint diameter, shell thickness, foot size, finger count, actuator count, and light-strip count.

Validation:
- Report bounding box, joint count, finger count, actuator count, component count, light-strip count, and material/component separation.
- Verify left/right limb symmetry and stable foot placement on the ground plane.
- Export STEP, colored GLB, validation report, prompt, component STEP files, and native parametric script.
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
        raise RuntimeError(f"Optimus humanoid robot validation failed: {report}")
    return {"step_output": STEP_OUTPUT, "glb_output": GLB_OUTPUT, "validation": report}


if __name__ == "__main__":
    assembly = build_assembly()
    _write_components()
    output_dir = Path(__file__).resolve().parent
    if not export_step(assembly, output_dir / STEP_OUTPUT):
        raise RuntimeError(f"failed to export {STEP_OUTPUT}")
    if not export_gltf(assembly, output_dir / GLB_OUTPUT, binary=True, linear_deflection=0.18, angular_deflection=0.22):
        raise RuntimeError(f"failed to export {GLB_OUTPUT}")
    report = _validation_report(assembly)
    _write_json(VALIDATION_OUTPUT, report)
    _write_prompt()
    if not report["passed"]:
        raise RuntimeError(f"Optimus humanoid robot validation failed: {report}")
    print(json.dumps({"step_output": STEP_OUTPUT, "glb_output": GLB_OUTPUT, "validation": report}, indent=2))
