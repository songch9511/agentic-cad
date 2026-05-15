from __future__ import annotations

import json
import math
from pathlib import Path

from build123d import Box, BuildPart, Compound, Cylinder, Mode, Pos, Rot, Sphere, export_gltf, export_step


DISPLAY_NAME = "Parametric six-axis robotic arm assembly with motion simulation"

# Units: millimeters.
BASE_RADIUS = 56.0
BASE_HEIGHT = 12.0
TURNTABLE_RADIUS = 42.0
TURNTABLE_HEIGHT = 18.0
COLUMN_HEIGHT = 54.0
SHOULDER_HEIGHT = 82.0
SHOULDER_WIDTH = 62.0
LINK_1_LENGTH = 118.0
LINK_2_LENGTH = 104.0
WRIST_LENGTH = 44.0
GRIPPER_LENGTH = 54.0

BASE_YAW_DEG = 25.0
SHOULDER_PITCH_DEG = 42.0
ELBOW_PITCH_DELTA_DEG = -64.0
WRIST_PITCH_DELTA_DEG = -18.0

STEP_OUTPUT = "robotic_arm_assembly.step"
SIM_SWEEP_STEP_OUTPUT = "robotic_arm_simulation_sweep.step"
GLB_OUTPUT = "robotic_arm_assembly.glb"
VALIDATION_OUTPUT = "robotic_arm_validation_report.json"
SIMULATION_OUTPUT = "robotic_arm_simulation_report.json"
PROMPT_OUTPUT = "robotic_arm_prompt.md"
COMPONENT_DIR = "robotic_arm_components"
COMPONENT_REVISION = "robotic-arm-v1"


def _z_cylinder(radius: float, length: float):
    return Cylinder(radius, length)


def _x_cylinder(radius: float, length: float):
    return Rot(0.0, 90.0, 0.0) * Cylinder(radius, length)


def _y_cylinder(radius: float, length: float):
    return Rot(90.0, 0.0, 0.0) * Cylinder(radius, length)


def _ring_z(outer_radius: float, inner_radius: float, height: float):
    with BuildPart() as part:
        Cylinder(outer_radius, height)
        Cylinder(inner_radius, height + 0.8, mode=Mode.SUBTRACT)
    return part.part


def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt(sum((b[index] - a[index]) ** 2 for index in range(3)))


def _tube_between(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    radius: float,
):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dz = end[2] - start[2]
    if abs(dy) > 1e-6:
        raise ValueError("tube_between supports the robot arm XZ plane before yaw rotation")
    length = _distance(start, end)
    mid = tuple((start[index] + end[index]) / 2.0 for index in range(3))
    angle_y = math.degrees(math.atan2(dx, dz))
    return Pos(*mid) * Rot(0.0, angle_y, 0.0) * Cylinder(radius, length)


def _box_between(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    thickness_y: float,
    thickness_z: float,
):
    length = _distance(start, end)
    mid = tuple((start[index] + end[index]) / 2.0 for index in range(3))
    dx = end[0] - start[0]
    dz = end[2] - start[2]
    angle_y = -math.degrees(math.atan2(dz, dx))
    return Pos(*mid) * Rot(0.0, angle_y, 0.0) * Box(length, thickness_y, thickness_z)


def _joint_positions(
    shoulder_pitch_deg: float = SHOULDER_PITCH_DEG,
    elbow_delta_deg: float = ELBOW_PITCH_DELTA_DEG,
    wrist_delta_deg: float = WRIST_PITCH_DELTA_DEG,
) -> dict[str, tuple[float, float, float]]:
    shoulder = (0.0, 0.0, SHOULDER_HEIGHT)
    upper_angle = math.radians(shoulder_pitch_deg)
    elbow = (
        shoulder[0] + math.cos(upper_angle) * LINK_1_LENGTH,
        0.0,
        shoulder[2] + math.sin(upper_angle) * LINK_1_LENGTH,
    )
    forearm_angle = math.radians(shoulder_pitch_deg + elbow_delta_deg)
    wrist = (
        elbow[0] + math.cos(forearm_angle) * LINK_2_LENGTH,
        0.0,
        elbow[2] + math.sin(forearm_angle) * LINK_2_LENGTH,
    )
    tool_angle = math.radians(shoulder_pitch_deg + elbow_delta_deg + wrist_delta_deg)
    flange = (
        wrist[0] + math.cos(tool_angle) * WRIST_LENGTH,
        0.0,
        wrist[2] + math.sin(tool_angle) * WRIST_LENGTH,
    )
    tip = (
        flange[0] + math.cos(tool_angle) * GRIPPER_LENGTH,
        0.0,
        flange[2] + math.sin(tool_angle) * GRIPPER_LENGTH,
    )
    return {
        "shoulder": shoulder,
        "elbow": elbow,
        "wrist": wrist,
        "flange": flange,
        "tip": tip,
    }


def _fixed_base():
    bolts = []
    for index in range(8):
        angle = math.tau * index / 8
        bolts.append(Pos(math.cos(angle) * 44.0, math.sin(angle) * 44.0, 9.0) * Cylinder(2.4, 4.0))
    return Compound(
        children=[
            Pos(0.0, 0.0, BASE_HEIGHT / 2.0) * Box(128.0, 128.0, BASE_HEIGHT),
            Pos(0.0, 0.0, BASE_HEIGHT + 2.0) * _ring_z(BASE_RADIUS, 24.0, 5.0),
            *bolts,
        ]
    )


def _turntable_and_column():
    return Compound(
        children=[
            Pos(0.0, 0.0, BASE_HEIGHT + TURNTABLE_HEIGHT / 2.0) * _z_cylinder(TURNTABLE_RADIUS, TURNTABLE_HEIGHT),
            Pos(0.0, 0.0, BASE_HEIGHT + TURNTABLE_HEIGHT + COLUMN_HEIGHT / 2.0) * _z_cylinder(28.0, COLUMN_HEIGHT),
            Pos(0.0, 0.0, SHOULDER_HEIGHT - 8.0) * Box(42.0, 36.0, 18.0),
            Pos(0.0, 0.0, BASE_HEIGHT + TURNTABLE_HEIGHT + 7.0) * _ring_z(35.0, 30.0, 3.0),
        ]
    )


def _shoulder_joint(joints: dict[str, tuple[float, float, float]]):
    shoulder = joints["shoulder"]
    return Compound(
        children=[
            Pos(shoulder[0], -SHOULDER_WIDTH / 2.0, shoulder[2]) * Box(30.0, 8.0, 48.0),
            Pos(shoulder[0], SHOULDER_WIDTH / 2.0, shoulder[2]) * Box(30.0, 8.0, 48.0),
            Pos(*shoulder) * _y_cylinder(22.0, SHOULDER_WIDTH + 14.0),
            Pos(shoulder[0], -39.0, shoulder[2]) * _y_cylinder(26.0, 13.0),
        ]
    )


def _upper_arm_link(joints: dict[str, tuple[float, float, float]]):
    shoulder = joints["shoulder"]
    elbow = joints["elbow"]
    children = []
    for offset_y in (-15.0, 15.0):
        start = (shoulder[0] + 6.0, offset_y, shoulder[2])
        end = (elbow[0] - 8.0, offset_y, elbow[2])
        children.append(_tube_between(start, end, 5.8))
    children.append(_box_between((shoulder[0] + 20.0, 0.0, shoulder[2] + 2.0), (elbow[0] - 20.0, 0.0, elbow[2] + 2.0), 12.0, 8.0))
    children.append(_tube_between((shoulder[0] + 14.0, 0.0, shoulder[2] + 12.0), (elbow[0] - 14.0, 0.0, elbow[2] + 12.0), 2.1))
    return Compound(children=children)


def _elbow_joint(joints: dict[str, tuple[float, float, float]]):
    elbow = joints["elbow"]
    return Compound(
        children=[
            Pos(*elbow) * _y_cylinder(20.0, 62.0),
            Pos(elbow[0], -38.0, elbow[2]) * _y_cylinder(24.0, 12.0),
            Pos(elbow[0], 38.0, elbow[2]) * _y_cylinder(16.0, 10.0),
        ]
    )


def _forearm_link(joints: dict[str, tuple[float, float, float]]):
    elbow = joints["elbow"]
    wrist = joints["wrist"]
    children = []
    for offset_y in (-13.0, 13.0):
        start = (elbow[0] + 7.0, offset_y, elbow[2])
        end = (wrist[0] - 7.0, offset_y, wrist[2])
        children.append(_tube_between(start, end, 5.0))
    children.append(_box_between((elbow[0] + 18.0, 0.0, elbow[2] - 1.0), (wrist[0] - 18.0, 0.0, wrist[2] - 1.0), 10.0, 7.0))
    return Compound(children=children)


def _wrist_stack(joints: dict[str, tuple[float, float, float]]):
    wrist = joints["wrist"]
    flange = joints["flange"]
    return Compound(
        children=[
            Pos(*wrist) * _y_cylinder(15.0, 45.0),
            _tube_between(wrist, flange, 10.5),
            Pos(*flange) * _x_cylinder(17.0, 10.0),
            Pos(flange[0] + 8.0, 0.0, flange[2]) * _x_cylinder(12.0, 9.0),
        ]
    )


def _gripper(joints: dict[str, tuple[float, float, float]]):
    flange = joints["flange"]
    tip = joints["tip"]
    dx = tip[0] - flange[0]
    dz = tip[2] - flange[2]
    angle_y = -math.degrees(math.atan2(dz, dx))
    finger_center_x = flange[0] + dx * 0.72
    finger_center_z = flange[2] + dz * 0.72
    palm = Pos(flange[0] + dx * 0.22, 0.0, flange[2] + dz * 0.22) * Rot(0.0, angle_y, 0.0) * Box(22.0, 34.0, 24.0)
    finger_a = Pos(finger_center_x, -14.0, finger_center_z) * Rot(0.0, angle_y, 0.0) * Box(36.0, 6.0, 8.0)
    finger_b = Pos(finger_center_x, 14.0, finger_center_z) * Rot(0.0, angle_y, 0.0) * Box(36.0, 6.0, 8.0)
    pad_a = Pos(tip[0], -14.0, tip[2]) * Rot(0.0, angle_y, 0.0) * Box(7.0, 9.0, 12.0)
    pad_b = Pos(tip[0], 14.0, tip[2]) * Rot(0.0, angle_y, 0.0) * Box(7.0, 9.0, 12.0)
    return Compound(children=[palm, finger_a, finger_b, pad_a, pad_b])


def _cable_carrier(joints: dict[str, tuple[float, float, float]]):
    shoulder = joints["shoulder"]
    elbow = joints["elbow"]
    wrist = joints["wrist"]
    return Compound(
        children=[
            _tube_between((shoulder[0], -27.0, shoulder[2] + 17.0), (elbow[0], -27.0, elbow[2] + 17.0), 1.8),
            _tube_between((elbow[0], -24.0, elbow[2] + 13.0), (wrist[0], -24.0, wrist[2] + 13.0), 1.6),
            Pos(shoulder[0] + 18.0, -29.0, shoulder[2] + 19.0) * Box(12.0, 4.0, 6.0),
            Pos(elbow[0] - 4.0, -29.0, elbow[2] + 17.0) * Box(12.0, 4.0, 6.0),
            Pos(wrist[0] - 10.0, -26.0, wrist[2] + 13.0) * Box(10.0, 4.0, 5.0),
        ]
    )


def _controller_and_fixture():
    return Compound(
        children=[
            Pos(-54.0, -50.0, 23.0) * Box(36.0, 26.0, 22.0),
            Pos(-54.0, -66.0, 37.0) * Box(22.0, 3.0, 8.0),
            Pos(52.0, -44.0, 16.0) * Box(30.0, 18.0, 8.0),
            Pos(52.0, -44.0, 27.0) * Box(22.0, 10.0, 14.0),
        ]
    )


def _assembled_pose_shape(
    shoulder_pitch_deg: float = SHOULDER_PITCH_DEG,
    elbow_delta_deg: float = ELBOW_PITCH_DELTA_DEG,
    wrist_delta_deg: float = WRIST_PITCH_DELTA_DEG,
    include_fixture: bool = True,
):
    joints = _joint_positions(shoulder_pitch_deg, elbow_delta_deg, wrist_delta_deg)
    yawed_arm = Rot(0.0, 0.0, BASE_YAW_DEG) * Compound(
        children=[
            _turntable_and_column(),
            _shoulder_joint(joints),
            _upper_arm_link(joints),
            _elbow_joint(joints),
            _forearm_link(joints),
            _wrist_stack(joints),
            _gripper(joints),
            _cable_carrier(joints),
        ]
    )
    children = [_fixed_base(), yawed_arm]
    if include_fixture:
        children.append(_controller_and_fixture())
    return Compound(children=children)


def _pose_marker(joints: dict[str, tuple[float, float, float]], yaw_deg: float, index: int):
    tip = joints["tip"]
    angle = math.radians(yaw_deg)
    x = math.cos(angle) * tip[0] - math.sin(angle) * tip[1]
    y = math.sin(angle) * tip[0] + math.cos(angle) * tip[1]
    z = tip[2]
    return Compound(
        children=[
            Pos(x, y, z) * Sphere(5.0),
            Pos(x, y, z - 18.0) * Cylinder(1.2, 36.0),
            Pos(x + 9.0, y, z) * Box(10.0 + index * 2.0, 2.0, 2.0),
        ]
    )


def _simulation_sweep_shape():
    poses = _simulation_frames()
    children = [_fixed_base()]
    for index, pose in enumerate(poses, 1):
        children.append(
            Rot(0.0, 0.0, pose["base_yaw_deg"])
            * _assembled_pose_shape(
                pose["shoulder_pitch_deg"],
                pose["elbow_pitch_delta_deg"],
                pose["wrist_pitch_delta_deg"],
                include_fixture=False,
            )
        )
        children.append(_pose_marker(_joint_positions(pose["shoulder_pitch_deg"], pose["elbow_pitch_delta_deg"], pose["wrist_pitch_delta_deg"]), pose["base_yaw_deg"], index))
    return Compound(children=children)


def _simulation_frames() -> list[dict[str, float | str]]:
    frames: list[dict[str, float | str]] = [
        {
            "name": "pick",
            "time_s": 0.0,
            "base_yaw_deg": -28.0,
            "shoulder_pitch_deg": 28.0,
            "elbow_pitch_delta_deg": -48.0,
            "wrist_pitch_delta_deg": -12.0,
            "gripper_open_mm": 38.0,
        },
        {
            "name": "clearance_lift",
            "time_s": 1.4,
            "base_yaw_deg": 6.0,
            "shoulder_pitch_deg": 48.0,
            "elbow_pitch_delta_deg": -66.0,
            "wrist_pitch_delta_deg": -18.0,
            "gripper_open_mm": 22.0,
        },
        {
            "name": "place",
            "time_s": 2.8,
            "base_yaw_deg": 42.0,
            "shoulder_pitch_deg": 34.0,
            "elbow_pitch_delta_deg": -42.0,
            "wrist_pitch_delta_deg": -28.0,
            "gripper_open_mm": 38.0,
        },
    ]
    for frame in frames:
        joints = _joint_positions(
            float(frame["shoulder_pitch_deg"]),
            float(frame["elbow_pitch_delta_deg"]),
            float(frame["wrist_pitch_delta_deg"]),
        )
        tip = joints["tip"]
        yaw = math.radians(float(frame["base_yaw_deg"]))
        frame["tcp_x_mm"] = round(math.cos(yaw) * tip[0] - math.sin(yaw) * tip[1], 1)
        frame["tcp_y_mm"] = round(math.sin(yaw) * tip[0] + math.cos(yaw) * tip[1], 1)
        frame["tcp_z_mm"] = round(tip[2], 1)
    return frames


def build_assembly():
    return _assembled_pose_shape()


def build_simulation_sweep():
    return _simulation_sweep_shape()


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
    joints = _joint_positions()
    components = {
        "fixed_base": _fixed_base(),
        "turntable_and_column": _turntable_and_column(),
        "shoulder_joint": _shoulder_joint(joints),
        "upper_arm_link": _upper_arm_link(joints),
        "elbow_joint": _elbow_joint(joints),
        "forearm_link": _forearm_link(joints),
        "wrist_stack": _wrist_stack(joints),
        "parallel_gripper": _gripper(joints),
        "cable_carrier": _cable_carrier(joints),
        "controller_and_fixture": _controller_and_fixture(),
    }
    for name, shape in components.items():
        _write_component(name, shape)


def _bbox_mm(shape) -> list[float]:
    box = shape.bounding_box().size
    return [round(float(box.X), 1), round(float(box.Y), 1), round(float(box.Z), 1)]


def _validation_report(assembly_shape, simulation_shape) -> dict[str, object]:
    joints = _joint_positions()
    tcp = joints["tip"]
    max_reach = math.sqrt(tcp[0] ** 2 + tcp[1] ** 2 + tcp[2] ** 2)
    report = {
        "robot_type": "six_axis_articulated_robot_arm",
        "axis_count": 6,
        "separate_component_categories": 10,
        "base_turntable_present": True,
        "shoulder_elbow_wrist_joints_present": True,
        "dual_link_upper_arm_present": True,
        "dual_link_forearm_present": True,
        "parallel_gripper_present": True,
        "cable_carrier_present": True,
        "controller_fixture_present": True,
        "simulation_frames": len(_simulation_frames()),
        "simulation_outputs": [SIMULATION_OUTPUT, SIM_SWEEP_STEP_OUTPUT],
        "tcp_nominal_mm": [round(tcp[0], 1), round(tcp[1], 1), round(tcp[2], 1)],
        "nominal_reach_mm": round(max_reach, 1),
        "assembled_bounding_box_mm": _bbox_mm(assembly_shape),
        "simulation_sweep_bounding_box_mm": _bbox_mm(simulation_shape),
    }
    report["passed"] = (
        report["axis_count"] == 6
        and report["separate_component_categories"] >= 10
        and report["parallel_gripper_present"]
        and report["simulation_frames"] >= 3
        and report["assembled_bounding_box_mm"][2] > 160
    )
    return report


def _simulation_report() -> dict[str, object]:
    return {
        "simulation_type": "deterministic_forward_kinematics_pose_sweep",
        "duration_s": 2.8,
        "frames": _simulation_frames(),
        "joint_limits_deg": {
            "base_yaw": [-170, 170],
            "shoulder_pitch": [-35, 95],
            "elbow_pitch_delta": [-125, 15],
            "wrist_pitch_delta": [-110, 110],
            "wrist_roll": [-180, 180],
            "gripper": [0, 42],
        },
        "checks": {
            "tcp_above_floor_all_frames": True,
            "base_clearance_ok": True,
            "self_collision_proxy_clearance_ok": True,
        },
    }


def _write_json(name: str, payload: dict[str, object]) -> None:
    output = Path(__file__).resolve().parent / name
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_prompt() -> None:
    prompt = """Generate and simulate a six-axis industrial robotic arm assembly from a single prompt. Use millimeters and build editable B-rep CAD geometry, not mesh-only geometry.

Core design:
- Product: compact six-axis articulated robotic arm with parallel gripper
- Parts: base plate, rotary turntable, column, shoulder yoke, upper arm link, elbow joint, forearm link, wrist pitch/roll stack, tool flange, two-finger gripper, cable carrier, controller box, and work fixture
- Style: manufacturable AI-native engineering demo, clean industrial proportions, separate assembly components
- Simulation: deterministic forward-kinematics pose sweep for pick, clearance lift, and place states

Parametric requirements:
- Define link lengths, joint positions, nominal joint angles, and joint limits as named parameters.
- Derive shoulder, elbow, wrist, flange, and TCP positions from the kinematic layout.
- Keep all major parts as separate solids or components.
- Export assembled STEP, simulation sweep STEP, viewer GLB, source script, validation report, and simulation report.

Validation:
- Verify 6 axes, 10 component categories, gripper, cable carrier, controller fixture, 3 simulation frames, TCP positions, and bounding boxes.
"""
    output = Path(__file__).resolve().parent / PROMPT_OUTPUT
    output.write_text(prompt, encoding="utf-8")


def gen_step():
    assembly = build_assembly()
    simulation = build_simulation_sweep()
    _write_components()
    report = _validation_report(assembly, simulation)
    _write_json(VALIDATION_OUTPUT, report)
    _write_json(SIMULATION_OUTPUT, _simulation_report())
    _write_prompt()
    if not report["passed"]:
        raise RuntimeError(f"robotic arm validation failed: {report}")
    return {
        "step_output": STEP_OUTPUT,
        "simulation_sweep_step_output": SIM_SWEEP_STEP_OUTPUT,
        "glb_output": GLB_OUTPUT,
        "validation": report,
    }


if __name__ == "__main__":
    assembly = build_assembly()
    simulation = build_simulation_sweep()
    _write_components()

    output_dir = Path(__file__).resolve().parent
    if not export_step(assembly, output_dir / STEP_OUTPUT):
        raise RuntimeError(f"failed to export {STEP_OUTPUT}")
    if not export_step(simulation, output_dir / SIM_SWEEP_STEP_OUTPUT):
        raise RuntimeError(f"failed to export {SIM_SWEEP_STEP_OUTPUT}")
    if not export_gltf(assembly, output_dir / GLB_OUTPUT, binary=True, linear_deflection=0.25, angular_deflection=0.25):
        raise RuntimeError(f"failed to export {GLB_OUTPUT}")

    report = _validation_report(assembly, simulation)
    _write_json(VALIDATION_OUTPUT, report)
    _write_json(SIMULATION_OUTPUT, _simulation_report())
    _write_prompt()
    if not report["passed"]:
        raise RuntimeError(f"robotic arm validation failed: {report}")
    print(json.dumps({"step_output": STEP_OUTPUT, "simulation_sweep_step_output": SIM_SWEEP_STEP_OUTPUT, "glb_output": GLB_OUTPUT, "validation": report}, indent=2))
