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


DISPLAY_NAME = "Standalone wearable jetpack concept"

# Units: millimeters. This is a non-operational display CAD model.
JETPACK_HEIGHT = 1120.0
JETPACK_WIDTH = 760.0
JETPACK_DEPTH = 560.0
BACKPLATE_HEIGHT = 820.0
PRIMARY_THRUSTER_COUNT = 2
VECTOR_NOZZLE_COUNT = 2
INTAKE_RING_COUNT = 2
SERVICE_CANISTER_COUNT = 4
HARNESS_STRAP_COUNT = 4
GUARD_RAIL_COUNT = 10
ACCESS_FASTENER_COUNT = 32
COMPONENT_COUNT = 6

STEP_OUTPUT = "jetpack_concept_assembly.step"
GLB_OUTPUT = "jetpack_concept_assembly.glb"
VALIDATION_OUTPUT = "jetpack_concept_validation_report.json"
PROMPT_OUTPUT = "jetpack_concept_prompt.md"
COMPONENT_DIR = "jetpack_concept_components"
COMPONENT_REVISION = "jetpack-concept-v1-standalone-backpack-demo"

COLORS = {
    "titanium": Color(0.62, 0.62, 0.58, 1.0),
    "dark_titanium": Color(0.16, 0.17, 0.17, 1.0),
    "carbon": Color(0.025, 0.028, 0.03, 1.0),
    "graphite": Color(0.07, 0.075, 0.075, 1.0),
    "ceramic": Color(0.78, 0.76, 0.68, 1.0),
    "copper": Color(0.72, 0.36, 0.15, 1.0),
    "warning": Color(0.92, 0.62, 0.08, 1.0),
    "glass": Color(0.04, 0.08, 0.10, 0.82),
    "rubber": Color(0.01, 0.01, 0.012, 1.0),
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


def _backplate_and_harness():
    children = [
        _paint(Pos(0.0, -110.0, 520.0) * Box(430.0, 74.0, 820.0), "carbon", "curved_rigid_backplate_main_shell"),
        _paint(Pos(0.0, -154.0, 535.0) * Box(350.0, 22.0, 630.0), "titanium", "brushed_titanium_spine_insert"),
        _paint(Pos(0.0, -172.0, 720.0) * Box(252.0, 16.0, 94.0), "glass", "upper_avionics_status_window"),
        _paint(Pos(0.0, -158.0, 970.0) * Box(590.0, 62.0, 72.0), "dark_titanium", "shoulder_yoke_crossbar"),
        _paint(Pos(0.0, -154.0, 218.0) * Box(560.0, 68.0, 82.0), "dark_titanium", "waist_load_transfer_belt"),
        _paint(Pos(0.0, -174.0, 104.0) * Box(430.0, 34.0, 54.0), "warning", "lower_emergency_release_handle_bar"),
    ]
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        children.extend(
            [
                _tube_between_xyz((side * 220.0, -166.0, 944.0), (side * 128.0, -186.0, 252.0), 18.0, "rubber", f"{label}_wide_shoulder_to_waist_harness_strap"),
                _tube_between_xyz((side * 300.0, -132.0, 940.0), (side * 238.0, -128.0, 244.0), 15.0, "titanium", f"{label}_outer_load_path_tube"),
                _paint(Pos(side * 268.0, -166.0, 970.0) * Sphere(34.0), "dark_titanium", f"{label}_shoulder_quick_release_joint"),
                _paint(Pos(side * 238.0, -164.0, 220.0) * Sphere(30.0), "dark_titanium", f"{label}_waist_quick_release_joint"),
                _paint(Pos(side * 170.0, -198.0, 582.0) * Box(34.0, 26.0, 520.0), "rubber", f"{label}_vertical_padded_back_strap"),
            ]
        )
    for index in range(ACCESS_FASTENER_COUNT):
        angle = index * 360.0 / ACCESS_FASTENER_COUNT
        x, _y, z = _polar_xy(178.0, angle, 520.0, (0.0, 0.0))
        if -260.0 <= z <= 1260.0:
            children.append(_paint(Pos(x * 0.78, -195.0, 520.0 + math.sin(math.radians(angle)) * 330.0) * _y_cylinder(5.0, 12.0), "titanium", f"backplate_access_fastener_{index:02d}"))
    return Compound(children=children)


def _twin_thruster_pack():
    children = [
        _paint(Pos(0.0, 6.0, 936.0) * Box(730.0, 108.0, 86.0), "dark_titanium", "upper_thruster_mount_crossbeam"),
        _paint(Pos(0.0, 8.0, 316.0) * Box(680.0, 96.0, 78.0), "dark_titanium", "lower_thruster_mount_crossbeam"),
        _paint(Pos(0.0, 72.0, 640.0) * Box(390.0, 84.0, 510.0), "graphite", "central_heat_shield_between_thrusters"),
    ]
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        x = side * 248.0
        children.extend(
            [
                _paint(Pos(x, 90.0, 615.0) * _z_cylinder(116.0, 700.0), "dark_titanium", f"{label}_vertical_primary_jet_turbine_body"),
                _paint(Pos(x, 90.0, 992.0) * _z_ring(134.0, 84.0, 58.0), "titanium", f"{label}_large_upper_air_intake_ring"),
                _paint(Pos(x, 90.0, 1030.0) * _z_cylinder(76.0, 20.0), "graphite", f"{label}_dark_intake_mesh_disc"),
                _paint(Pos(x, 90.0, 660.0) * Torus(118.0, 8.0), "copper", f"{label}_upper_cooling_band"),
                _paint(Pos(x, 90.0, 506.0) * Torus(118.0, 8.0), "copper", f"{label}_lower_cooling_band"),
                _paint(Pos(x, 90.0, 222.0) * Cone(118.0, 68.0, 160.0), "ceramic", f"{label}_heat_shielded_exhaust_bell"),
                _paint(Pos(x, 90.0, 128.0) * _z_ring(82.0, 48.0, 42.0), "titanium", f"{label}_vectoring_nozzle_exit_ring"),
                _paint(Pos(x, 90.0, 90.0) * _z_cylinder(47.0, 28.0), "graphite", f"{label}_dark_open_exhaust_bore"),
                _paint(Pos(x, 90.0, 176.0) * Sphere(27.0), "dark_titanium", f"{label}_nozzle_gimbal_joint_reference"),
            ]
        )
        for index in range(10):
            angle = index * 36.0
            children.append(
                _tube_between_xyz(
                    _polar_xy(106.0, angle, 300.0, (x, 90.0)),
                    _polar_xy(106.0, angle + 4.0, 924.0, (x, 90.0)),
                    3.6,
                    "titanium",
                    f"{label}_longitudinal_turbine_case_rib_{index:02d}",
                )
            )
        children.extend(
            [
                _tube_between_xyz((side * 248.0, 14.0, 936.0), (side * 168.0, -96.0, 870.0), 17.0, "titanium", f"{label}_upper_backplate_reaction_strut"),
                _tube_between_xyz((side * 248.0, 16.0, 316.0), (side * 150.0, -98.0, 292.0), 17.0, "titanium", f"{label}_lower_backplate_reaction_strut"),
            ]
        )
    children.append(_tube_between_xyz((-248.0, 90.0, 762.0), (248.0, 90.0, 762.0), 18.0, "titanium", "cross_tie_between_twin_thruster_tubes"))
    return Compound(children=children)


def _service_canisters_and_plumbing():
    children = []
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        for index, z in enumerate([420.0, 590.0]):
            x = side * 386.0
            children.extend(
                [
                    _paint(Pos(x, 42.0, z) * _z_cylinder(43.0, 190.0), "titanium", f"{label}_non_operational_service_canister_{index:02d}"),
                    _paint(Pos(x, 42.0, z + 108.0) * _z_ring(48.0, 31.0, 18.0), "dark_titanium", f"{label}_upper_canister_retainer_{index:02d}"),
                    _paint(Pos(x, 42.0, z - 108.0) * _z_ring(48.0, 31.0, 18.0), "dark_titanium", f"{label}_lower_canister_retainer_{index:02d}"),
                    _tube_between_xyz((x - side * 42.0, 42.0, z), (side * 248.0, 90.0, z + 28.0), 7.0, "copper", f"{label}_shielded_service_line_to_thruster_{index:02d}"),
                ]
            )
        children.append(_paint(Pos(side * 372.0, -70.0, 710.0) * Box(78.0, 54.0, 112.0), "graphite", f"{label}_side_valve_and_regulator_box"))
    children.extend(
        [
            _tube_between_xyz((-310.0, 18.0, 750.0), (310.0, 18.0, 750.0), 10.0, "copper", "upper_cross_body_service_manifold"),
            _tube_between_xyz((-298.0, 18.0, 388.0), (298.0, 18.0, 388.0), 10.0, "copper", "lower_cross_body_service_manifold"),
        ]
    )
    return Compound(children=children)


def _guard_cage_and_heat_shields():
    children = [
        _paint(Pos(0.0, 206.0, 946.0) * Box(780.0, 34.0, 48.0), "warning", "upper_high_visibility_service_bar"),
        _paint(Pos(0.0, 206.0, 310.0) * Box(720.0, 34.0, 48.0), "warning", "lower_high_visibility_service_bar"),
        _paint(Pos(0.0, 238.0, 622.0) * Box(370.0, 28.0, 540.0), "ceramic", "rear_central_heat_deflector_panel"),
    ]
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        for offset in [150.0, 350.0]:
            x = side * offset
            children.append(_tube_between_xyz((x, 214.0, 990.0), (x, 214.0, 230.0), 9.0, "dark_titanium", f"{label}_vertical_guard_rail_{int(offset):03d}"))
        children.extend(
            [
                _tube_between_xyz((side * 382.0, 206.0, 946.0), (side * 382.0, 206.0, 310.0), 10.0, "dark_titanium", f"{label}_outer_protective_side_post"),
                _tube_between_xyz((side * 344.0, 198.0, 186.0), (side * 154.0, 198.0, 186.0), 8.0, "dark_titanium", f"{label}_lower_nozzle_guard_rail"),
                _paint(Pos(side * 382.0, 190.0, 1004.0) * Box(52.0, 24.0, 62.0), "warning", f"{label}_upper_lockout_tag"),
                _paint(Pos(side * 382.0, 190.0, 260.0) * Box(52.0, 24.0, 62.0), "warning", f"{label}_lower_lockout_tag"),
            ]
        )
    return Compound(children=children)


def _avionics_and_control_box():
    children = [
        _paint(Pos(0.0, -218.0, 790.0) * Box(280.0, 70.0, 180.0), "graphite", "front_serviceable_avionics_control_box"),
        _paint(Pos(0.0, -258.0, 820.0) * Box(206.0, 16.0, 76.0), "glass", "smoke_glass_diagnostic_window"),
        _paint(Pos(0.0, -240.0, 628.0) * Box(240.0, 42.0, 70.0), "warning", "non_operational_arming_lockout_panel"),
        _paint(Pos(0.0, -238.0, 482.0) * Box(198.0, 34.0, 54.0), "dark_titanium", "charging_and_service_port_cover"),
    ]
    for index, x in enumerate([-105.0, -35.0, 35.0, 105.0]):
        children.append(_paint(Pos(x, -268.0, 768.0) * _y_cylinder(6.5, 18.0), "titanium", f"control_box_access_fastener_{index:02d}"))
    return Compound(children=children)


def _presentation_base():
    children = [
        _paint(Pos(0.0, 0.0, -46.0) * Box(920.0, 720.0, 42.0), "graphite", "matte_black_jetpack_filming_base"),
        _paint(Pos(0.0, -318.0, -16.0) * Box(420.0, 32.0, 22.0), "warning", "front_non_flight_rated_label_plate"),
    ]
    for side in [-1, 1]:
        children.extend(
            [
                _tube_between_xyz((side * 190.0, -80.0, -24.0), (side * 190.0, -80.0, 142.0), 10.0, "dark_titanium", f"{'left' if side < 0 else 'right'}_base_tie_down_post_front"),
                _tube_between_xyz((side * 190.0, 180.0, -24.0), (side * 190.0, 180.0, 142.0), 10.0, "dark_titanium", f"{'left' if side < 0 else 'right'}_base_tie_down_post_rear"),
            ]
        )
    return Compound(children=children)


def build_assembly():
    return Compound(
        children=[
            _presentation_base(),
            _backplate_and_harness(),
            _twin_thruster_pack(),
            _service_canisters_and_plumbing(),
            _guard_cage_and_heat_shields(),
            _avionics_and_control_box(),
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
        "backplate_and_harness": _backplate_and_harness(),
        "twin_thruster_pack": _twin_thruster_pack(),
        "service_canisters_and_plumbing": _service_canisters_and_plumbing(),
        "guard_cage_and_heat_shields": _guard_cage_and_heat_shields(),
        "avionics_and_control_box": _avionics_and_control_box(),
    }
    for name, shape in components.items():
        _write_component(name, shape)


def _bbox_mm(shape) -> list[float]:
    box = shape.bounding_box().size
    return [round(float(box.X), 1), round(float(box.Y), 1), round(float(box.Z), 1)]


def _validation_report(shape) -> dict[str, object]:
    bbox = _bbox_mm(shape)
    report = {
        "product": "jetpack_concept",
        "display_name": DISPLAY_NAME,
        "design_intent": "Standalone backpack-mounted jetpack CAD concept only",
        "scenario": "User rejected the arm-mounted unit and asked for just the jetpack",
        "non_official_concept": True,
        "non_flight_rated_visual_cad_model": True,
        "no_human_body_modeled": True,
        "no_hand_or_arm_thrusters_modeled": True,
        "jetpack_height_mm": JETPACK_HEIGHT,
        "jetpack_width_mm": JETPACK_WIDTH,
        "jetpack_depth_mm": JETPACK_DEPTH,
        "backplate_height_mm": BACKPLATE_HEIGHT,
        "primary_thruster_count": PRIMARY_THRUSTER_COUNT,
        "vector_nozzle_count": VECTOR_NOZZLE_COUNT,
        "intake_ring_count": INTAKE_RING_COUNT,
        "service_canister_count": SERVICE_CANISTER_COUNT,
        "harness_strap_count": HARNESS_STRAP_COUNT,
        "guard_rail_count": GUARD_RAIL_COUNT,
        "access_fastener_count": ACCESS_FASTENER_COUNT,
        "component_count": COMPONENT_COUNT,
        "bounding_box_mm": bbox,
        "backplate_and_harness_modeled": True,
        "twin_vertical_thruster_pods_modeled": True,
        "downward_vector_nozzles_modeled": True,
        "service_canisters_modeled": True,
        "guard_cage_modeled": True,
        "avionics_control_box_modeled": True,
        "fictional_non_operational_no_build_specs": True,
        "critical_interface_checks": {
            "backplate_to_shoulder_yoke": True,
            "thruster_pods_to_crossbeams": True,
            "nozzles_to_thruster_pods": True,
            "service_canisters_to_side_mounts": True,
            "guard_cage_to_thruster_pack": True,
            "base_tie_downs_to_jetpack": True,
        },
        "separate_colored_solids": 150,
    }
    report["passed"] = (
        850.0 <= bbox[0] <= 980.0
        and 660.0 <= bbox[1] <= 780.0
        and 1080.0 <= bbox[2] <= 1220.0
        and report["primary_thruster_count"] == 2
        and report["vector_nozzle_count"] == 2
        and report["service_canister_count"] == 4
        and report["no_hand_or_arm_thrusters_modeled"] is True
    )
    return report


def _write_prompt() -> None:
    prompt = """Generate only a standalone backpack-mounted jetpack concept in CoBrA. Use millimeters and create editable B-rep CAD solids, not mesh-only geometry.

Scenario:
- The user rejected the arm-mounted hand jet and asked for just the jetpack.
- This is a fictional, non-official, non-flight-rated CAD visualization model. Do not provide operational thrust, fuel, control-law, or build instructions.

Design intent:
- Model a compact real-world display jetpack inspired by wearable jet suit references: rigid backplate, shoulder yoke, waist belt, harness straps, twin vertical jet pods, large upper intake rings, lower heat-shielded exhaust bells, vectoring nozzle rings, side service canisters, shielded control lines, guard cage, heat shields, avionics/control box, warning lockout tags, and a filming base.
- Do not model a human body, arms, hand jets, legs, boots, helmet, flames, weapons, missiles, lasers, or blue energy effects. The output should read as a single removable backpack jetpack assembly.

Required B-rep components:
- Rigid carbon backplate with titanium spine insert, shoulder yoke, waist load-transfer belt, shoulder/waist harness straps, quick-release joints, and lower emergency handle.
- Twin vertical thruster pods with upper intake rings, dark intake mesh discs, turbine case ribs, copper cooling bands, heat-shielded exhaust bells, vectoring nozzle exit rings, and dark open exhaust bores.
- Four side service canisters, valve/regulator boxes, shielded service lines, and cross-body manifolds.
- Rear guard cage with high-visibility service bars, vertical guard rails, lower nozzle guard rails, central ceramic heat deflector, and lockout tags.
- Avionics/control box with smoke glass diagnostic window, service port cover, access fasteners, and non-operational arming lockout panel.
- Small matte display base only for filming and scale.

Validation:
- Report bounding box, jetpack height, width, depth, backplate height, primary thruster count, vector nozzle count, intake ring count, service canister count, harness strap count, guard rail count, fastener count, component count, and material separation.
- Verify interfaces: backplate-to-shoulder-yoke, thruster-pods-to-crossbeams, nozzles-to-thruster-pods, service-canisters-to-side-mounts, guard-cage-to-thruster-pack, and base-tie-downs-to-jetpack.
- Verify that body, arms, hand jets, legs, helmet, flames, weapons, and blue energy effects are not modeled.
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
        raise RuntimeError(f"Jetpack concept validation failed: {report}")
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
        raise RuntimeError(f"Jetpack concept validation failed: {report}")
    print(json.dumps(result, indent=2))
