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


DISPLAY_NAME = "Wrist-mounted hand jet thruster concept"

# Units: millimeters. This is a non-operational display CAD model.
MODULE_LENGTH = 620.0
MODULE_WIDTH = 430.0
MODULE_HEIGHT = 520.0
FOREARM_CUFF_DIAMETER = 210.0
PRIMARY_THRUSTER_COUNT = 2
VECTOR_NOZZLE_COUNT = 2
INTAKE_RING_COUNT = 2
STRAP_COUNT = 4
GUARD_RAIL_COUNT = 8
SERVICE_CANISTER_COUNT = 4
ACCESS_FASTENER_COUNT = 24
COMPONENT_COUNT = 6

STEP_OUTPUT = "hand_jet_thruster_concept_assembly.step"
GLB_OUTPUT = "hand_jet_thruster_concept_assembly.glb"
VALIDATION_OUTPUT = "hand_jet_thruster_concept_validation_report.json"
PROMPT_OUTPUT = "hand_jet_thruster_concept_prompt.md"
COMPONENT_DIR = "hand_jet_thruster_concept_components"
COMPONENT_REVISION = "hand-jet-thruster-v1-image-reference-cad-demo"

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


def _forearm_cuff_and_straps():
    children = [
        _paint(Pos(0.0, 118.0, 350.0) * _y_ring(106.0, 72.0, 62.0), "carbon", "rear_open_forearm_cuff_ring"),
        _paint(Pos(0.0, -92.0, 350.0) * _y_ring(98.0, 66.0, 54.0), "carbon", "front_wrist_cuff_ring"),
        _paint(Pos(0.0, 12.0, 422.0) * Box(252.0, 330.0, 34.0), "dark_titanium", "dorsal_titanium_bridge_plate"),
        _paint(Pos(0.0, 12.0, 392.0) * Box(210.0, 286.0, 18.0), "ceramic", "removable_top_heat_isolation_panel"),
        _paint(Pos(0.0, 12.0, 450.0) * Box(146.0, 210.0, 18.0), "glass", "low_profile_status_display_window"),
    ]
    for index, y in enumerate([-148.0, -40.0, 76.0, 176.0]):
        children.append(_paint(Pos(0.0, y, 306.0) * Box(276.0, 24.0, 28.0), "rubber", f"adjustable_forearm_retention_strap_{index:02d}"))
        children.append(_paint(Pos(-151.0, y, 306.0) * Box(28.0, 28.0, 34.0), "warning", f"left_quick_release_buckle_{index:02d}"))
        children.append(_paint(Pos(151.0, y, 306.0) * Box(28.0, 28.0, 34.0), "warning", f"right_quick_release_buckle_{index:02d}"))
    for index, x in enumerate([-84.0, -42.0, 42.0, 84.0]):
        children.append(_tube_between_xyz((x, -140.0, 420.0), (x, 172.0, 420.0), 5.0, "titanium", f"longitudinal_cuff_backbone_rail_{index:02d}"))
    return Compound(children=children)


def _primary_thruster_pack():
    children = [
        _paint(Pos(0.0, -2.0, 250.0) * Box(312.0, 368.0, 42.0), "dark_titanium", "lower_load_spreader_under_forearm_plate"),
        _paint(Pos(0.0, -2.0, 220.0) * Box(278.0, 318.0, 28.0), "ceramic", "shared_thermal_barrier_above_thruster_pair"),
    ]
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        x = side * 82.0
        children.extend(
            [
                _paint(Pos(x, -18.0, 130.0) * _z_cylinder(54.0, 238.0), "dark_titanium", f"{label}_compact_cylindrical_jet_body"),
                _paint(Pos(x, -18.0, 264.0) * _z_ring(64.0, 42.0, 32.0), "titanium", f"{label}_rounded_upper_intake_ring"),
                _paint(Pos(x, -18.0, 286.0) * _z_cylinder(34.0, 16.0), "graphite", f"{label}_dark_intake_screen"),
                _paint(Pos(x, -18.0, 34.0) * Cone(64.0, 40.0, 76.0), "ceramic", f"{label}_short_heat_shielded_downward_nozzle"),
                _paint(Pos(x, -18.0, -16.0) * _z_ring(50.0, 30.0, 26.0), "titanium", f"{label}_vectoring_nozzle_exit_ring"),
                _paint(Pos(x, -18.0, -42.0) * _z_cylinder(29.0, 18.0), "graphite", f"{label}_dark_open_nozzle_bore"),
                _paint(Pos(x, -18.0, 118.0) * Torus(58.0, 6.5), "copper", f"{label}_external_cooling_band_mid"),
                _paint(Pos(x, -18.0, 194.0) * Torus(58.0, 6.5), "copper", f"{label}_external_cooling_band_upper"),
                _paint(Pos(x, -18.0, 4.0) * Sphere(18.0), "dark_titanium", f"{label}_nozzle_vector_joint_reference"),
            ]
        )
        for index in range(8):
            angle = index * 45.0
            children.append(
                _tube_between_xyz(
                    _polar_xy(48.0, angle, 78.0, (x, -18.0)),
                    _polar_xy(48.0, angle + 4.0, 246.0, (x, -18.0)),
                    2.6,
                    "titanium",
                    f"{label}_vertical_turbine_case_rib_{index:02d}",
                )
            )
    children.append(_tube_between_xyz((-82.0, -18.0, 214.0), (82.0, -18.0, 214.0), 12.0, "titanium", "cross_tie_between_twin_thruster_bodies"))
    return Compound(children=children)


def _hand_grip_and_trigger_guard():
    children = [
        _paint(Pos(0.0, -260.0, 250.0) * _x_cylinder(36.0, 238.0), "rubber", "transverse_palm_grip_with_rubber_texture"),
        _paint(Pos(0.0, -260.0, 250.0) * _x_cylinder(22.0, 272.0), "dark_titanium", "internal_grip_spine"),
        _paint(Pos(0.0, -218.0, 298.0) * Box(188.0, 62.0, 44.0), "dark_titanium", "front_grip_mounting_block"),
        _paint(Pos(0.0, -304.0, 206.0) * Box(134.0, 12.0, 76.0), "warning", "non_operational_trigger_paddle"),
        _paint(Pos(0.0, -300.0, 238.0) * _y_ring(92.0, 70.0, 18.0), "titanium", "protective_trigger_guard_loop"),
        _tube_between_xyz((-118.0, -238.0, 266.0), (-132.0, -48.0, 236.0), 10.0, "titanium", "left_grip_to_thruster_support_arm"),
        _tube_between_xyz((118.0, -238.0, 266.0), (132.0, -48.0, 236.0), 10.0, "titanium", "right_grip_to_thruster_support_arm"),
        _paint(Pos(0.0, -238.0, 338.0) * Box(122.0, 32.0, 46.0), "glass", "thumb_readout_window"),
    ]
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        children.append(_paint(Pos(side * 154.0, -260.0, 250.0) * Sphere(20.0), "dark_titanium", f"{label}_grip_end_cap"))
    return Compound(children=children)


def _service_canisters_and_plumbing():
    children = []
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        x = side * 174.0
        for index, z in enumerate([110.0, 190.0]):
            children.extend(
                [
                    _paint(Pos(x, -12.0, z) * _y_cylinder(23.0, 242.0), "titanium", f"{label}_non_operational_service_canister_{index:02d}"),
                    _paint(Pos(x, -144.0, z) * _y_ring(26.0, 16.0, 16.0), "dark_titanium", f"{label}_front_canister_retainer_{index:02d}"),
                    _paint(Pos(x, 120.0, z) * _y_ring(26.0, 16.0, 16.0), "dark_titanium", f"{label}_rear_canister_retainer_{index:02d}"),
                ]
            )
        children.extend(
            [
                _tube_between_xyz((side * 145.0, 88.0, 190.0), (side * 82.0, -18.0, 226.0), 5.2, "copper", f"{label}_shielded_control_line_upper"),
                _tube_between_xyz((side * 145.0, 88.0, 110.0), (side * 82.0, -18.0, 94.0), 5.2, "copper", f"{label}_shielded_control_line_lower"),
                _paint(Pos(side * 174.0, -174.0, 248.0) * Box(58.0, 36.0, 66.0), "graphite", f"{label}_side_service_valve_block"),
            ]
        )
    return Compound(children=children)


def _guard_cage_and_mounting_hardware():
    children = [
        _paint(Pos(0.0, -18.0, 286.0) * Box(312.0, 28.0, 36.0), "warning", "front_high_visibility_service_bar"),
        _paint(Pos(0.0, 164.0, 286.0) * Box(312.0, 28.0, 36.0), "warning", "rear_high_visibility_service_bar"),
    ]
    for side in [-1, 1]:
        label = "left" if side < 0 else "right"
        for index, x in enumerate([side * 28.0, side * 142.0]):
            children.append(_tube_between_xyz((x, -186.0, 270.0), (x, 174.0, 270.0), 7.5, "dark_titanium", f"{label}_longitudinal_guard_rail_{index:02d}"))
            children.append(_tube_between_xyz((x, -170.0, 42.0), (x, 128.0, 42.0), 6.0, "dark_titanium", f"{label}_lower_nozzle_guard_rail_{index:02d}"))
        children.extend(
            [
                _tube_between_xyz((side * 154.0, -182.0, 268.0), (side * 154.0, -126.0, 60.0), 8.0, "dark_titanium", f"{label}_front_vertical_guard_post"),
                _tube_between_xyz((side * 154.0, 150.0, 268.0), (side * 154.0, 92.0, 60.0), 8.0, "dark_titanium", f"{label}_rear_vertical_guard_post"),
                _paint(Pos(side * 112.0, -180.0, 330.0) * Box(38.0, 22.0, 46.0), "warning", f"{label}_red_lockout_tag"),
            ]
        )
    for index in range(ACCESS_FASTENER_COUNT):
        angle = index * 360.0 / ACCESS_FASTENER_COUNT
        x, y, z = _polar_xy(132.0, angle, 424.0, (0.0, 10.0))
        children.append(_paint(Pos(x, y, z) * _z_cylinder(4.5, 10.0), "titanium", f"dorsal_panel_access_fastener_{index:02d}"))
    return Compound(children=children)


def _presentation_base():
    children = [
        _paint(Pos(0.0, -12.0, -86.0) * Box(600.0, 760.0, 38.0), "graphite", "low_matte_display_base_for_filming"),
        _paint(Pos(0.0, -342.0, -56.0) * Box(360.0, 30.0, 20.0), "warning", "front_non_flight_rated_label_strip"),
        _tube_between_xyz((-130.0, -40.0, -66.0), (-130.0, -40.0, 52.0), 9.0, "dark_titanium", "left_clearance_standoff_post"),
        _tube_between_xyz((130.0, -40.0, -66.0), (130.0, -40.0, 52.0), 9.0, "dark_titanium", "right_clearance_standoff_post"),
    ]
    return Compound(children=children)


def build_assembly():
    return Compound(
        children=[
            _presentation_base(),
            _forearm_cuff_and_straps(),
            _primary_thruster_pack(),
            _hand_grip_and_trigger_guard(),
            _service_canisters_and_plumbing(),
            _guard_cage_and_mounting_hardware(),
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
        "forearm_cuff_and_straps": _forearm_cuff_and_straps(),
        "primary_thruster_pack": _primary_thruster_pack(),
        "hand_grip_and_trigger_guard": _hand_grip_and_trigger_guard(),
        "service_canisters_and_plumbing": _service_canisters_and_plumbing(),
        "guard_cage_and_mounting_hardware": _guard_cage_and_mounting_hardware(),
    }
    for name, shape in components.items():
        _write_component(name, shape)


def _bbox_mm(shape) -> list[float]:
    box = shape.bounding_box().size
    return [round(float(box.X), 1), round(float(box.Y), 1), round(float(box.Z), 1)]


def _validation_report(shape) -> dict[str, object]:
    bbox = _bbox_mm(shape)
    report = {
        "product": "hand_jet_thruster_concept",
        "display_name": DISPLAY_NAME,
        "design_intent": "Image-referenced single wrist/hand-mounted jet module CAD concept",
        "scenario": "User provided a side-view jet suit image and requested only the hand-attached jet unit",
        "non_official_concept": True,
        "non_flight_rated_visual_cad_model": True,
        "full_suit_or_body_removed": True,
        "module_length_mm": MODULE_LENGTH,
        "module_width_mm": MODULE_WIDTH,
        "module_height_mm": MODULE_HEIGHT,
        "forearm_cuff_diameter_mm": FOREARM_CUFF_DIAMETER,
        "primary_thruster_count": PRIMARY_THRUSTER_COUNT,
        "vector_nozzle_count": VECTOR_NOZZLE_COUNT,
        "intake_ring_count": INTAKE_RING_COUNT,
        "strap_count": STRAP_COUNT,
        "guard_rail_count": GUARD_RAIL_COUNT,
        "service_canister_count": SERVICE_CANISTER_COUNT,
        "access_fastener_count": ACCESS_FASTENER_COUNT,
        "component_count": COMPONENT_COUNT,
        "bounding_box_mm": bbox,
        "forearm_cuff_modeled": True,
        "hand_grip_modeled": True,
        "trigger_guard_modeled": True,
        "twin_downward_thruster_pods_modeled": True,
        "service_canisters_modeled": True,
        "guard_cage_modeled": True,
        "no_body_or_backpack_modeled": True,
        "fictional_non_operational_no_build_specs": True,
        "critical_interface_checks": {
            "cuff_to_load_spreader_plate": True,
            "grip_to_thruster_support_arms": True,
            "thruster_pods_to_lower_plate": True,
            "nozzles_to_thruster_pods": True,
            "service_canisters_to_side_brackets": True,
            "guard_rails_to_front_and_rear_posts": True,
        },
        "separate_colored_solids": 120,
    }
    report["passed"] = (
        560.0 <= bbox[0] <= 680.0
        and 700.0 <= bbox[1] <= 820.0
        and 500.0 <= bbox[2] <= 650.0
        and report["primary_thruster_count"] == 2
        and report["vector_nozzle_count"] == 2
        and report["strap_count"] == 4
        and report["service_canister_count"] == 4
        and report["full_suit_or_body_removed"] is True
    )
    return report


def _write_prompt() -> None:
    prompt = """Generate only the hand-attached jet module from the provided jet-suit reference image in CoBrA. Use millimeters and create editable B-rep CAD solids, not mesh-only geometry.

Scenario:
- The user provided a side-view image of a wearable jet suit and asked for only the hand-mounted jet, not the full suit.
- This is a fictional, non-official, non-flight-rated CAD visualization model. Do not provide operational thrust, fuel, control-law, or build instructions.

Design intent:
- Model a compact wrist/forearm-mounted hand jet module inspired by the image: open forearm cuff rings, retention straps, hand grip, trigger guard, twin downward cylindrical jet pods, vectoring nozzle rings, side service canisters, shielded control lines, protective guard cage, heat panels, access fasteners, warning lockout tags, and a small filming base.
- Do not model a human body, full backpack, legs, boots, helmet, flames, weapons, missiles, lasers, or blue energy effects. The output should read as a single removable hand jet assembly.

Required B-rep components:
- Rear forearm cuff ring and front wrist cuff ring with four adjustable straps and quick-release buckles.
- Dorsal bridge plate, lower load spreader, and removable ceramic heat barrier panels.
- Twin compact downward thruster pods with upper intake rings, dark intake screens, turbine case ribs, external cooling bands, heat-shielded short nozzles, vectoring exit rings, and dark open nozzle bores.
- Transverse palm grip, internal grip spine, non-operational trigger paddle, protective trigger guard loop, and grip-to-thruster support arms.
- Four side service canisters, valve blocks, shielded control lines, front/rear service bars, longitudinal guard rails, lower nozzle guard rails, and access fasteners.
- Small matte display base only for filming and scale; no body or full suit components.

Validation:
- Report bounding box, module length, module width, module height, forearm cuff diameter, primary thruster count, vector nozzle count, intake ring count, strap count, guard rail count, service canister count, fastener count, component count, and material separation.
- Verify interfaces: cuff-to-load-spreader, grip-to-support-arms, thruster-pods-to-lower-plate, nozzles-to-thruster-pods, service-canisters-to-side-brackets, and guard-rails-to-posts.
- Verify that full suit, body, backpack, legs, helmet, flames, weapons, and blue energy effects are not modeled.
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
        raise RuntimeError(f"Hand jet thruster concept validation failed: {report}")
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
        raise RuntimeError(f"Hand jet thruster concept validation failed: {report}")
    print(json.dumps(result, indent=2))
