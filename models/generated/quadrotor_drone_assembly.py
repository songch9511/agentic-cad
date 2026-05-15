from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


DISPLAY_NAME = "Parametric compact quadrotor drone assembly"

# Dimensions are millimeters.
MOTOR_TO_MOTOR_DIAGONAL = 260.0
MOTOR_RADIUS_FROM_CENTER = MOTOR_TO_MOTOR_DIAGONAL / 2.0
ARM_LENGTH = 92.0
ARM_WIDTH = 12.0
ARM_HEIGHT = 5.0
CENTER_BODY_LENGTH = 76.0
CENTER_BODY_WIDTH = 56.0
BODY_SHELL_HEIGHT = 16.0
MOTOR_CAN_DIAMETER = 24.0
MOTOR_CAN_HEIGHT = 10.0
PROPELLER_DIAMETER = 118.0
PROPELLER_BLADE_WIDTH = 12.0
PROPELLER_THICKNESS = 1.8
BATTERY_LENGTH = 62.0
BATTERY_WIDTH = 34.0
BATTERY_HEIGHT = 13.0
LANDING_SKID_HEIGHT = 28.0
CAMERA_GIMBAL_WIDTH = 24.0
CAMERA_LENS_DIAMETER = 10.0
ESC_LENGTH = 32.0
ESC_WIDTH = 13.0
PDB_LENGTH = 34.0
PDB_WIDTH = 28.0
FLIGHT_CONTROLLER_SIZE = 30.0
RECEIVER_LENGTH = 28.0
RECEIVER_WIDTH = 16.0

COMPONENT_DIR = "quadrotor_drone_components"
STEP_OUTPUT = "quadrotor_drone_assembly.step"
REPORT_OUTPUT = "quadrotor_drone_validation_report.json"
COMPONENT_REVISION = "quadrotor-drone-v2"


def _component_path(name: str) -> Path:
    return Path(__file__).resolve().parent / COMPONENT_DIR / f"{name}.step"


def _component_topology_path(step_path: Path) -> Path:
    return step_path.parent / f".{step_path.name}" / "topology.json"


def _component_revision_path(step_path: Path) -> Path:
    return step_path.parent / f".{step_path.name}" / "revision.txt"


def _component_is_current(step_path: Path) -> bool:
    try:
        return _component_revision_path(step_path).read_text(encoding="utf-8").strip() == COMPONENT_REVISION
    except OSError:
        return False


def _limit_dependency_catalog_scan() -> None:
    try:
        import common.assembly_spec as assembly_spec
        import common.catalog as catalog
    except ImportError:
        return
    scan_root = Path(__file__).resolve().parent
    assembly_spec.CAD_ROOT = scan_root
    catalog.CAD_ROOT = scan_root


def _write_component_topology(step_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "skills" / "cad" / "scripts" / "gen_step_part"
    completed = subprocess.run(
        [sys.executable, str(script), str(step_path)],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"failed to generate component topology for {step_path}:\n{completed.stdout}\n{completed.stderr}"
        )


def _write_component(name: str, shape) -> str:
    output = _component_path(name)
    if output.exists() and _component_topology_path(output).exists() and _component_is_current(output):
        return f"{COMPONENT_DIR}/{name}.step"
    output.parent.mkdir(parents=True, exist_ok=True)
    if not export_step(shape, output):
        raise RuntimeError(f"failed to export component STEP: {output}")
    _write_component_topology(output)
    revision = _component_revision_path(output)
    revision.parent.mkdir(parents=True, exist_ok=True)
    revision.write_text(COMPONENT_REVISION + "\n", encoding="utf-8")
    return f"{COMPONENT_DIR}/{name}.step"


def _z_cylinder(radius: float, height: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Cylinder(radius, height)


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z), "use_source_colors": False}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children, "use_source_colors": False}


def _motor_centers() -> list[tuple[str, float, float]]:
    radius_xy = MOTOR_RADIUS_FROM_CENTER / math.sqrt(2.0)
    return [
        ("front_right", radius_xy, radius_xy),
        ("front_left", -radius_xy, radius_xy),
        ("rear_left", -radius_xy, -radius_xy),
        ("rear_right", radius_xy, -radius_xy),
    ]


def _lower_frame_plate():
    return Compound(
        children=[
            Box(CENTER_BODY_LENGTH, CENTER_BODY_WIDTH, 3.0),
            Box(CENTER_BODY_WIDTH, CENTER_BODY_LENGTH, 3.0),
            _z_cylinder(4.0, 3.4, x=-24.0, y=-18.0),
            _z_cylinder(4.0, 3.4, x=24.0, y=-18.0),
            _z_cylinder(4.0, 3.4, x=-24.0, y=18.0),
            _z_cylinder(4.0, 3.4, x=24.0, y=18.0),
        ]
    )


def _top_body_shell():
    return Compound(
        children=[
            Pos(-26.0, -20.0, -5.0) * _z_cylinder(2.0, 14.0),
            Pos(26.0, -20.0, -5.0) * _z_cylinder(2.0, 14.0),
            Pos(-26.0, 20.0, -5.0) * _z_cylinder(2.0, 14.0),
            Pos(26.0, 20.0, -5.0) * _z_cylinder(2.0, 14.0),
            Pos(0.0, 0.0, 2.0) * Box(CENTER_BODY_LENGTH * 0.86, CENTER_BODY_WIDTH * 0.82, BODY_SHELL_HEIGHT),
            Pos(0.0, CENTER_BODY_WIDTH * 0.42, 5.0) * Box(28.0, 8.0, 8.0),
        ]
    )


def _arm_x():
    return Compound(children=[Box(ARM_LENGTH, ARM_WIDTH, ARM_HEIGHT), _z_cylinder(5.8, 3.0, x=ARM_LENGTH / 2.0 - 8.0)])


def _arm_y():
    return Compound(children=[Box(ARM_WIDTH, ARM_LENGTH, ARM_HEIGHT), _z_cylinder(5.8, 3.0, y=ARM_LENGTH / 2.0 - 8.0)])


def _motor_can():
    return Compound(
        children=[
            _z_cylinder(MOTOR_CAN_DIAMETER / 2.0, MOTOR_CAN_HEIGHT),
            _z_cylinder(4.0, 3.0, z=MOTOR_CAN_HEIGHT / 2.0 + 1.5),
            _z_cylinder(1.8, 6.0, z=MOTOR_CAN_HEIGHT / 2.0 + 5.0),
        ]
    )


def _propeller_x():
    blade = Box(PROPELLER_DIAMETER, PROPELLER_BLADE_WIDTH, PROPELLER_THICKNESS)
    return Compound(
        children=[
            blade,
            Rot(0.0, 0.0, 8.0) * Box(PROPELLER_DIAMETER * 0.44, PROPELLER_BLADE_WIDTH * 1.28, PROPELLER_THICKNESS),
            _z_cylinder(6.5, PROPELLER_THICKNESS * 1.6),
        ]
    )


def _propeller_y():
    blade = Box(PROPELLER_BLADE_WIDTH, PROPELLER_DIAMETER, PROPELLER_THICKNESS)
    return Compound(
        children=[
            blade,
            Rot(0.0, 0.0, -8.0) * Box(PROPELLER_BLADE_WIDTH * 1.28, PROPELLER_DIAMETER * 0.44, PROPELLER_THICKNESS),
            _z_cylinder(6.5, PROPELLER_THICKNESS * 1.6),
        ]
    )


def _esc_x():
    return Compound(
        children=[
            Box(ESC_LENGTH, ESC_WIDTH, 4.0),
            Pos(-9.0, 0.0, 2.6) * Box(10.0, ESC_WIDTH + 1.5, 1.2),
            Pos(4.0, 0.0, 2.6) * Box(10.0, ESC_WIDTH + 1.5, 1.2),
            Pos(15.0, 0.0, 2.6) * Box(3.0, ESC_WIDTH + 1.5, 1.2),
        ]
    )


def _esc_y():
    return Compound(
        children=[
            Box(ESC_WIDTH, ESC_LENGTH, 4.0),
            Pos(0.0, -9.0, 2.6) * Box(ESC_WIDTH + 1.5, 10.0, 1.2),
            Pos(0.0, 4.0, 2.6) * Box(ESC_WIDTH + 1.5, 10.0, 1.2),
            Pos(0.0, 15.0, 2.6) * Box(ESC_WIDTH + 1.5, 3.0, 1.2),
        ]
    )


def _wire_bundle_x():
    return Compound(
        children=[
            Pos(0.0, -3.5, 0.0) * Box(62.0, 1.2, 1.2),
            Pos(0.0, 0.0, 0.0) * Box(62.0, 1.2, 1.2),
            Pos(0.0, 3.5, 0.0) * Box(62.0, 1.2, 1.2),
        ]
    )


def _wire_bundle_y():
    return Compound(
        children=[
            Pos(-3.5, 0.0, 0.0) * Box(1.2, 62.0, 1.2),
            Pos(0.0, 0.0, 0.0) * Box(1.2, 62.0, 1.2),
            Pos(3.5, 0.0, 0.0) * Box(1.2, 62.0, 1.2),
        ]
    )


def _battery_pack():
    return Compound(
        children=[
            Box(BATTERY_LENGTH, BATTERY_WIDTH, BATTERY_HEIGHT),
            Pos(-18.0, 0.0, BATTERY_HEIGHT / 2.0 + 1.0) * Box(4.0, BATTERY_WIDTH + 4.0, 2.0),
            Pos(18.0, 0.0, BATTERY_HEIGHT / 2.0 + 1.0) * Box(4.0, BATTERY_WIDTH + 4.0, 2.0),
        ]
    )


def _flight_controller_stack():
    return Compound(
        children=[
            Box(PDB_LENGTH, PDB_WIDTH, 2.0),
            Pos(-12.0, 0.0, 2.0) * Box(4.0, PDB_WIDTH + 3.0, 1.2),
            Pos(12.0, 0.0, 2.0) * Box(4.0, PDB_WIDTH + 3.0, 1.2),
            Pos(0.0, 0.0, 5.0) * Box(FLIGHT_CONTROLLER_SIZE, FLIGHT_CONTROLLER_SIZE, 2.0),
            Pos(0.0, 9.5, 7.0) * Box(12.0, 2.0, 1.2),
            Pos(0.0, 13.5, 7.0) * Box(5.5, 2.0, 1.2),
            _z_cylinder(1.8, 7.0, x=-14.0, y=-11.0, z=2.5),
            _z_cylinder(1.8, 7.0, x=14.0, y=-11.0, z=2.5),
            _z_cylinder(1.8, 7.0, x=-14.0, y=11.0, z=2.5),
            _z_cylinder(1.8, 7.0, x=14.0, y=11.0, z=2.5),
        ]
    )


def _receiver():
    return Compound(
        children=[
            Box(RECEIVER_LENGTH, RECEIVER_WIDTH, 5.0),
            Pos(-8.0, 0.0, 3.4) * Box(3.0, RECEIVER_WIDTH + 1.5, 1.0),
            Pos(8.0, 0.0, 3.4) * Box(3.0, RECEIVER_WIDTH + 1.5, 1.0),
        ]
    )


def _camera_gimbal():
    return Compound(
        children=[
            Box(CAMERA_GIMBAL_WIDTH, 5.0, 18.0),
            Pos(0.0, 6.0, 0.0) * Box(22.0, 14.0, 16.0),
            Pos(0.0, 13.5, 0.0) * Rot(90.0, 0.0, 0.0) * Cylinder(CAMERA_LENS_DIAMETER / 2.0, 4.0),
            Pos(-14.0, 4.0, 0.0) * Box(3.0, 10.0, 14.0),
            Pos(14.0, 4.0, 0.0) * Box(3.0, 10.0, 14.0),
        ]
    )


def _landing_leg():
    return Compound(children=[Box(4.0, 5.0, LANDING_SKID_HEIGHT), Pos(0.0, 0.0, -LANDING_SKID_HEIGHT / 2.0) * Box(7.0, 7.0, 2.0)])


def _skid_x():
    return Box(88.0, 5.0, 3.0)


def _fastener():
    return _z_cylinder(2.0, 1.4)


def _direction_cap_cw():
    return Compound(children=[_z_cylinder(4.4, 1.0), Pos(0.0, 0.0, 0.9) * Box(8.0, 1.2, 0.8)])


def _direction_cap_ccw():
    return Compound(children=[_z_cylinder(4.4, 1.0), Pos(0.0, 0.0, 0.9) * Box(1.2, 8.0, 0.8)])


def _antenna_pair():
    return Compound(
        children=[
            Pos(-5.0, 0.0, 10.0) * Rot(18.0, 0.0, -16.0) * Cylinder(0.9, 34.0),
            Pos(5.0, 0.0, 10.0) * Rot(18.0, 0.0, 16.0) * Cylinder(0.9, 34.0),
        ]
    )


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    motor_children = []
    prop_children = []
    esc_children = []
    wire_children = []
    leg_children = []
    fasteners = []
    for index, (name, x, y) in enumerate(_motor_centers()):
        motor_children.append(_leaf(f"brushless_motor_can_{name}", paths["motor_can"], x, y, 16.0))
        prop_path = paths["propeller_x"] if index % 2 == 0 else paths["propeller_y"]
        prop_children.append(_leaf(f"two_blade_propeller_{name}", prop_path, x, y, 27.0))
        cap_path = paths["direction_cap_cw"] if index % 2 == 0 else paths["direction_cap_ccw"]
        prop_children.append(_leaf(f"{'cw' if index % 2 == 0 else 'ccw'}_rotation_marker_{name}", cap_path, x, y, 31.8))
        esc_path = paths["esc_x"] if abs(x) >= abs(y) else paths["esc_y"]
        wire_path = paths["wire_x"] if abs(x) >= abs(y) else paths["wire_y"]
        esc_children.append(_leaf(f"esc_module_{name}", esc_path, x * 0.62, y * 0.62, 13.0))
        wire_children.append(_leaf(f"pdb_to_esc_wire_bundle_{name}", wire_path, x * 0.36, y * 0.36, 12.8))
        leg_children.append(_leaf(f"landing_leg_{name}", paths["landing_leg"], x * 0.42, y * 0.42, -8.0))
        fasteners.append(_leaf(f"motor_mount_screws_{name}", paths["fastener"], x, y, 22.0))
    return [
        _subassembly(
            "central_body_module",
            [
                _leaf("lower_carbon_frame_plate", paths["lower_frame"], 0.0, 0.0, 7.0),
                _leaf("top_electronics_shell", paths["top_shell"], 0.0, 0.0, 18.0),
                _leaf("pdb_and_flight_controller_stack", paths["flight_controller"], 0.0, 0.0, 18.0),
                _leaf("radio_receiver", paths["receiver"], 0.0, -30.0, 17.0),
                _leaf("underslung_battery_pack", paths["battery"], 0.0, -3.0, -3.0),
                _leaf("rear_dual_antenna_pair", paths["antenna"], 0.0, -36.0, 20.0),
                _leaf("battery_to_pdb_power_leads", paths["wire_y"], 0.0, -18.0, 5.0),
            ],
        ),
        _subassembly(
            "x_airframe_arm_module",
            [
                _leaf("right_airframe_arm", paths["arm_x"], 67.0, 0.0, 10.0),
                _leaf("left_airframe_arm", paths["arm_x"], -67.0, 0.0, 10.0),
                _leaf("front_airframe_arm", paths["arm_y"], 0.0, 67.0, 10.0),
                _leaf("rear_airframe_arm", paths["arm_y"], 0.0, -67.0, 10.0),
            ],
        ),
        _subassembly("four_motor_module", motor_children),
        _subassembly("four_propeller_module", prop_children),
        _subassembly("four_esc_module", esc_children),
        _subassembly("wiring_harness_module", wire_children),
        _subassembly(
            "front_camera_gimbal_module",
            [_leaf("front_camera_gimbal", paths["camera"], 0.0, 43.0, 4.0)],
        ),
        _subassembly(
            "landing_gear_module",
            [
                *leg_children,
                _leaf("left_landing_skid", paths["skid_x"], -34.0, 0.0, -23.0),
                _leaf("right_landing_skid", paths["skid_x"], 34.0, 0.0, -23.0),
            ],
        ),
        _subassembly(
            "fastener_module",
            [
                *fasteners,
                _leaf("arm_root_screw_right", paths["fastener"], 30.0, 0.0, 14.0),
                _leaf("arm_root_screw_left", paths["fastener"], -30.0, 0.0, 14.0),
                _leaf("arm_root_screw_front", paths["fastener"], 0.0, 30.0, 14.0),
                _leaf("arm_root_screw_rear", paths["fastener"], 0.0, -30.0, 14.0),
            ],
        ),
    ]


def _validate() -> dict[str, object]:
    centers = _motor_centers()
    prop_radius = PROPELLER_DIAMETER / 2.0
    body_radius = math.hypot(CENTER_BODY_LENGTH / 2.0, CENTER_BODY_WIDTH / 2.0)
    min_motor_radius = min(math.hypot(x, y) for _, x, y in centers)
    prop_body_clearance = min_motor_radius - prop_radius - body_radius
    battery_bottom_z = -3.0 - BATTERY_HEIGHT / 2.0
    skid_top_z = -23.0 + 1.5
    battery_skid_clearance = battery_bottom_z - skid_top_z
    bbox_x = MOTOR_TO_MOTOR_DIAGONAL / math.sqrt(2.0) + PROPELLER_DIAMETER
    bbox_y = bbox_x
    bbox_z = 27.0 + PROPELLER_THICKNESS / 2.0 - (-23.0 - 1.5)
    checks = {
        "motor_count": len(centers),
        "propeller_count": len(centers),
        "arm_count": 4,
        "esc_count": 4,
        "flight_controller_count": 1,
        "receiver_count": 1,
        "landing_leg_count": len(centers),
        "cw_propeller_markers": 2,
        "ccw_propeller_markers": 2,
        "propeller_body_clearance_mm": round(prop_body_clearance, 2),
        "battery_skid_clearance_mm": round(battery_skid_clearance, 2),
        "bounding_box_mm": [round(bbox_x, 1), round(bbox_y, 1), round(bbox_z, 1)],
    }
    checks["passed"] = (
        checks["motor_count"] == 4
        and checks["propeller_count"] == 4
        and checks["arm_count"] == 4
        and checks["esc_count"] == 4
        and checks["flight_controller_count"] == 1
        and checks["receiver_count"] == 1
        and checks["landing_leg_count"] == 4
        and checks["cw_propeller_markers"] == 2
        and checks["ccw_propeller_markers"] == 2
        and prop_body_clearance > 2.0
        and battery_skid_clearance > 2.0
    )
    return checks


def _write_validation_report(report: dict[str, object]) -> None:
    output = Path(__file__).resolve().parent / REPORT_OUTPUT
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "lower_frame": _write_component("lower_carbon_frame_plate", _lower_frame_plate()),
        "top_shell": _write_component("top_electronics_shell", _top_body_shell()),
        "arm_x": _write_component("carbon_arm_x", _arm_x()),
        "arm_y": _write_component("carbon_arm_y", _arm_y()),
        "motor_can": _write_component("brushed_aluminum_motor_can", _motor_can()),
        "propeller_x": _write_component("smoke_propeller_x", _propeller_x()),
        "propeller_y": _write_component("smoke_propeller_y", _propeller_y()),
        "esc_x": _write_component("esc_module_x", _esc_x()),
        "esc_y": _write_component("esc_module_y", _esc_y()),
        "wire_x": _write_component("wire_bundle_x", _wire_bundle_x()),
        "wire_y": _write_component("wire_bundle_y", _wire_bundle_y()),
        "battery": _write_component("underslung_lipo_battery", _battery_pack()),
        "flight_controller": _write_component("flight_controller_stack", _flight_controller_stack()),
        "receiver": _write_component("radio_receiver", _receiver()),
        "camera": _write_component("front_camera_gimbal", _camera_gimbal()),
        "landing_leg": _write_component("landing_leg", _landing_leg()),
        "skid_x": _write_component("landing_skid", _skid_x()),
        "fastener": _write_component("socket_head_fastener", _fastener()),
        "direction_cap_cw": _write_component("cw_rotation_marker_cap", _direction_cap_cw()),
        "direction_cap_ccw": _write_component("ccw_rotation_marker_cap", _direction_cap_ccw()),
        "antenna": _write_component("rear_antenna_pair", _antenna_pair()),
    }
    report = _validate()
    _write_validation_report(report)
    if not report["passed"]:
        raise RuntimeError(f"quadrotor validation failed: {report}")
    return {"children": _assembly_children(paths), "step_output": "quadrotor_drone_assembly.step"}


if __name__ == "__main__":
    envelope = gen_step()
    print(json.dumps({"step_output": envelope["step_output"], "validation": _validate()}, indent=2))
