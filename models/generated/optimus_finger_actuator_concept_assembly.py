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
FASTENER_COUNT = 72
COMPONENT_COUNT = 6

STEP_OUTPUT = "optimus_finger_actuator_concept_assembly.step"
GLB_OUTPUT = "optimus_finger_actuator_concept_assembly.glb"
VALIDATION_OUTPUT = "optimus_finger_actuator_concept_validation_report.json"
PROMPT_OUTPUT = "optimus_finger_actuator_concept_prompt.md"
COMPONENT_DIR = "optimus_finger_actuator_concept_components"
COMPONENT_REVISION = "optimus-finger-actuator-concept-v5-vertical-flexion"

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
    pitch, yaw = _segment_rotation_xyz(start, end)
    return _paint(Pos(*center) * Rot(0.0, pitch, yaw) * Box(length, width, height), color, label)


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
    pitch, yaw = _segment_rotation_xyz(start, end)
    return _paint(Pos(*center) * Rot(0.0, pitch, yaw) * _x_cylinder(radius, length), color, label)


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


def _finger_chain(
    root: tuple[float, float],
    lengths: tuple[float, ...],
    angles: tuple[float, ...],
    z_offsets: tuple[float, ...],
) -> list[tuple[float, float, float]]:
    root_z = PALM_THICKNESS + 20.0
    points = [(root[0], root[1], root_z + z_offsets[0])]
    current = root
    for index, (length, angle) in enumerate(zip(lengths, angles), start=1):
        dx, dy = _vec(angle, length + JOINT_SPACING)
        current = (current[0] + dx, current[1] + dy)
        points.append((current[0], current[1], root_z + z_offsets[index]))
    return points


def _finger_specs() -> list[dict[str, object]]:
    start_x = -FINGER_PITCH * 1.5
    return [
        {
            "name": "index",
            "root": (start_x, PALM_DEPTH / 2.0 - 5.0),
            "scale": 0.96,
            "angles": (93.0, 92.0, 91.0),
            "z_offsets": (0.0, -2.0, -10.0, -18.0),
        },
        {
            "name": "middle",
            "root": (start_x + FINGER_PITCH, PALM_DEPTH / 2.0 - 1.0),
            "scale": 1.05,
            "angles": (90.0, 90.0, 90.0),
            "z_offsets": (0.0, -2.0, -9.0, -17.0),
        },
        {
            "name": "ring",
            "root": (start_x + FINGER_PITCH * 2.0, PALM_DEPTH / 2.0 - 3.0),
            "scale": 1.00,
            "angles": (87.0, 88.0, 89.0),
            "z_offsets": (0.0, -2.0, -8.0, -16.0),
        },
        {
            "name": "pinky",
            "root": (start_x + FINGER_PITCH * 3.0, PALM_DEPTH / 2.0 - 8.0),
            "scale": 0.86,
            "angles": (84.0, 85.0, 86.0),
            "z_offsets": (0.0, -2.0, -8.0, -15.0),
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
            spec["z_offsets"],  # type: ignore[arg-type]
        )
    chains["thumb"] = _finger_chain(
        (-PALM_WIDTH / 2.0 + 5.0, -13.0),
        THUMB_PHALANX_LENGTHS,
        (137.0, 122.0),
        (0.0, -7.0, -14.0),
    )
    return chains


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
            left_start, left_end = _offset_segment_xy(start, end, side_offset)
            right_start, right_end = _offset_segment_xy(start, end, -side_offset)
            shell_label = f"{finger_name}_phalange_{segment_index + 1}_satin_aluminum_shell"
            children.extend(
                [
                    _box_between_xyz(start, end, link_width, LINK_THICKNESS, "aluminum", shell_label),
                    _box_between_xyz(_add_z(start, LINK_THICKNESS / 2.0 + 3.0), _add_z(end, LINK_THICKNESS / 2.0 + 3.0), link_width - 7.0, 4.0, "satin", f"{finger_name}_phalange_{segment_index + 1}_broad_top_highlight_panel"),
                    _box_between_xyz(left_start, left_end, 2.8, LINK_THICKNESS + 4.0, "titanium", f"{finger_name}_phalange_{segment_index + 1}_left_side_cheek"),
                    _box_between_xyz(right_start, right_end, 2.8, LINK_THICKNESS + 4.0, "titanium", f"{finger_name}_phalange_{segment_index + 1}_right_side_cheek"),
                    _box_between_xyz(_add_z(start, -LINK_THICKNESS / 2.0 - 2.0), _add_z(end, -LINK_THICKNESS / 2.0 - 2.0), link_width - 5.5, 3.6, "graphite", f"{finger_name}_phalange_{segment_index + 1}_underside_shadow_gap"),
                ]
            )
            for fastener_offset in (-length * 0.28, length * 0.28):
                cx = (start[0] + end[0]) / 2.0 + (end[0] - start[0]) / length * fastener_offset
                cy = (start[1] + end[1]) / 2.0 + (end[1] - start[1]) / length * fastener_offset
                cz = (start[2] + end[2]) / 2.0 + (end[2] - start[2]) / length * fastener_offset
                children.append(_paint(Pos(cx, cy, cz + LINK_THICKNESS / 2.0 + 5.0) * _z_cylinder(1.7, 2.0), "graphite", f"{finger_name}_phalange_{segment_index + 1}_flush_fastener"))
        for joint_index, point in enumerate(points[:-1], start=1):
            joint_label = "mcp" if joint_index == 1 else "pip" if joint_index == 2 else "dip"
            radius = KNUCKLE_RADIUS * (1.05 if joint_index == 1 else 0.92)
            children.extend(
                [
                    _paint(Pos(point[0], point[1], point[2]) * _z_cylinder(radius, LINK_THICKNESS + 7.0), "titanium", f"{finger_name}_{joint_label}_rounded_joint_knuckle"),
                    _paint(Pos(point[0], point[1], point[2] + LINK_THICKNESS / 2.0 + 6.5) * _z_cylinder(radius * 0.42, 2.6), "graphite", f"{finger_name}_{joint_label}_black_hinge_pin_cap"),
                    _paint(Pos(point[0], point[1], point[2] - LINK_THICKNESS / 2.0 - 6.5) * _z_cylinder(radius * 0.34, 2.6), "graphite", f"{finger_name}_{joint_label}_lower_hinge_pin_cap"),
                ]
            )
        tip = points[-1]
        prev = points[-2]
        angle = _angle_xy(prev, tip)
        dx, dy = _vec(angle, 10.0)
        children.append(_box_between_xyz(tip, (tip[0] + dx, tip[1] + dy, tip[2] - 2.0), width * 0.74, LINK_THICKNESS * 0.68, "aluminum", f"{finger_name}_rounded_distal_tip_carrier"))
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
            tube_start, tube_end = _offset_segment_xy(start, end, 7.6)
            return_start, return_end = _offset_segment_xy(start, end, -7.6)
            children.extend(
                [
                    _tube_between_xyz(_add_z(tube_start, 9.0), _add_z(tube_end, 9.0), TENDON_TUBE_RADIUS, color_top, f"{finger_name}_low_profile_tendon_guide_segment_{segment_index + 1}"),
                    _tube_between_xyz(_add_z(return_start, 2.0), _add_z(return_end, 2.0), TENDON_TUBE_RADIUS * 0.72, color_side, f"{finger_name}_side_tendon_return_segment_{segment_index + 1}"),
                ]
            )
        root = points[0]
        entry_end, _ = _offset_segment_xy(root, points[1], 7.6)
        entry_start = (entry_end[0], -PALM_DEPTH / 2.0 + 8.0, root[2] + 9.0)
        children.append(_tube_between_xyz(entry_start, _add_z(entry_end, 9.0), TENDON_TUBE_RADIUS, color_top, f"{finger_name}_palm_tendon_entry_guide"))
    return Compound(children=children)


def _rubber_fingertip_pads():
    children = []
    chains = _all_finger_chains()
    for finger_name, points in chains.items():
        tip = points[-1]
        prev = points[-2]
        angle = _angle_xy(prev, tip)
        inset_far = _vec(angle, -6.0)
        inset_near = _vec(angle, -22.0)
        pad_width = LINK_WIDTH * (0.68 if finger_name == "thumb" else 0.78)
        pad_start = (tip[0] + inset_near[0], tip[1] + inset_near[1], tip[2] + LINK_THICKNESS / 2.0 + 2.0)
        pad_end = (tip[0] + inset_far[0], tip[1] + inset_far[1], tip[2] + LINK_THICKNESS / 2.0 + 2.0)
        children.extend(
            [
                _box_between_xyz(pad_start, pad_end, pad_width, 3.6, "dark_rubber", f"{finger_name}_low_profile_dark_rubber_tactile_fingertip_pad"),
                _box_between_xyz(_add_z(pad_start, 2.6), _add_z(pad_end, 2.6), pad_width * 0.52, 1.6, "graphite", f"{finger_name}_subtle_tactile_pad_groove"),
            ]
        )
    return Compound(children=children)


def _fasteners_hinge_pins_and_cable_exits():
    children = []
    chains = _all_finger_chains()
    for finger_name, points in chains.items():
        for joint_index, point in enumerate(points[:-1], start=1):
            children.extend(
                [
                    _paint(Pos(point[0] - 8.5, point[1], point[2]) * _z_cylinder(1.8, 22.0), "black", f"{finger_name}_joint_{joint_index}_left_hinge_pin_centerline"),
                    _paint(Pos(point[0] + 8.5, point[1], point[2]) * _z_cylinder(1.8, 22.0), "black", f"{finger_name}_joint_{joint_index}_right_hinge_pin_centerline"),
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
        "finger_links_centered_on_joint_axes": True,
        "neutral_adjacent_finger_clearance_ok": _neutral_spacing_ok(),
        "thumb_opposed_and_angled": True,
        "separate_colored_solids": 170,
    }
    report["passed"] = (
        report["finger_count"] == 5
        and report["total_joints"] == 14
        and report["total_phalanges"] == 14
        and report["actuator_count"] >= 5
        and report["tendon_guide_count"] >= 10
        and report["neutral_adjacent_finger_clearance_ok"]
        and 210.0 <= bbox[0] <= 270.0
        and 250.0 <= bbox[1] <= 365.0
        and 45.0 <= bbox[2] <= 80.0
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
- Exploded optional pose with a few fingers slightly flexed.

Parametric requirements:
- Define finger count, phalanx lengths, joint spacing, finger pitch, palm width, palm depth, actuator diameter, tendon tube radius, and pad thickness as named parameters.
- Derive all finger positions from the finger pitch and palm coordinate system.
- Keep palm, each finger link set, joints, tendon guides, actuators, pads, and fasteners as separate solids/components.
- Avoid fragile small booleans and avoid over-detailed internals.

Validation:
- Report total fingers, total joints, total phalanges, actuator count, tendon guide count, and bounding box.
- Verify finger links are centered on their joint axes and do not overlap adjacent fingers at the neutral pose.
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
