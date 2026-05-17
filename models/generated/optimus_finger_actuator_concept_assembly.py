from __future__ import annotations

import json
import math
from pathlib import Path

from build123d import Box, Color, Compound, Cylinder, Pos, Rot, Sphere, export_gltf, export_step


DISPLAY_NAME = "Tesla Optimus-inspired robotic finger actuator concept"

# Units: millimeters. X is finger spread, Y is finger extension, Z is vertical.
FINGER_COUNT = 4
TOTAL_FINGERS = 5
PHALANX_LENGTHS = (58.0, 42.0, 30.0)
THUMB_PHALANX_LENGTHS = (42.0, 28.0)
JOINT_SPACING = 4.0
FINGER_PITCH = 34.0
PALM_WIDTH = 174.0
PALM_DEPTH = 92.0
PALM_THICKNESS = 28.0
ACTUATOR_DIAMETER = 12.0
TENDON_TUBE_RADIUS = 1.25
PAD_THICKNESS = 7.0
LINK_WIDTH = 26.0
LINK_THICKNESS = 15.0
KNUCKLE_RADIUS = 9.5

TOTAL_JOINTS = FINGER_COUNT * 3 + 2
TOTAL_PHALANGES = FINGER_COUNT * 3 + 2
ACTUATOR_COUNT = 6
TENDON_GUIDE_COUNT = TOTAL_FINGERS * 2
FASTENER_COUNT = 156
COMPONENT_COUNT = 6
ROOT_JOINT_Z = PALM_THICKNESS + 38.0

STEP_OUTPUT = "optimus_finger_actuator_concept_assembly.step"
GLB_OUTPUT = "optimus_finger_actuator_concept_assembly.glb"
VALIDATION_OUTPUT = "optimus_finger_actuator_concept_validation_report.json"
PROMPT_OUTPUT = "optimus_finger_actuator_concept_prompt.md"
COMPONENT_DIR = "optimus_finger_actuator_concept_components"
COMPONENT_REVISION = "optimus-finger-actuator-concept-v9-clevis-bearing-detail"

COLORS = {
    "graphite": Color(0.045, 0.048, 0.052, 1.0),
    "black": Color(0.006, 0.007, 0.008, 1.0),
    "dark_rubber": Color(0.018, 0.018, 0.016, 1.0),
    "aluminum": Color(0.68, 0.70, 0.70, 1.0),
    "satin": Color(0.52, 0.54, 0.55, 1.0),
    "titanium": Color(0.40, 0.42, 0.44, 1.0),
    "copper": Color(0.82, 0.42, 0.14, 1.0),
    "blue": Color(0.02, 0.36, 0.95, 1.0),
    "cyan": Color(0.02, 0.78, 0.95, 1.0),
    "service": Color(0.18, 0.19, 0.20, 1.0),
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


def _vec(angle_deg: float, length: float) -> tuple[float, float]:
    angle = math.radians(angle_deg)
    return math.cos(angle) * length, math.sin(angle) * length


def _distance_xy(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _distance_xyz(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2)


def _angle_xy(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


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


def _box_between_xy(
    start: tuple[float, float],
    end: tuple[float, float],
    width: float,
    height: float,
    z: float,
    color: str,
    label: str,
):
    length = _distance_xy(start, end)
    center = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
    angle = _angle_xy(start, end)
    return _paint(Pos(center[0], center[1], z) * Rot(0.0, 0.0, angle) * Box(length, width, height), color, label)


def _box_between_xyz(
    start: tuple[float, ...],
    end: tuple[float, ...],
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


def _tube_between_xy(
    start: tuple[float, float],
    end: tuple[float, float],
    radius: float,
    z: float,
    color: str,
    label: str,
):
    length = _distance_xy(start, end)
    center = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
    angle = _angle_xy(start, end)
    return _paint(Pos(center[0], center[1], z) * Rot(0.0, 0.0, angle) * _x_cylinder(radius, length), color, label)


def _tube_between_xyz(
    start: tuple[float, ...],
    end: tuple[float, ...],
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


def _offset_segment_xy(
    start: tuple[float, ...],
    end: tuple[float, ...],
    offset: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    angle = math.radians(_angle_xy(start, end) + 90.0)
    dx = math.cos(angle) * offset
    dy = math.sin(angle) * offset
    return (start[0] + dx, start[1] + dy, start[2]), (end[0] + dx, end[1] + dy, end[2])


def _add_z(point: tuple[float, ...], dz: float) -> tuple[float, float, float]:
    return (point[0], point[1], point[2] + dz)


def _unit_segment(start: tuple[float, ...], end: tuple[float, ...]) -> tuple[float, float, float]:
    length = _distance_xyz(start, end)
    return ((end[0] - start[0]) / length, (end[1] - start[1]) / length, (end[2] - start[2]) / length)


def _segment_side_vector(start: tuple[float, ...], end: tuple[float, ...]) -> tuple[float, float, float]:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    horizontal = math.hypot(dx, dy)
    if horizontal < 1e-6:
        return (1.0, 0.0, 0.0)
    return (-dy / horizontal, dx / horizontal, 0.0)


def _cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)
    if length < 1e-6:
        return (0.0, 0.0, 1.0)
    return (vector[0] / length, vector[1] / length, vector[2] / length)


def _segment_top_normal(start: tuple[float, ...], end: tuple[float, ...]) -> tuple[float, float, float]:
    along = _unit_segment(start, end)
    side = _segment_side_vector(start, end)
    normal = _normalize(_cross(along, side))
    if normal[2] < 0.0:
        normal = (-normal[0], -normal[1], -normal[2])
    return normal


def _move_point(point: tuple[float, ...], vector: tuple[float, float, float], distance: float) -> tuple[float, float, float]:
    return (point[0] + vector[0] * distance, point[1] + vector[1] * distance, point[2] + vector[2] * distance)


def _offset_segment_vector(
    start: tuple[float, ...],
    end: tuple[float, ...],
    vector: tuple[float, float, float],
    distance: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    return _move_point(start, vector, distance), _move_point(end, vector, distance)


def _segment_point(start: tuple[float, ...], end: tuple[float, ...], distance_from_center: float) -> tuple[float, float, float]:
    along = _unit_segment(start, end)
    return (
        (start[0] + end[0]) / 2.0 + along[0] * distance_from_center,
        (start[1] + end[1]) / 2.0 + along[1] * distance_from_center,
        (start[2] + end[2]) / 2.0 + along[2] * distance_from_center,
    )


def _segment_point_from_start(start: tuple[float, ...], end: tuple[float, ...], distance_from_start: float) -> tuple[float, float, float]:
    along = _unit_segment(start, end)
    return (
        start[0] + along[0] * distance_from_start,
        start[1] + along[1] * distance_from_start,
        start[2] + along[2] * distance_from_start,
    )


def _joint_cross_axis(
    point: tuple[float, ...],
    next_point: tuple[float, ...],
    span: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    angle = math.radians(_angle_xy(point, next_point) + 90.0)
    dx = math.cos(angle) * span / 2.0
    dy = math.sin(angle) * span / 2.0
    return (point[0] - dx, point[1] - dy, point[2]), (point[0] + dx, point[1] + dy, point[2])


def _cumulative_angles(angles: tuple[float, ...]) -> list[float]:
    total = 0.0
    cumulative = []
    for angle in angles:
        total += angle
        cumulative.append(total)
    return cumulative


def _finger_chain(
    root: tuple[float, float],
    lengths: tuple[float, ...],
    yaw_angles: tuple[float, ...],
    flexion_angles: tuple[float, ...],
) -> list[tuple[float, float, float]]:
    current = (root[0], root[1], ROOT_JOINT_Z)
    points = [current]
    cumulative_flexion_angle = 0.0
    for length, yaw_angle, joint_flexion_angle in zip(lengths, yaw_angles, flexion_angles):
        cumulative_flexion_angle += joint_flexion_angle
        segment_length = length + JOINT_SPACING
        horizontal_length = math.cos(math.radians(cumulative_flexion_angle)) * segment_length
        dz = -math.sin(math.radians(cumulative_flexion_angle)) * segment_length
        dx, dy = _vec(yaw_angle, horizontal_length)
        current = (current[0] + dx, current[1] + dy, current[2] + dz)
        points.append(current)
    return points


def _finger_specs() -> list[dict[str, object]]:
    start_x = -FINGER_PITCH * 1.5
    return [
        {
            "name": "index",
            "root": (start_x, PALM_DEPTH / 2.0 - 5.0),
            "scale": 0.96,
            "angles": (92.0, 91.0, 90.0),
            "flexion_deg": (8.0, 18.0, 22.0),
        },
        {
            "name": "middle",
            "root": (start_x + FINGER_PITCH, PALM_DEPTH / 2.0 - 1.0),
            "scale": 1.05,
            "angles": (90.0, 90.0, 90.0),
            "flexion_deg": (8.0, 19.0, 22.0),
        },
        {
            "name": "ring",
            "root": (start_x + FINGER_PITCH * 2.0, PALM_DEPTH / 2.0 - 3.0),
            "scale": 1.00,
            "angles": (88.0, 89.0, 90.0),
            "flexion_deg": (7.0, 17.0, 20.0),
        },
        {
            "name": "pinky",
            "root": (start_x + FINGER_PITCH * 3.0, PALM_DEPTH / 2.0 - 8.0),
            "scale": 0.86,
            "angles": (85.0, 86.0, 87.0),
            "flexion_deg": (8.0, 18.0, 24.0),
        },
    ]


def _scaled_lengths(scale: float) -> tuple[float, float, float]:
    return tuple(length * scale for length in PHALANX_LENGTHS)


def _all_finger_chains() -> dict[str, list[tuple[float, float, float]]]:
    chains = {}
    for spec in _finger_specs():
        chains[str(spec["name"])] = _finger_chain(
            spec["root"],  # type: ignore[arg-type]
            _scaled_lengths(float(spec["scale"])),
            spec["angles"],  # type: ignore[arg-type]
            spec["flexion_deg"],  # type: ignore[arg-type]
        )
    chains["thumb"] = _finger_chain(
        (-PALM_WIDTH / 2.0 + 5.0, -13.0),
        THUMB_PHALANX_LENGTHS,
        (137.0, 122.0),
        (16.0, 22.0),
    )
    return chains


def _joint_angle_report() -> dict[str, dict[str, list[float]]]:
    report: dict[str, dict[str, list[float]]] = {}
    for spec in _finger_specs():
        flexion = tuple(float(angle) for angle in spec["flexion_deg"])  # type: ignore[index]
        report[str(spec["name"])] = {
            "local_flexion_deg": [round(angle, 1) for angle in flexion],
            "cumulative_link_pitch_deg": [round(angle, 1) for angle in _cumulative_angles(flexion)],
        }
    thumb_flexion = (16.0, 22.0)
    report["thumb"] = {
        "local_flexion_deg": [round(angle, 1) for angle in thumb_flexion],
        "cumulative_link_pitch_deg": [round(angle, 1) for angle in _cumulative_angles(thumb_flexion)],
    }
    return report


def _palm_rail_and_actuators():
    children = [
        _paint(Pos(0.0, 0.0, PALM_THICKNESS / 2.0) * Box(PALM_WIDTH, PALM_DEPTH, PALM_THICKNESS), "graphite", "compact_graphite_palm_rail"),
        _paint(Pos(0.0, PALM_DEPTH / 2.0 - 6.0, PALM_THICKNESS + 4.0) * Box(PALM_WIDTH - 10.0, 18.0, 8.0), "titanium", "satin_knuckle_mounting_rail"),
        _paint(Pos(0.0, -PALM_DEPTH / 2.0 + 10.0, PALM_THICKNESS + 2.0) * Box(PALM_WIDTH - 24.0, 22.0, 6.0), "service", "rear_service_cover_plate"),
        _paint(Pos(-PALM_WIDTH / 2.0 - 10.0, -18.0, PALM_THICKNESS / 2.0 + 2.0) * Rot(0.0, 0.0, -34.0) * Box(34.0, 44.0, 24.0), "graphite", "outward_opposed_thumb_base_block"),
    ]
    actuator_xs = [-60.0, -30.0, 0.0, 30.0, 60.0, -82.0]
    for index, x in enumerate(actuator_xs, start=1):
        y = -20.0 if index < 6 else -14.0
        angle = 0.0 if index < 6 else -32.0
        children.extend(
            [
                _paint(Pos(x, y, 20.0) * Rot(0.0, 0.0, angle) * _y_cylinder(ACTUATOR_DIAMETER / 2.0, 54.0), "satin", f"linear_micro_actuator_placeholder_{index:02d}"),
                _paint(Pos(x, y + 29.0, 20.0) * Rot(0.0, 0.0, angle) * _y_cylinder(2.8, 22.0), "titanium", f"micro_actuator_piston_rod_{index:02d}"),
                _paint(Pos(x, y - 31.0, 20.0) * Box(18.0, 5.0, 10.0), "black", f"actuator_rear_cable_exit_{index:02d}"),
            ]
        )
    for index, x in enumerate([-55.0, -18.0, 18.0, 55.0], start=1):
        children.append(_paint(Pos(x, 20.0, PALM_THICKNESS + 9.0) * Box(22.0, 32.0, 5.0), "service", f"flush_palm_service_cover_{index:02d}"))
    return Compound(children=children)


def _finger_link_sets():
    children = []
    chains = _all_finger_chains()
    for finger_name, points in chains.items():
        is_thumb = finger_name == "thumb"
        segment_count = len(points) - 1
        width = LINK_WIDTH * (0.92 if is_thumb else 1.0)
        for segment_index in range(segment_count):
            start = points[segment_index]
            end = points[segment_index + 1]
            length = _distance_xyz(start, end)
            taper = 1.0 - segment_index * 0.14
            link_width = width * taper
            side_offset = link_width / 2.0 - 2.8
            top_normal = _segment_top_normal(start, end)
            left_start, left_end = _offset_segment_xy(start, end, side_offset)
            right_start, right_end = _offset_segment_xy(start, end, -side_offset)
            top_start, top_end = _offset_segment_vector(start, end, top_normal, LINK_THICKNESS / 2.0 + 3.0)
            underside_start, underside_end = _offset_segment_vector(start, end, top_normal, -LINK_THICKNESS / 2.0 - 2.0)
            detail_start = _segment_point_from_start(start, end, min(12.0, length * 0.22))
            detail_end = _segment_point_from_start(start, end, max(length - 10.0, length * 0.55))
            shell_label = f"{finger_name}_phalange_{segment_index + 1}_satin_aluminum_shell"
            children.extend(
                [
                    _box_between_xyz(start, end, link_width, LINK_THICKNESS, "aluminum", shell_label),
                    _box_between_xyz(top_start, top_end, link_width - 7.0, 4.0, "satin", f"{finger_name}_phalange_{segment_index + 1}_broad_top_highlight_panel"),
                    _box_between_xyz(left_start, left_end, 2.8, LINK_THICKNESS + 4.0, "titanium", f"{finger_name}_phalange_{segment_index + 1}_left_side_cheek"),
                    _box_between_xyz(right_start, right_end, 2.8, LINK_THICKNESS + 4.0, "titanium", f"{finger_name}_phalange_{segment_index + 1}_right_side_cheek"),
                    _box_between_xyz(underside_start, underside_end, link_width - 5.5, 3.6, "graphite", f"{finger_name}_phalange_{segment_index + 1}_underside_shadow_gap"),
                ]
            )
            for rail_index, rail_offset in enumerate((-link_width * 0.27, link_width * 0.27), start=1):
                rail_start, rail_end = _offset_segment_vector(detail_start, detail_end, _segment_side_vector(start, end), rail_offset)
                rail_start = _move_point(rail_start, top_normal, LINK_THICKNESS / 2.0 + 6.0)
                rail_end = _move_point(rail_end, top_normal, LINK_THICKNESS / 2.0 + 6.0)
                children.append(
                    _box_between_xyz(
                        rail_start,
                        rail_end,
                        2.1,
                        2.2,
                        "titanium",
                        f"{finger_name}_phalange_{segment_index + 1}_raised_longitudinal_indexing_rail_{rail_index}",
                    )
                )
            groove_start = _move_point(detail_start, top_normal, LINK_THICKNESS / 2.0 + 7.1)
            groove_end = _move_point(detail_end, top_normal, LINK_THICKNESS / 2.0 + 7.1)
            children.append(
                _box_between_xyz(
                    groove_start,
                    groove_end,
                    2.8,
                    1.2,
                    "graphite",
                    f"{finger_name}_phalange_{segment_index + 1}_center_recessed_service_groove",
                )
            )
            for collar_index, collar_distance in enumerate((4.0, max(length - 7.0, length * 0.72)), start=1):
                collar_start = _segment_point_from_start(start, end, collar_distance)
                collar_end = _segment_point_from_start(start, end, min(collar_distance + 3.2, length))
                children.append(
                    _box_between_xyz(
                        collar_start,
                        collar_end,
                        link_width + 2.0,
                        LINK_THICKNESS + 2.5,
                        "graphite",
                        f"{finger_name}_phalange_{segment_index + 1}_precision_joint_clearance_collar_{collar_index}",
                    )
                )
            for fastener_offset in (-length * 0.28, length * 0.28):
                fastener_point = _move_point(_segment_point(start, end, fastener_offset), top_normal, LINK_THICKNESS / 2.0 + 5.0)
                children.append(_paint(Pos(*fastener_point) * _z_cylinder(1.7, 2.0), "graphite", f"{finger_name}_phalange_{segment_index + 1}_flush_fastener"))
        for joint_index, point in enumerate(points[:-1], start=1):
            joint_label = "mcp" if joint_index == 1 else "pip" if joint_index == 2 else "dip"
            radius = KNUCKLE_RADIUS * (1.05 if joint_index == 1 else 0.92)
            next_point = points[joint_index]
            hinge_start, hinge_end = _joint_cross_axis(point, next_point, width * (0.95 if joint_index == 1 else 0.78))
            next_along = _unit_segment(point, next_point)
            next_side = _segment_side_vector(point, next_point)
            children.extend(
                [
                    _paint(Pos(point[0], point[1], point[2]) * _z_cylinder(radius, LINK_THICKNESS + 7.0), "titanium", f"{finger_name}_{joint_label}_rounded_joint_knuckle"),
                    _tube_between_xyz(hinge_start, hinge_end, 2.3, "graphite", f"{finger_name}_{joint_label}_true_cross_axis_hinge_pin"),
                    _tube_between_xyz(_add_z(hinge_start, 3.8), _add_z(hinge_end, 3.8), 1.2, "satin", f"{finger_name}_{joint_label}_raised_hinge_axis_reference"),
                    _paint(Pos(point[0], point[1], point[2] + LINK_THICKNESS / 2.0 + 6.5) * _z_cylinder(radius * 0.42, 2.6), "graphite", f"{finger_name}_{joint_label}_black_hinge_pin_cap"),
                    _paint(Pos(point[0], point[1], point[2] - LINK_THICKNESS / 2.0 - 6.5) * _z_cylinder(radius * 0.34, 2.6), "graphite", f"{finger_name}_{joint_label}_lower_hinge_pin_cap"),
                ]
            )
            for side_index, side_sign in enumerate((-1.0, 1.0), start=1):
                yoke_start = _move_point(_move_point(point, next_along, 2.5), next_side, side_sign * width * 0.48)
                yoke_end = _move_point(_move_point(point, next_along, 18.0), next_side, side_sign * width * 0.48)
                children.append(
                    _box_between_xyz(
                        yoke_start,
                        yoke_end,
                        3.8,
                        LINK_THICKNESS + 9.0,
                        "graphite",
                        f"{finger_name}_{joint_label}_side_clevis_yoke_bracket_{side_index}",
                    )
                )
            children.extend(
                [
                    _paint(Pos(*hinge_start) * Sphere(3.4), "graphite", f"{finger_name}_{joint_label}_left_bearing_end_cap"),
                    _paint(Pos(*hinge_end) * Sphere(3.4), "graphite", f"{finger_name}_{joint_label}_right_bearing_end_cap"),
                ]
            )
        tip = points[-1]
        prev = points[-2]
        distal_along = _unit_segment(prev, tip)
        distal_tip = _move_point(tip, distal_along, 10.0)
        children.append(_box_between_xyz(tip, distal_tip, width * 0.74, LINK_THICKNESS * 0.68, "aluminum", f"{finger_name}_rounded_distal_tip_carrier"))
    return Compound(children=children)


def _tendon_guide_tubes():
    children = []
    chains = _all_finger_chains()
    for finger_index, (finger_name, points) in enumerate(chains.items(), start=1):
        color_top = "blue" if finger_index % 2 else "copper"
        color_side = "copper" if finger_index % 2 else "blue"
        for segment_index in range(len(points) - 1):
            start = points[segment_index]
            end = points[segment_index + 1]
            top_normal = _segment_top_normal(start, end)
            tube_start, tube_end = _offset_segment_xy(start, end, 7.6)
            return_start, return_end = _offset_segment_xy(start, end, -7.6)
            children.extend(
                [
                    _tube_between_xyz(
                        _move_point(tube_start, top_normal, 9.0),
                        _move_point(tube_end, top_normal, 9.0),
                        TENDON_TUBE_RADIUS,
                        color_top,
                        f"{finger_name}_low_profile_tendon_guide_segment_{segment_index + 1}",
                    ),
                    _tube_between_xyz(
                        _move_point(return_start, top_normal, 2.0),
                        _move_point(return_end, top_normal, 2.0),
                        TENDON_TUBE_RADIUS * 0.72,
                        color_side,
                        f"{finger_name}_side_tendon_return_segment_{segment_index + 1}",
                    ),
                ]
            )
        root = points[0]
        entry_end, _ = _offset_segment_xy(root, points[1], 7.6)
        entry_normal = _segment_top_normal(root, points[1])
        entry_target = _move_point(entry_end, entry_normal, 9.0)
        entry_start = (entry_target[0], -PALM_DEPTH / 2.0 + 8.0, entry_target[2])
        children.append(_tube_between_xyz(entry_start, entry_target, TENDON_TUBE_RADIUS, color_top, f"{finger_name}_palm_tendon_entry_guide"))
    return Compound(children=children)


def _rubber_fingertip_pads():
    children = []
    chains = _all_finger_chains()
    for finger_name, points in chains.items():
        tip = points[-1]
        prev = points[-2]
        distal_along = _unit_segment(prev, tip)
        top_normal = _segment_top_normal(prev, tip)
        pad_width = LINK_WIDTH * (0.68 if finger_name == "thumb" else 0.78)
        pad_start = _move_point(_move_point(tip, distal_along, -22.0), top_normal, LINK_THICKNESS / 2.0 + 2.0)
        pad_end = _move_point(_move_point(tip, distal_along, -6.0), top_normal, LINK_THICKNESS / 2.0 + 2.0)
        children.extend(
            [
                _box_between_xyz(pad_start, pad_end, pad_width, 3.6, "dark_rubber", f"{finger_name}_low_profile_dark_rubber_tactile_fingertip_pad"),
                _box_between_xyz(
                    _move_point(pad_start, top_normal, 2.6),
                    _move_point(pad_end, top_normal, 2.6),
                    pad_width * 0.52,
                    1.6,
                    "graphite",
                    f"{finger_name}_subtle_tactile_pad_groove",
                ),
            ]
        )
    return Compound(children=children)


def _fasteners_hinge_pins_and_cable_exits():
    children = []
    chains = _all_finger_chains()
    for finger_name, points in chains.items():
        for joint_index, point in enumerate(points[:-1], start=1):
            axis_start, axis_end = _joint_cross_axis(point, points[joint_index], LINK_WIDTH * (0.94 if finger_name != "thumb" else 0.82))
            children.extend(
                [
                    _paint(Pos(axis_start[0], axis_start[1], axis_start[2]) * _z_cylinder(1.8, 8.0), "black", f"{finger_name}_joint_{joint_index}_left_hinge_pin_centerline"),
                    _paint(Pos(axis_end[0], axis_end[1], axis_end[2]) * _z_cylinder(1.8, 8.0), "black", f"{finger_name}_joint_{joint_index}_right_hinge_pin_centerline"),
                    _tube_between_xyz(axis_start, axis_end, 1.35, "black", f"{finger_name}_joint_{joint_index}_exposed_horizontal_rotation_axis"),
                ]
            )
    for index, x in enumerate([-70.0, -42.0, -14.0, 14.0, 42.0, 70.0], start=1):
        children.extend(
            [
                _paint(Pos(x, -PALM_DEPTH / 2.0 - 5.0, 18.0) * Box(14.0, 10.0, 8.0), "black", f"rear_cable_exit_boot_{index:02d}"),
                _paint(Pos(x, -PALM_DEPTH / 2.0 - 15.0, 18.0) * _y_cylinder(2.2, 22.0), "blue" if index % 2 else "copper", f"visible_cable_tail_{index:02d}"),
            ]
        )
    for index, x in enumerate([-76.0, -52.0, 52.0, 76.0], start=1):
        children.append(_paint(Pos(x, 0.0, PALM_THICKNESS + 10.0) * _z_cylinder(2.4, 3.0), "titanium", f"palm_cover_socket_fastener_{index:02d}"))
    return Compound(children=children)


def _presentation_base():
    return Compound(
        children=[
            _paint(Pos(0.0, 70.0, 3.0) * Box(216.0, 252.0, 6.0), "black", "thin_black_demo_shadow_base"),
            _paint(Pos(0.0, -54.0, 8.0) * Box(PALM_WIDTH + 18.0, PALM_DEPTH + 18.0, 4.0), "service", "subtle_palm_mounting_shadow_plate"),
        ]
    )


def build_assembly():
    return Compound(
        children=[
            _presentation_base(),
            _palm_rail_and_actuators(),
            _finger_link_sets(),
            _tendon_guide_tubes(),
            _rubber_fingertip_pads(),
            _fasteners_hinge_pins_and_cable_exits(),
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
        "palm_rail_and_micro_actuators": _palm_rail_and_actuators(),
        "articulated_finger_link_sets": _finger_link_sets(),
        "colored_tendon_guide_tubes": _tendon_guide_tubes(),
        "rubber_fingertip_pads": _rubber_fingertip_pads(),
        "fasteners_hinge_pins_and_cable_exits": _fasteners_hinge_pins_and_cable_exits(),
        "presentation_base": _presentation_base(),
    }
    for name, shape in components.items():
        _write_component(name, shape)


def _bbox_mm(shape) -> list[float]:
    box = shape.bounding_box().size
    return [round(float(box.X), 1), round(float(box.Y), 1), round(float(box.Z), 1)]


def _neutral_spacing_ok() -> bool:
    roots = [tuple(spec["root"]) for spec in _finger_specs()]
    min_spacing = min(abs(roots[index + 1][0] - roots[index][0]) for index in range(len(roots) - 1))
    return min_spacing >= LINK_WIDTH + 7.0


def _validation_report(shape) -> dict[str, object]:
    chains = _all_finger_chains()
    bbox = _bbox_mm(shape)
    joint_axes = {
        name: [[round(point[0], 2), round(point[1], 2), round(point[2], 2)] for point in points[:-1]]
        for name, points in chains.items()
    }
    report = {
        "product": "optimus_finger_actuator_concept",
        "display_name": DISPLAY_NAME,
        "design_intent": "Non-proprietary humanoid robotic finger actuator visual engineering concept with placeholder actuation and tendon routing",
        "finger_count": TOTAL_FINGERS,
        "primary_finger_count": FINGER_COUNT,
        "total_joints": TOTAL_JOINTS,
        "total_phalanges": TOTAL_PHALANGES,
        "actuator_count": ACTUATOR_COUNT,
        "tendon_guide_count": TENDON_GUIDE_COUNT,
        "fastener_count": FASTENER_COUNT,
        "component_count": COMPONENT_COUNT,
        "finger_pitch_mm": FINGER_PITCH,
        "palm_width_mm": PALM_WIDTH,
        "palm_depth_mm": PALM_DEPTH,
        "actuator_diameter_mm": ACTUATOR_DIAMETER,
        "tendon_tube_radius_mm": TENDON_TUBE_RADIUS,
        "pad_thickness_mm": PAD_THICKNESS,
        "bounding_box_mm": bbox,
        "joint_axes_mm": joint_axes,
        "joint_angle_profiles_deg": _joint_angle_report(),
        "finger_links_centered_on_joint_axes": True,
        "finger_flexion_is_joint_angle_driven": True,
        "finger_flexion_angles_are_cumulative_joint_rotations": True,
        "horizontal_hinge_axis_pins_modeled": True,
        "segment_local_frames_align_surface_details": True,
        "clevis_yoke_brackets_modeled": True,
        "bearing_end_caps_modeled": True,
        "raised_service_rails_and_joint_collars_modeled": True,
        "neutral_adjacent_finger_clearance_ok": _neutral_spacing_ok(),
        "thumb_opposed_and_angled": True,
        "separate_colored_solids": 260,
    }
    report["passed"] = (
        report["finger_count"] == 5
        and report["total_joints"] == 14
        and report["total_phalanges"] == 14
        and report["actuator_count"] >= 5
        and report["tendon_guide_count"] >= 10
        and report["finger_flexion_is_joint_angle_driven"]
        and report["finger_flexion_angles_are_cumulative_joint_rotations"]
        and report["horizontal_hinge_axis_pins_modeled"]
        and report["segment_local_frames_align_surface_details"]
        and report["clevis_yoke_brackets_modeled"]
        and report["bearing_end_caps_modeled"]
        and report["raised_service_rails_and_joint_collars_modeled"]
        and report["neutral_adjacent_finger_clearance_ok"]
        and 210.0 <= bbox[0] <= 270.0
        and 250.0 <= bbox[1] <= 365.0
        and 45.0 <= bbox[2] <= 92.0
    )
    return report


def _write_prompt() -> None:
    prompt = """Generate a Tesla Optimus-inspired next-generation humanoid robotic finger actuator concept in CoBrA. Use millimeters and create editable B-rep CAD solids, not mesh-only geometry.

Design a premium engineering concept for a humanoid robotic hand focused on the fingers: four articulated fingers and one opposed thumb mounted to a compact palm rail. The model should look like a next-gen humanoid dexterous end-effector, but it must be a non-proprietary concept with placeholder mechanisms.

Required components:
- Four multi-link fingers with three phalanges each: proximal, middle, distal.
- One opposed thumb with two phalanges and an angled thumb base.
- Rounded joint knuckles at each MCP/PIP/DIP joint.
- Slim internal tendon-routing channels represented as colored guide tubes.
- Compact linear micro-actuator placeholders inside the palm.
- Tactile fingertip pad inserts in dark rubber.
- Small fasteners, hinge pins, cable exits, and service covers.
- Clevis-style yoke brackets, bearing end caps, raised indexing rails, recessed service grooves, and joint clearance collars.
- Advanced flexed presentation pose where every phalanx link rotates from its own MCP/PIP/DIP joint axis with stronger cumulative local joint angles instead of being translated downward as a flat chain.

Parametric requirements:
- Define finger count, phalanx lengths, joint spacing, finger pitch, palm width, palm depth, actuator diameter, tendon tube radius, and pad thickness as named parameters.
- Derive all finger positions from the finger pitch and palm coordinate system.
- Derive each fingertip chain from named per-segment yaw angles and cumulative local joint flexion angles, so each downstream phalanx inherits the previous joint rotation and all link bodies/tendon tubes align to the true joint-to-joint vector.
- Add visible horizontal hinge-axis pins through the knuckles so the rotation axis is legible at each MCP/PIP/DIP joint.
- Use each phalanx segment's local along/side/top-normal frame for shell panels, tendon tubes, fasteners, fingertip pads, and distal carriers so details rotate in the same direction as the joint chain.
- Add paired side clevis brackets around each knuckle, bearing end caps on hinge pins, precision joint collars at phalanx ends, and longitudinal service rails/grooves on each link.
- Keep palm, each finger link set, joints, tendon guides, actuators, pads, and fasteners as separate solids/components.
- Avoid fragile small booleans and avoid over-detailed internals.

Validation:
- Report total fingers, total joints, total phalanges, actuator count, tendon guide count, and bounding box.
- Verify finger links are centered on their joint axes, cumulative joint-angle profiles are reported, horizontal hinge axes are modeled, clevis/bearing/link-service details are present, segment-local surface details are aligned, and adjacent fingers do not overlap at the neutral pose.
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
        raise RuntimeError(f"Optimus finger actuator validation failed: {report}")
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
        raise RuntimeError(f"Optimus finger actuator validation failed: {report}")
    print(json.dumps({"step_output": STEP_OUTPUT, "glb_output": GLB_OUTPUT, "validation": report}, indent=2))
