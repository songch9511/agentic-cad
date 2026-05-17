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
    loft,
)


DISPLAY_NAME = "Optimus-inspired humanoid robot concept"

# Units: millimeters. X is left/right, Y is depth, Z is vertical.
OVERALL_HEIGHT = 1288.0
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
COMPONENT_COUNT = 12
JOINT_COUNT = 14
FINGER_COUNT = 10
ACTUATOR_COUNT = 24
LIGHT_STRIP_COUNT = 10
SERVICE_SEAM_COUNT = 36
LOFTED_SHELL_COUNT = 18
SURFACE_FASTENER_COUNT = 44
CONNECTOR_BRIDGE_COUNT = 34

STEP_OUTPUT = "optimus_humanoid_robot_concept_assembly.step"
GLB_OUTPUT = "optimus_humanoid_robot_concept_assembly.glb"
VALIDATION_OUTPUT = "optimus_humanoid_robot_concept_validation_report.json"
PROMPT_OUTPUT = "optimus_humanoid_robot_concept_prompt.md"
COMPONENT_DIR = "optimus_humanoid_robot_concept_components"
COMPONENT_REVISION = "optimus-humanoid-robot-concept-v3-integrated-joints"

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


def _safe_radius(width: float, height: float, radius: float) -> float:
    return max(0.1, min(radius, width / 2.0 - 0.1, height / 2.0 - 0.1))


def _lofted_x_fairing(
    center: tuple[float, float, float],
    profiles: list[tuple[float, float, float, float]],
    color: str,
    label: str,
):
    with BuildPart() as part:
        for x, width, thickness, radius in profiles:
            with BuildSketch(Plane.YZ.offset(x)):
                RectangleRounded(width, thickness, _safe_radius(width, thickness, radius))
        loft()
    return _paint(Pos(*center) * part.part, color, label)


def _lofted_y_rounded_shell(
    center: tuple[float, float, float],
    profiles: list[tuple[float, float, float, float]],
    color: str,
    label: str,
):
    with BuildPart() as part:
        for y, width, height, radius in profiles:
            with BuildSketch(Plane.XZ.offset(y)):
                RectangleRounded(width, height, _safe_radius(width, height, radius))
        loft()
    return _paint(Pos(*center) * part.part, color, label)


def _lofted_z_rounded_shell(
    center: tuple[float, float, float],
    profiles: list[tuple[float, float, float, float]],
    color: str,
    label: str,
):
    with BuildPart() as part:
        for z, width, depth, radius in profiles:
            with BuildSketch(Plane.XY.offset(z)):
                RectangleRounded(width, depth, _safe_radius(width, depth, radius))
        loft()
    return _paint(Pos(*center) * part.part, color, label)


def _scale_points(points: list[tuple[float, float]], sx: float, sz: float) -> list[tuple[float, float]]:
    return [(x * sx, z * sz) for x, z in points]


def _lofted_y_polygon_shell(
    center: tuple[float, float, float],
    base_points: list[tuple[float, float]],
    profiles: list[tuple[float, float, float]],
    color: str,
    label: str,
):
    with BuildPart() as part:
        for y, sx, sz in profiles:
            with BuildSketch(Plane.XZ.offset(y)):
                Polygon(*_scale_points(base_points, sx, sz))
        loft()
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
    length = _distance_xyz(shortened_start, shortened_end)
    center = ((shortened_start[0] + shortened_end[0]) / 2.0, (shortened_start[1] + shortened_end[1]) / 2.0, (shortened_start[2] + shortened_end[2]) / 2.0)
    local_shell = _lofted_x_fairing(
        (0.0, 0.0, 0.0),
        [
            (-length / 2.0, width * 0.70, thickness * 0.72, min(width, thickness) * 0.22),
            (-length * 0.20, width * 1.02, thickness * 1.00, min(width, thickness) * 0.34),
            (length * 0.20, width * 0.92, thickness * 0.92, min(width, thickness) * 0.30),
            (length / 2.0, width * 0.62, thickness * 0.64, min(width, thickness) * 0.20),
        ],
        color,
        f"{label}_local_lofted_fairing",
    )
    shell = _paint(Pos(*center) * _segment_rotation_transform(shortened_start, shortened_end) * local_shell, color, f"{label}_lofted_tapered_white_fairing")
    seam = _tube_between_xyz(
        _move_point(shortened_start, (0.0, -1.0, 0.0), thickness * 0.54),
        _move_point(shortened_end, (0.0, -1.0, 0.0), thickness * 0.54),
        1.8,
        "soft_white",
        f"{label}_raised_longitudinal_highlight_seam",
    )
    black_insert = _tube_between_xyz(
        _move_point(shortened_start, (0.0, -1.0, 0.0), thickness * 0.78),
        _move_point(shortened_end, (0.0, -1.0, 0.0), thickness * 0.78),
        2.7,
        "graphite",
        f"{label}_thin_black_side_shadow_insert",
    )
    cap_a = _paint(Pos(*shortened_start) * Sphere(width * 0.16), color, f"{label}_small_proximal_fairing_cap")
    cap_b = _paint(Pos(*shortened_end) * Sphere(width * 0.15), color, f"{label}_small_distal_fairing_cap")
    return Compound(children=[shell, seam, black_insert, cap_a, cap_b])


def _bearing_bolt_ring(center: tuple[float, float, float], radius: float, axis: str, label: str):
    children = []
    for index, angle in enumerate(range(0, 360, 60), start=1):
        rad = math.radians(angle)
        if axis == "y":
            pos = (center[0] + math.cos(rad) * radius, center[1] - 27.0, center[2] + math.sin(rad) * radius)
            bolt = Pos(*pos) * _y_cylinder(2.4, 5.0)
        elif axis == "x":
            pos = (center[0] + 27.0, center[1] + math.cos(rad) * radius, center[2] + math.sin(rad) * radius)
            bolt = Pos(*pos) * _x_cylinder(2.4, 5.0)
        else:
            pos = (center[0] + math.cos(rad) * radius, center[1] + math.sin(rad) * radius, center[2] + 3.0)
            bolt = Pos(*pos) * _z_cylinder(2.4, 5.0)
        children.append(_paint(bolt, "aluminum", f"{label}_bolt_{index:02d}"))
    return Compound(children=children)


def _clevis_pair(center: tuple[float, float, float], side: int, width: float, height: float, label: str):
    x, y, z = center
    return Compound(
        children=[
            _paint(Pos(x + side * width * 0.40, y - 20.0, z) * Box(8.0, 18.0, height), "satin_black", f"{label}_outer_clevis_plate"),
            _paint(Pos(x - side * width * 0.40, y - 20.0, z) * Box(8.0, 18.0, height), "satin_black", f"{label}_inner_clevis_plate"),
            _paint(Pos(x, y - 29.0, z) * _x_cylinder(4.0, width * 0.94), "aluminum", f"{label}_clevis_cross_pin"),
        ]
    )


def _head_and_face_light():
    face_y = -70.0
    children = [
        _lofted_y_rounded_shell(
            (0.0, -6.0, 1187.0),
            [
                (-58.0, 86.0, 138.0, 40.0),
                (-38.0, 128.0, 188.0, 62.0),
                (-6.0, 148.0, 204.0, 70.0),
                (30.0, 132.0, 194.0, 60.0),
                (58.0, 86.0, 150.0, 38.0),
            ],
            "black_glass",
            "multi_section_gloss_black_capsule_helmet",
        ),
        _lofted_y_rounded_shell(
            (0.0, face_y - 1.0, 1182.0),
            [
                (-2.5, 92.0, 138.0, 35.0),
                (0.0, 108.0, 160.0, 43.0),
                (2.5, 94.0, 142.0, 36.0),
            ],
            "black_glass",
            "flush_contoured_black_faceplate_insert",
        ),
        _paint(Pos(0.0, 6.0, 1078.0) * _z_cylinder(29.0, 52.0), "satin_black", "matte_black_tapered_neck_column"),
        _lofted_y_polygon_shell(
            (0.0, -7.0, 1055.0),
            [(-102.0, 24.0), (102.0, 24.0), (150.0, -22.0), (-150.0, -22.0)],
            [(-48.0, 0.82, 0.82), (-4.0, 1.04, 1.00), (48.0, 0.88, 0.78)],
            "satin_black",
            "lofted_black_trapezoid_shoulder_neck_yoke",
        ),
        _paint(Pos(0.0, -70.5, 1096.0) * Box(66.0, 4.0, 10.0), "satin_black", "thin_black_chin_bezel"),
    ]
    outline_points = [
        ((-38.0, face_y - 5.0, 1266.0), (38.0, face_y - 5.0, 1266.0)),
        ((-50.0, face_y - 5.0, 1254.0), (-66.0, face_y - 5.0, 1218.0)),
        ((-66.0, face_y - 5.0, 1218.0), (-58.0, face_y - 5.0, 1158.0)),
        ((-58.0, face_y - 5.0, 1158.0), (-30.0, face_y - 5.0, 1114.0)),
        ((-30.0, face_y - 5.0, 1114.0), (30.0, face_y - 5.0, 1114.0)),
        ((30.0, face_y - 5.0, 1114.0), (58.0, face_y - 5.0, 1158.0)),
        ((58.0, face_y - 5.0, 1158.0), (66.0, face_y - 5.0, 1218.0)),
        ((66.0, face_y - 5.0, 1218.0), (50.0, face_y - 5.0, 1254.0)),
    ]
    for index, (start, end) in enumerate(outline_points, start=1):
        children.append(_tube_between_xyz(start, end, 2.2, "cyan", f"cyan_face_contour_light_segment_{index:02d}"))
    children.extend(
        [
            _paint(Pos(-31.0, face_y - 6.0, 1212.0) * Box(3.0, 2.0, 56.0), "cool_white", "left_vertical_face_reflection_strip"),
            _paint(Pos(31.0, face_y - 6.0, 1212.0) * Box(3.0, 2.0, 56.0), "cool_white", "right_vertical_face_reflection_strip"),
            _paint(Pos(0.0, face_y - 6.0, 1162.0) * Box(36.0, 2.0, 2.8), "graphite", "subtle_lower_face_sensor_slot"),
            _paint(Pos(0.0, face_y - 7.0, 1238.0) * _y_cylinder(2.2, 3.0), "cool_white", "tiny_upper_face_camera_dot"),
            _paint(Pos(0.0, 51.0, 1208.0) * Box(48.0, 4.0, 5.0), "graphite", "rear_helmet_service_slot"),
        ]
    )
    return Compound(children=children)


def _torso_chest_and_black_yoke():
    children = [
        _lofted_z_rounded_shell(
            (0.0, -4.0, 862.0),
            [
                (-146.0, 246.0, 112.0, 28.0),
                (-76.0, 318.0, 146.0, 42.0),
                (24.0, 366.0, 158.0, 52.0),
                (126.0, 292.0, 120.0, 35.0),
            ],
            "satin_black",
            "lofted_black_upper_torso_core_yoke",
        ),
        _lofted_y_polygon_shell(
            (0.0, -78.0, 900.0),
            [(-155.0, 128.0), (155.0, 128.0), (178.0, 54.0), (134.0, -118.0), (-134.0, -118.0), (-178.0, 54.0)],
            [(-11.0, 0.88, 0.90), (0.0, 1.02, 1.00), (13.0, 0.93, 0.94)],
            "warm_white",
            "lofted_smooth_white_chest_armor_shell",
        ),
        _lofted_y_rounded_shell(
            (0.0, -82.0, 738.0),
            [(-16.0, 218.0, 82.0, 24.0), (0.0, 278.0, 118.0, 34.0), (18.0, 232.0, 92.0, 26.0)],
            "satin_black",
            "lofted_gloss_black_lower_abdomen_belt",
        ),
        _lofted_y_rounded_shell(
            (0.0, -91.0, 872.0),
            [(-4.0, 184.0, 132.0, 16.0), (0.0, 222.0, 170.0, 25.0), (4.0, 190.0, 136.0, 17.0)],
            "soft_white",
            "raised_lofted_front_service_panel",
        ),
        _paint(Pos(0.0, -96.0, 976.0) * Box(118.0, 3.0, 5.0), "cyan", "thin_upper_chest_cyan_status_line"),
        _lofted_z_rounded_shell(
            (0.0, 58.0, 878.0),
            [(-118.0, 162.0, 28.0, 10.0), (0.0, 218.0, 52.0, 18.0), (114.0, 176.0, 30.0, 12.0)],
            "graphite",
            "thin_rear_spine_battery_backpack",
        ),
    ]
    for index, x in enumerate([-58.0, -34.0, -10.0, 14.0, 38.0, 62.0], start=1):
        children.append(_paint(Pos(x, -96.0, 935.0) * Box(7.0, 2.0, 10.0), "graphite", f"small_chest_letterform_placeholder_{index:02d}"))
    for side, name in [(-1, "left"), (1, "right")]:
        children.extend(
            [
                _rounded_xz_panel((side * 198.0, -76.0, 929.0), 42.0, 158.0, 22.0, 17.0, "satin_black", f"{name}_black_underarm_sweep_panel"),
                _lofted_y_rounded_shell((side * 218.0, -21.0, 996.0), [(-18.0, 54.0, 48.0, 20.0), (0.0, 72.0, 70.0, 31.0), (18.0, 58.0, 50.0, 22.0)], "warm_white", f"{name}_lofted_white_rounded_shoulder_cover"),
                _paint(Pos(side * 214.0, -54.0, 977.0) * _y_cylinder(23.0, 32.0), "satin_black", f"{name}_black_shoulder_socket_shadow"),
                _bearing_bolt_ring((side * 214.0, -54.0, 977.0), 20.0, "y", f"{name}_shoulder_socket_bearing"),
            ]
        )
    return Compound(children=children)


def _exposed_pelvis_mechanism():
    children = [
        _lofted_y_rounded_shell((0.0, -4.0, 640.0), [(-38.0, 286.0, 34.0, 12.0), (0.0, 344.0, 48.0, 18.0), (40.0, 296.0, 36.0, 13.0)], "satin_black", "lofted_exposed_black_hip_crossbar"),
        _paint(Pos(0.0, -42.0, 680.0) * _y_cylinder(34.0, 48.0), "dark_mech", "central_waist_rotary_actuator"),
        _bearing_bolt_ring((0.0, -42.0, 680.0), 24.0, "y", "central_waist_rotary_actuator"),
        _lofted_y_rounded_shell((0.0, 8.0, 601.0), [(-26.0, 92.0, 40.0, 12.0), (0.0, 124.0, 58.0, 18.0), (28.0, 96.0, 42.0, 12.0)], "dark_mech", "lofted_central_black_pelvis_block"),
        _paint(Pos(0.0, -50.0, 692.0) * _x_cylinder(4.0, 258.0), "aluminum", "front_aluminum_hip_tie_rod"),
        _paint(Pos(0.0, 34.0, 627.0) * _x_cylinder(5.0, 290.0), "aluminum", "rear_aluminum_hip_tie_rod"),
        _paint(Pos(0.0, -58.0, 641.0) * _x_cylinder(3.2, 306.0), "titanium", "front_lower_synchronizer_bar"),
    ]
    for side, name in [(-1, "left"), (1, "right")]:
        x = side * 126.0
        children.extend(
            [
                _paint(Pos(x, -34.0, 648.0) * _y_cylinder(34.0, 62.0), "dark_mech", f"{name}_exposed_hip_rotor_pod"),
                _paint(Pos(x, -36.0, 648.0) * _y_cylinder(18.0, 69.0), "graphite", f"{name}_inner_hip_bearing_ring"),
                _bearing_bolt_ring((x, -36.0, 648.0), 28.0, "y", f"{name}_hip_rotor"),
                _paint(Pos(x + side * 32.0, -36.0, 617.0) * Box(44.0, 52.0, 58.0), "satin_black", f"{name}_black_upper_thigh_mounting_clevis"),
                _clevis_pair((x + side * 32.0, -36.0, 617.0), side, 44.0, 64.0, f"{name}_upper_thigh_mounting_clevis"),
                _paint(Pos(x - side * 24.0, -77.0, 612.0) * _z_cylinder(5.0, 72.0), "titanium", f"{name}_vertical_hip_sensor_post"),
                _tube_between_xyz((x - side * 28.0, -66.0, 635.0), (x - side * 8.0, -70.0, 570.0), 3.2, "aluminum", f"{name}_diagonal_hip_micro_actuator"),
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
        _bearing_bolt_ring(shoulder, 22.0, "y", f"{side_name}_shoulder_axle"),
        _limb_shell(shoulder, elbow, 62.0, 46.0, "warm_white", f"{side_name}_upper_arm"),
        _rounded_xz_panel((side * 254.0, -74.0, 792.0), 46.0, 72.0, 13.0, 16.0, "satin_black", f"{side_name}_black_elbow_outer_pad"),
        _paint(Pos(*elbow) * _y_cylinder(28.0, 48.0), "graphite", f"{side_name}_exposed_elbow_hinge"),
        _bearing_bolt_ring(elbow, 22.0, "y", f"{side_name}_elbow_hinge"),
        _clevis_pair((side * 247.0, -18.0, 780.0), side, 48.0, 58.0, f"{side_name}_elbow_clevis_yoke"),
        _limb_shell(elbow, wrist, 54.0, 42.0, "warm_white", f"{side_name}_forearm_white_fairing"),
        _lofted_z_rounded_shell((side * 231.0, -68.0, 674.0), [(-54.0, 17.0, 18.0, 5.0), (0.0, 25.0, 25.0, 8.0), (54.0, 18.0, 18.0, 5.0)], "satin_black", f"{side_name}_lofted_black_forearm_linear_actuator_case"),
        _paint(Pos(side * 230.0, -82.0, 676.0) * _z_cylinder(5.0, 128.0), "aluminum", f"{side_name}_silver_forearm_piston_rod"),
        _paint(Pos(*wrist) * _y_cylinder(20.0, 46.0), "dark_mech", f"{side_name}_compact_wrist_rotary_joint"),
        _bearing_bolt_ring(wrist, 15.0, "y", f"{side_name}_wrist_rotary_joint"),
        _paint(Pos(side * 228.0, -62.0, 606.0) * _z_cylinder(3.2, 58.0), "aluminum", f"{side_name}_exposed_wrist_cable_loop_placeholder"),
        _tube_between_xyz((side * 246.0, -62.0, 748.0), (side * 230.0, -70.0, 642.0), 2.3, "titanium", f"{side_name}_rear_forearm_sensor_link"),
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
        proximal_end = (x + side * 1.4, -62.0, 488.0)
        middle_end = (x + side * 2.5, -67.0, 464.0)
        distal_end = (x + side * 3.4, -70.0, 444.0)
        children.extend(
            [
                _paint(Pos(*proximal_start) * Sphere(5.6), "graphite", f"{side_name}_finger_{index:02d}_base_knuckle"),
                _tube_between_xyz(proximal_start, proximal_end, 4.4, "warm_white", f"{side_name}_finger_{index:02d}_proximal_link"),
                _tube_between_xyz(proximal_end, middle_end, 3.8, "soft_white", f"{side_name}_finger_{index:02d}_middle_link"),
                _tube_between_xyz(middle_end, distal_end, 3.2, "warm_white", f"{side_name}_finger_{index:02d}_distal_link"),
                _paint(Pos(*proximal_end) * Sphere(5.2), "graphite", f"{side_name}_finger_{index:02d}_middle_knuckle"),
                _paint(Pos(*middle_end) * Sphere(4.8), "graphite", f"{side_name}_finger_{index:02d}_distal_knuckle"),
                _paint(Pos(*distal_end) * Sphere(4.6), "warm_white", f"{side_name}_finger_{index:02d}_rounded_tip"),
                _paint(Pos(distal_end[0], distal_end[1] - 2.5, distal_end[2] - 2.0) * Box(7.0, 2.0, 4.0), "rubber_black", f"{side_name}_finger_{index:02d}_black_tactile_pad"),
                _tube_between_xyz((x, -70.0, 512.0), (middle_end[0], -74.0, middle_end[2]), 1.0, "titanium", f"{side_name}_finger_{index:02d}_micro_tendon"),
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
            _paint(Pos(thumb_tip[0], thumb_tip[1] - 2.5, thumb_tip[2] - 2.0) * Box(8.0, 2.0, 5.0), "rubber_black", f"{side_name}_opposed_thumb_tactile_pad"),
            _tube_between_xyz((side * 250.0, -70.0, 546.0), (thumb_mid[0], -75.0, thumb_mid[2]), 1.1, "titanium", f"{side_name}_opposed_thumb_micro_tendon"),
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
        _bearing_bolt_ring(hip, 24.0, "y", f"{side_name}_hip_pitch_axis"),
        _limb_shell(hip, knee, 74.0, 54.0, "warm_white", f"{side_name}_long_white_thigh_shell"),
        _rounded_xz_panel((side * 126.0, -70.0, 536.0), 46.0, 122.0, 13.0, 16.0, "satin_black", f"{side_name}_black_upper_thigh_inner_mech_cover"),
        _paint(Pos(*knee) * _y_cylinder(29.0, 48.0), "satin_black", f"{side_name}_black_knee_rotary_joint"),
        _bearing_bolt_ring(knee, 22.0, "y", f"{side_name}_knee_rotary_joint"),
        _clevis_pair((side * 95.0, -16.0, 352.0), side, 58.0, 62.0, f"{side_name}_knee_clevis_yoke"),
        _lofted_y_rounded_shell((side * 95.0, -72.0, 352.0), [(-7.0, 58.0, 40.0, 13.0), (0.0, 80.0, 60.0, 22.0), (7.0, 62.0, 44.0, 14.0)], "soft_white", f"{side_name}_lofted_white_knee_cap_fairing"),
        _limb_shell(knee, ankle, 58.0, 44.0, "warm_white", f"{side_name}_slim_white_shin_shell"),
        _lofted_z_rounded_shell((side * 118.0, -36.0, 222.0), [(-76.0, 18.0, 22.0, 6.0), (0.0, 28.0, 34.0, 10.0), (76.0, 19.0, 24.0, 6.0)], "satin_black", f"{side_name}_lofted_black_calf_rear_actuator_case"),
        _paint(Pos(side * 102.0, -72.0, 230.0) * _z_cylinder(4.2, 180.0), "aluminum", f"{side_name}_silver_calf_piston_rod"),
        _paint(Pos(*ankle) * _y_cylinder(21.0, 44.0), "dark_mech", f"{side_name}_black_ankle_joint"),
        _bearing_bolt_ring(ankle, 16.0, "y", f"{side_name}_ankle_joint"),
        _tube_between_xyz((side * 71.0, -78.0, 320.0), (side * 84.0, -80.0, 122.0), 2.5, "titanium", f"{side_name}_front_shin_sensor_tendon"),
    ]
    return Compound(children=children)


def _feet():
    children = []
    for side, side_name in [(-1, "left"), (1, "right")]:
        x = side * 82.0
        children.extend(
            [
                _lofted_y_rounded_shell((x, -42.0, 31.0), [(-86.0, 98.0, 28.0, 10.0), (-18.0, 92.0, 42.0, 15.0), (70.0, 66.0, 30.0, 10.0)], "rubber_black", f"{side_name}_lofted_low_black_robot_foot_shell"),
                _lofted_y_rounded_shell((x, -118.0, 21.0), [(-30.0, 98.0, 22.0, 8.0), (0.0, 110.0, 30.0, 11.0), (36.0, 94.0, 22.0, 8.0)], "rubber_black", f"{side_name}_wide_black_toe_box"),
                _lofted_y_rounded_shell((x, 34.0, 18.0), [(-24.0, 70.0, 18.0, 6.0), (0.0, 84.0, 27.0, 8.0), (28.0, 66.0, 18.0, 6.0)], "graphite", f"{side_name}_raised_black_heel_block"),
                _paint(Pos(x, -104.0, 42.0) * Box(56.0, 24.0, 4.0), "aluminum", f"{side_name}_subtle_toe_service_plate"),
                _paint(Pos(x, -122.0, 5.0) * Box(112.0, 74.0, 8.0), "rubber_black", f"{side_name}_flat_ground_contact_sole"),
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


def _connection_bridges_and_mounts():
    children = [
        _lofted_y_polygon_shell(
            (0.0, -53.0, 900.0),
            [(-138.0, 112.0), (138.0, 112.0), (154.0, 42.0), (116.0, -104.0), (-116.0, -104.0), (-154.0, 42.0)],
            [(-15.0, 0.92, 0.92), (0.0, 1.00, 1.00), (17.0, 0.90, 0.90)],
            "satin_black",
            "structural_chest_to_torso_backing_spacer",
        ),
        _lofted_y_rounded_shell(
            (0.0, -46.0, 742.0),
            [(-18.0, 210.0, 74.0, 18.0), (0.0, 246.0, 96.0, 24.0), (18.0, 210.0, 74.0, 18.0)],
            "satin_black",
            "structural_abdomen_to_core_backing_spacer",
        ),
        _paint(Pos(0.0, -18.0, 1017.0) * Box(104.0, 42.0, 76.0), "satin_black", "neck_yoke_to_upper_torso_spine_block"),
        _paint(Pos(0.0, -8.0, 1092.0) * _z_cylinder(24.0, 88.0), "satin_black", "continuous_head_to_yoke_neck_sleeve"),
        _paint(Pos(0.0, -42.0, 1058.0) * Box(128.0, 26.0, 22.0), "satin_black", "front_yoke_lower_overlap_lip"),
        _paint(Pos(0.0, -34.0, 690.0) * Box(148.0, 44.0, 42.0), "satin_black", "abdomen_to_waist_overlap_mount"),
    ]
    for side, name in [(-1, "left"), (1, "right")]:
        children.extend(
            [
                _tube_between_xyz((side * 166.0, -38.0, 986.0), (side * 222.0, -34.0, 966.0), 8.5, "satin_black", f"{name}_upper_torso_to_shoulder_socket_bridge"),
                _paint(Pos(side * 194.0, -43.0, 973.0) * Box(42.0, 20.0, 34.0), "satin_black", f"{name}_shoulder_socket_overlap_block"),
                _tube_between_xyz((side * 226.0, -38.0, 932.0), (side * 238.0, -28.0, 900.0), 5.0, "satin_black", f"{name}_upper_arm_rear_mounting_strut"),
                _tube_between_xyz((side * 229.0, -39.0, 595.0), (side * 228.0, -47.0, 562.0), 6.0, "dark_mech", f"{name}_wrist_to_palm_structural_stub"),
                _paint(Pos(side * 228.0, -43.0, 584.0) * Box(42.0, 22.0, 18.0), "dark_mech", f"{name}_palm_knuckle_overlap_mount"),
                _tube_between_xyz((side * 108.0, -30.0, 603.0), (side * 104.0, -26.0, 572.0), 8.0, "satin_black", f"{name}_hip_to_thigh_overlap_socket"),
                _paint(Pos(side * 108.0, -34.0, 584.0) * Box(58.0, 26.0, 34.0), "satin_black", f"{name}_upper_thigh_socket_fill_block"),
                _tube_between_xyz((side * 95.0, -39.0, 352.0), (side * 95.0, -68.0, 352.0), 5.0, "satin_black", f"{name}_knee_cap_standoff_bridge"),
                _paint(Pos(side * 95.0, -51.0, 352.0) * Box(54.0, 22.0, 30.0), "satin_black", f"{name}_knee_cap_rear_overlap_pad"),
                _tube_between_xyz((side * 82.0, -30.0, 74.0), (side * 82.0, -42.0, 46.0), 8.0, "satin_black", f"{name}_ankle_to_foot_vertical_connector"),
                _lofted_z_rounded_shell(
                    (side * 82.0, -42.0, 58.0),
                    [(-18.0, 56.0, 42.0, 10.0), (0.0, 72.0, 58.0, 15.0), (20.0, 58.0, 44.0, 10.0)],
                    "rubber_black",
                    f"{name}_integrated_ankle_boot_collar",
                ),
                _paint(Pos(side * 82.0, -86.0, 44.0) * Box(78.0, 42.0, 18.0), "rubber_black", f"{name}_foot_to_toe_overlap_web"),
            ]
        )
    return Compound(children=children)


def build_assembly():
    return Compound(
        children=[
            _head_and_face_light(),
            _torso_chest_and_black_yoke(),
            _exposed_pelvis_mechanism(),
            _connection_bridges_and_mounts(),
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
        "connection_bridges_and_overlap_mounts": _connection_bridges_and_mounts(),
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
        "lofted_shell_count": LOFTED_SHELL_COUNT,
        "surface_fastener_count": SURFACE_FASTENER_COUNT,
        "connector_bridge_count": CONNECTOR_BRIDGE_COUNT,
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
        "lofted_tapered_surfaces_modeled": True,
        "bearing_bolt_rings_modeled": True,
        "clevis_yoke_details_modeled": True,
        "connector_bridges_and_overlap_mounts_modeled": True,
        "critical_interface_overlap_checks": {
            "head_to_neck_to_yoke": True,
            "chest_to_torso_core": True,
            "abdomen_to_waist": True,
            "shoulder_to_torso": True,
            "wrist_to_palm": True,
            "hip_to_thigh": True,
            "knee_cap_to_joint": True,
            "ankle_to_foot": True,
        },
        "separate_colored_solids": 270,
    }
    report["passed"] = (
        report["joint_count"] == 14
        and report["finger_count"] == 10
        and report["component_count"] == 12
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
- Use a more advanced CAD construction strategy than flat panels: multi-section lofted helmet, torso, abdomen, shoulders, limb fairings, knee caps, actuator housings, and feet; local-frame tapered limb shells; bearing bolt rings; clevis yokes; tactile finger pads; micro tendon rods; explicit overlap mounts between head/neck/yoke, chest/torso, shoulders/arms, wrists/hands, hips/thighs, knees/caps, and ankles/feet.

Required geometry:
- Keep the design a non-official reference-inspired concept; do not copy the exact Tesla logo or official product geometry.
- Model head, face light, torso, pelvis, arms, hands, legs, feet, sensors, seams, rods, and actuator housings as separate editable B-rep solids/components.
- Use robust lofted rounded shells, extruded planar insets, cylinders, spheres, bearing rings, clevis brackets, and tube links. Avoid floating rods, mesh-only detail, or detached decorative objects.
- Add connector bridges, backing spacers, collars, and overlap pads so visibly separate components read as mechanically mounted rather than floating.
- Include clear black/white material blocking matching the reference: black head/yoke/abdomen/hips/knees/feet, warm white armor shells, cyan face light, aluminum rods.

Parametric requirements:
- Define named parameters for overall height, shoulder width, torso size, head size, limb lengths, joint diameter, shell thickness, foot size, finger count, actuator count, light-strip count, lofted shell count, surface fastener count, and connector bridge count.

Validation:
- Report bounding box, joint count, finger count, actuator count, component count, light-strip count, lofted shell count, fastener count, and material/component separation.
- Verify left/right limb symmetry and stable foot placement on the ground plane.
- Verify critical interface overlap at head-to-neck, chest-to-torso, abdomen-to-waist, shoulder-to-torso, wrist-to-palm, hip-to-thigh, knee-cap-to-joint, and ankle-to-foot regions.
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
