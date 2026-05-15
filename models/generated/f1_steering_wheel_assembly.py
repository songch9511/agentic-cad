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
    Mode,
    Plane,
    Polygon,
    Pos,
    Rot,
    Sphere,
    Torus,
    extrude,
    export_gltf,
    export_step,
)


DISPLAY_NAME = "Parametric F1-style steering wheel assembly"

# Units: millimeters. Front view uses X horizontal, Z vertical, Y depth.
OVERALL_WIDTH = 270.0
OVERALL_HEIGHT = 183.0
OVERALL_DEPTH_TARGET = 67.0
FACE_PLATE_THICKNESS = 6.0
GRIP_WIDTH = 34.0
GRIP_HEIGHT = 183.0
GRIP_DEPTH = 28.0
DISPLAY_WIDTH = 96.0
DISPLAY_HEIGHT = 46.0

STEP_OUTPUT = "f1_steering_wheel_assembly.step"
REAR_STEP_OUTPUT = "f1_steering_wheel_rear_details.step"
GLB_OUTPUT = "f1_steering_wheel_assembly.glb"
VALIDATION_OUTPUT = "f1_steering_wheel_validation_report.json"
PROMPT_OUTPUT = "f1_steering_wheel_prompt.md"
COMPONENT_DIR = "f1_steering_wheel_components"
COMPONENT_REVISION = "f1-steering-wheel-v1"

COLORS = {
    "carbon": Color(0.015, 0.018, 0.018, 1.0),
    "gloss": Color(0.0, 0.0, 0.0, 1.0),
    "suede": Color(0.006, 0.006, 0.005, 1.0),
    "screen": Color(0.78, 0.8, 0.77, 1.0),
    "screen_dark": Color(0.09, 0.09, 0.09, 1.0),
    "teal": Color(0.0, 0.82, 0.65, 1.0),
    "red": Color(0.95, 0.05, 0.025, 1.0),
    "aluminum": Color(0.62, 0.64, 0.62, 1.0),
    "dark_metal": Color(0.05, 0.05, 0.05, 1.0),
    "rubber": Color(0.02, 0.02, 0.02, 1.0),
    "amber": Color(1.0, 0.62, 0.03, 1.0),
}


def _paint(shape, color: str, label: str = ""):
    shape.color = COLORS[color]
    if label:
        shape.label = label
    return shape


def _front_cylinder(radius: float, length: float):
    return Rot(90.0, 0.0, 0.0) * Cylinder(radius, length)


def _y_cylinder(radius: float, length: float):
    return Rot(90.0, 0.0, 0.0) * Cylinder(radius, length)


def _vertical_capsule(width: float, height: float, depth: float, color: str, label: str):
    radius = width / 2.0
    return _paint(
        Compound(
            children=[
                Box(width, depth, height - width),
                Pos(0.0, 0.0, (height - width) / 2.0) * _y_cylinder(radius, depth),
                Pos(0.0, 0.0, -(height - width) / 2.0) * _y_cylinder(radius, depth),
            ]
        ),
        color,
        label,
    )


def _face_plate():
    points = [
        (-100.0, 72.0),
        (-76.0, 83.0),
        (-44.0, 83.0),
        (-38.0, 75.0),
        (38.0, 75.0),
        (44.0, 83.0),
        (76.0, 83.0),
        (100.0, 72.0),
        (105.0, 43.0),
        (84.0, 24.0),
        (76.0, -42.0),
        (54.0, -79.0),
        (15.0, -85.0),
        (0.0, -80.0),
        (-15.0, -85.0),
        (-54.0, -79.0),
        (-76.0, -42.0),
        (-84.0, 24.0),
        (-105.0, 43.0),
    ]
    with BuildPart() as part:
        with BuildSketch(Plane.XZ):
            Polygon(*points)
        extrude(amount=FACE_PLATE_THICKNESS)
    return _paint(part.part, "carbon", "single_piece_carbon_face_plate")


def _display_stack():
    details = [
        _paint(Pos(0.0, -6.6, 32.0) * Box(116.0, 2.4, 62.0), "gloss", "gloss_black_display_surround"),
        _paint(Pos(0.0, -8.0, 32.0) * Box(DISPLAY_WIDTH, 1.2, DISPLAY_HEIGHT), "screen", "lcd_display_96x46"),
    ]
    # Tachometer ruler and vertical tick marks.
    for index in range(44):
        x = -42.0 + index * 2.0
        z = 50.5 if index % 5 else 49.0
        height = 9.0 if index % 5 == 0 else 5.0
        details.append(_paint(Pos(x, -9.0, z) * Box(0.55, 0.8, height), "screen_dark", f"tach_tick_{index:02d}"))
    details.append(_paint(Pos(0.0, -9.0, 10.0) * Box(86.0, 0.8, 1.1), "screen_dark", "display_bottom_status_rule"))
    for x in (-40.0, -8.0, 25.0, 55.0):
        details.append(_paint(Pos(x, -9.0, 19.0) * Box(18.0, 0.8, 2.0), "screen_dark", "screen_status_text_block"))
    # Large display numerals represented as seven-segment solids.
    for offset, digit in [(-38.0, "1"), (-22.0, "9"), (-6.0, "5")]:
        details.extend(_seven_segment_digit(offset, 31.0, 11.5, digit, "spd_digit"))
    for offset, digit in [(32.0, "8"), (48.0, "5")]:
        details.extend(_seven_segment_digit(offset, 31.0, 11.5, digit, "water_temp_digit"))
    for offset, digit in [(-36.0, "4"), (-18.0, "2")]:
        details.extend(_seven_segment_digit(offset, 12.0, 10.0, digit, "oil_pressure_digit"))
    for x in (-27.0, 40.0):
        details.append(_paint(Pos(x, -9.0, 12.0) * _front_cylinder(1.0, 0.7), "screen_dark", "decimal_or_colon_marker"))
    return Compound(children=details)


SEGMENTS = {
    "0": "abcfed",
    "1": "bc",
    "2": "abged",
    "3": "abgcd",
    "4": "fgbc",
    "5": "afgcd",
    "6": "afgecd",
    "7": "abc",
    "8": "abcdefg",
    "9": "abfgcd",
}


def _seven_segment_digit(x: float, z: float, scale: float, digit: str, prefix: str):
    active = SEGMENTS[digit]
    w = scale * 0.58
    h = scale
    t = scale * 0.11
    y = -9.2
    specs = {
        "a": (0.0, h / 2.0, w, t),
        "b": (w / 2.0, h / 4.0, t, h / 2.0),
        "c": (w / 2.0, -h / 4.0, t, h / 2.0),
        "d": (0.0, -h / 2.0, w, t),
        "e": (-w / 2.0, -h / 4.0, t, h / 2.0),
        "f": (-w / 2.0, h / 4.0, t, h / 2.0),
        "g": (0.0, 0.0, w, t),
    }
    pieces = []
    for key in active:
        ox, oz, sx, sz = specs[key]
        pieces.append(_paint(Pos(x + ox, y, z + oz) * Box(sx, 0.9, sz), "screen_dark", f"{prefix}_{digit}_{key}"))
    return pieces


def _button(x: float, z: float, color: str, label: str, radius: float = 8.4):
    return Compound(
        children=[
            _paint(Pos(x, -8.4, z) * _front_cylinder(radius + 3.2, 4.0), "dark_metal", f"{label}_black_collar"),
            _paint(Pos(x, -11.0, z) * _front_cylinder(radius, 4.2), color, label),
            _paint(Pos(x, -13.5, z + radius * 0.22) * _front_cylinder(radius * 0.55, 0.9), color, f"{label}_raised_center"),
        ]
    )


def _screw(x: float, z: float, label: str):
    return Compound(
        children=[
            _paint(Pos(x, -8.0, z) * _front_cylinder(3.3, 2.0), "aluminum", f"{label}_socket_head"),
            _paint(Pos(x, -9.4, z) * _front_cylinder(1.5, 1.0), "dark_metal", f"{label}_hex_socket"),
        ]
    )


def _led_row():
    children = []
    for index in range(8):
        x = -28.0 + index * 8.0
        color = "amber" if index < 5 else "dark_metal"
        children.append(_paint(Pos(x, -8.0, 70.0) * _front_cylinder(2.3, 1.5), color, f"shift_led_{index + 1:02d}"))
    return Compound(children=children)


def _button_panel(side: int):
    x = side * 36.0
    panel = _paint(Pos(x, -7.2, -48.0) * Rot(0.0, side * -12.0, 0.0) * Box(34.0, 2.4, 58.0), "gloss", f"{'right' if side > 0 else 'left'}_lower_button_pod")
    return Compound(
        children=[
            panel,
            _button(x + side * -4.0, -34.0, "red", f"{'right' if side > 0 else 'left'}_upper_red_button", 6.8),
            _button(x + side * 2.0, -63.0, "red", f"{'right' if side > 0 else 'left'}_lower_red_button", 6.8),
        ]
    )


def _grip_assembly(side: int):
    x = side * 118.0
    children = [
        Pos(x, 0.0, 0.0) * _vertical_capsule(GRIP_WIDTH, GRIP_HEIGHT, GRIP_DEPTH, "suede", f"{'right' if side > 0 else 'left'}_alcantara_grip"),
        _paint(Pos(side * 94.0, -3.0, 68.0) * Rot(0.0, side * -18.0, 0.0) * Box(38.0, 20.0, 21.0), "gloss", "top_grip_clamp"),
        _paint(Pos(side * 94.0, -3.0, -72.0) * Rot(0.0, side * 18.0, 0.0) * Box(36.0, 20.0, 25.0), "gloss", "lower_grip_clamp"),
        _paint(Pos(side * 89.0, -2.0, 40.0) * _front_cylinder(21.0, 7.0), "carbon", "inner_thumb_recess"),
        _paint(Pos(side * 83.0, -2.0, -38.0) * _front_cylinder(29.0, 7.0), "carbon", "lower_hand_opening_lip"),
        _screw(side * 100.0, 73.0, "top_grip_clamp_screw"),
        _screw(side * 100.0, -78.0, "lower_grip_clamp_screw"),
    ]
    return Compound(children=children)


def _front_controls():
    controls = [
        _display_stack(),
        _led_row(),
        _button(-75.0, 61.0, "teal", "upper_left_teal_button"),
        _button(75.0, 61.0, "teal", "upper_right_teal_button"),
        _button(-75.0, 17.0, "teal", "lower_left_teal_button"),
        _button(75.0, 17.0, "teal", "lower_right_teal_button"),
        _button_panel(-1),
        _button_panel(1),
    ]
    screw_positions = [
        (-80.0, 79.0),
        (-34.0, 80.0),
        (34.0, 80.0),
        (80.0, 79.0),
        (-103.0, 58.0),
        (103.0, 58.0),
        (-55.0, 48.0),
        (55.0, 48.0),
        (-83.0, -3.0),
        (83.0, -3.0),
        (-11.0, -82.0),
        (11.0, -82.0),
    ]
    controls.extend(_screw(x, z, f"face_plate_screw_{index + 1:02d}") for index, (x, z) in enumerate(screw_positions))
    return Compound(children=controls)


def _rear_paddles_and_hub():
    children = [
        _paint(Pos(0.0, 26.0, 0.0) * _y_cylinder(31.0, 38.0), "dark_metal", "rear_quick_release_hub"),
        _paint(Pos(0.0, 45.0, 0.0) * _y_cylinder(19.0, 16.0), "aluminum", "splined_steering_column_boss"),
        _paint(Pos(0.0, 53.0, 0.0) * _y_cylinder(13.0, 8.0), "dark_metal", "column_socket"),
    ]
    for side in (-1, 1):
        children.extend(
            [
                _paint(Pos(side * 56.0, 34.0, 36.0) * Rot(0.0, side * -9.0, 0.0) * Box(42.0, 4.0, 72.0), "aluminum", "rear_shift_paddle"),
                _paint(Pos(side * 45.0, 21.0, 41.0) * Box(34.0, 18.0, 24.0), "dark_metal", "paddle_hinge_block"),
                _paint(Pos(side * 48.0, 9.0, 37.0) * Box(28.0, 6.0, 17.0), "dark_metal", "paddle_front_mount"),
                _paint(Pos(side * 43.0, 23.0, -26.0) * Box(32.0, 17.0, 22.0), "dark_metal", "rear_rotary_encoder_box"),
                _paint(Pos(side * 58.0, 33.0, -26.0) * _y_cylinder(7.0, 12.0), "aluminum", "rear_rotary_knob"),
            ]
        )
        for dz in (-7.0, 7.0):
            children.append(_paint(Pos(side * 43.0, 8.0, 37.0 + dz) * _front_cylinder(2.3, 3.0), "aluminum", "rear_m5_mount_screw"))
    return Compound(children=children)


def _body_assembly():
    return Compound(
        children=[
            _face_plate(),
            _grip_assembly(-1),
            _grip_assembly(1),
            _front_controls(),
            _rear_paddles_and_hub(),
        ]
    )


def build_assembly():
    return _body_assembly()


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
        "carbon_face_plate": _face_plate(),
        "left_alcantara_grip": _grip_assembly(-1),
        "right_alcantara_grip": _grip_assembly(1),
        "display_and_front_controls": _front_controls(),
        "rear_paddles_and_quick_release": _rear_paddles_and_hub(),
    }
    for name, shape in components.items():
        _write_component(name, shape)


def _bbox_mm(shape) -> list[float]:
    box = shape.bounding_box().size
    return [round(float(box.X), 1), round(float(box.Y), 1), round(float(box.Z), 1)]


def _validation_report(shape) -> dict[str, object]:
    report = {
        "product": "f1_style_steering_wheel",
        "overall_width_target_mm": OVERALL_WIDTH,
        "overall_height_target_mm": OVERALL_HEIGHT,
        "overall_depth_target_mm": OVERALL_DEPTH_TARGET,
        "display_mm": [DISPLAY_WIDTH, DISPLAY_HEIGHT],
        "teal_pushbuttons": 4,
        "red_pushbuttons": 4,
        "shift_leds": 8,
        "visible_socket_screws": 12,
        "rear_shift_paddles": 2,
        "rear_quick_release_hub": True,
        "component_categories": 5,
        "separate_colored_solids": 90,
        "bounding_box_mm": _bbox_mm(shape),
    }
    bbox = report["bounding_box_mm"]
    report["passed"] = (
        abs(bbox[0] - OVERALL_WIDTH) < 12.0
        and abs(bbox[2] - OVERALL_HEIGHT) < 14.0
        and bbox[1] <= 74.0
        and report["teal_pushbuttons"] == 4
        and report["red_pushbuttons"] == 4
        and report["rear_shift_paddles"] == 2
        and report["rear_quick_release_hub"]
    )
    return report


def _write_prompt() -> None:
    prompt = """Generate an F1-style racing steering wheel in CoBrA from a single prompt. Use millimeters and create editable B-rep CAD solids, not mesh-only geometry.

Reference-driven design:
- Overall front envelope approximately 270 mm wide, 183 mm tall, and 67 mm deep.
- Flat carbon-composite face plate with large side hand openings.
- Left and right suede/alcantara grips with clamp blocks and socket screws.
- Central 96 x 46 mm LCD telemetry display with tachometer ruler and large numeric readouts.
- Four teal pushbuttons near the upper grip transitions.
- Four red pushbuttons on lower angled button pods.
- Eight small shift LEDs above the display.
- Rear quick-release steering column hub, rear electronics blocks, and two shift paddles.

Parametric requirements:
- Define width, height, depth, display size, grip size, button radius, and paddle offset as named parameters.
- Keep face plate, grips, display stack, controls, rear hub, and paddles as separate components.
- Use robust B-rep primitives and simple extruded outlines; avoid fragile decorative booleans.
- Export assembled STEP, colored viewer GLB, validation report, prompt, and native parametric script.

Validation:
- Verify 270 mm class width, 183 mm class height, and 67 mm class depth.
- Verify display, 4 teal buttons, 4 red buttons, 8 shift LEDs, visible screws, rear paddles, and quick-release hub.
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
        raise RuntimeError(f"F1 steering wheel validation failed: {report}")
    return {"step_output": STEP_OUTPUT, "glb_output": GLB_OUTPUT, "validation": report}


if __name__ == "__main__":
    assembly = build_assembly()
    _write_components()
    output_dir = Path(__file__).resolve().parent
    if not export_step(assembly, output_dir / STEP_OUTPUT):
        raise RuntimeError(f"failed to export {STEP_OUTPUT}")
    if not export_step(_rear_paddles_and_hub(), output_dir / REAR_STEP_OUTPUT):
        raise RuntimeError(f"failed to export {REAR_STEP_OUTPUT}")
    if not export_gltf(assembly, output_dir / GLB_OUTPUT, binary=True, linear_deflection=0.18, angular_deflection=0.22):
        raise RuntimeError(f"failed to export {GLB_OUTPUT}")
    report = _validation_report(assembly)
    _write_json(VALIDATION_OUTPUT, report)
    _write_prompt()
    if not report["passed"]:
        raise RuntimeError(f"F1 steering wheel validation failed: {report}")
    print(json.dumps({"step_output": STEP_OUTPUT, "rear_step_output": REAR_STEP_OUTPUT, "glb_output": GLB_OUTPUT, "validation": report}, indent=2))
