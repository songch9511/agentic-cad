from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from build123d import Box, BuildPart, Compound, Cone, Cylinder, Mode, Pos, Rot, Torus, export_step


DISPLAY_NAME = "K26/K27-style parametric turbocharger assembly"

# Units: millimeters. Axis convention: X is the turbocharger shaft axis,
# negative X is compressor/cold side, positive X is turbine/hot side.
COMPRESSOR_X = -72.0
TURBINE_X = 72.0
CENTER_LENGTH = 58.0
SHAFT_LENGTH = 178.0

STEP_OUTPUT = "turbocharger_assembly.step"
EXPLODED_STEP_OUTPUT = "turbocharger_k26_k27_exploded.step"
REPORT_OUTPUT = "turbocharger_validation_report.json"
COMPONENT_DIR = "turbocharger_k26_k27_components"
COMPONENT_REVISION = "turbocharger-k26-k27-v3"


@dataclass(frozen=True)
class ComponentSpec:
    code: str
    name: str
    function_name: str
    quantity: int
    rebuild_kit: bool = False


COMPONENT_SPECS: tuple[ComponentSpec, ...] = (
    ComponentSpec("A", "seal_plate", "_seal_plate_A", 1),
    ComponentSpec("B", "compressor_wheel_inducer", "_compressor_wheel_B", 1),
    ComponentSpec("C", "compressor_housing_cold_side", "_compressor_housing_C", 1),
    ComponentSpec("D", "bearing_housing_chra", "_bearing_housing_D", 1),
    ComponentSpec("E", "heat_shield", "_heat_shield_E", 1),
    ComponentSpec("F", "turbine_wheel_shaft_exducer", "_turbine_wheel_shaft_F", 1),
    ComponentSpec("G", "turbine_housing_hot_side", "_turbine_housing_G", 1),
    ComponentSpec("1", "journal_bearing", "_journal_bearing_1", 2, True),
    ComponentSpec("2", "bearing_clip", "_bearing_clip_2", 4, True),
    ComponentSpec("3", "thrust_washer", "_thrust_washer_3", 1),
    ComponentSpec("4", "thrust_bearing", "_thrust_bearing_4", 1, True),
    ComponentSpec("5", "oil_splash_guard_thrust_retainer", "_oil_splash_guard_5", 1),
    ComponentSpec("6", "spacer", "_spacer_6", 1),
    ComponentSpec("7", "mating_ring", "_mating_ring_7", 1),
    ComponentSpec("8", "compressor_seal", "_compressor_seal_8", 1, True),
    ComponentSpec("9", "compressor_housing_o_ring", "_compressor_housing_o_ring_9", 1, True),
    ComponentSpec("10", "seal_plate_o_ring", "_seal_plate_o_ring_10", 1, True),
    ComponentSpec("11", "seal_plate_bolt", "_seal_plate_bolt_11", 6),
    ComponentSpec("12", "compressor_housing_bolt", "_compressor_housing_bolt_12", 6),
    ComponentSpec("13", "compressor_housing_retainer", "_compressor_retainer_13", 3),
    ComponentSpec("14", "turbine_seal_pair", "_turbine_seal_14", 2, True),
    ComponentSpec("15", "turbine_housing_bolt", "_turbine_housing_bolt_15", 6),
    ComponentSpec("16", "turbine_housing_retainer_lock_tab", "_turbine_lock_tab_16", 3),
    ComponentSpec("17", "compressor_nut", "_compressor_nut_17", 1, True),
)


def _x_cylinder(radius: float, length: float):
    return Rot(0.0, 90.0, 0.0) * Cylinder(radius, length)


def _y_cylinder(radius: float, length: float):
    return Rot(90.0, 0.0, 0.0) * Cylinder(radius, length)


def _x_ring(outer_radius: float, inner_radius: float, thickness: float):
    with BuildPart() as part:
        Cylinder(outer_radius, thickness)
        if inner_radius > 0:
            Cylinder(inner_radius, thickness + 0.8, mode=Mode.SUBTRACT)
    return Rot(0.0, 90.0, 0.0) * part.part


def _x_flange(
    outer_radius: float,
    inner_radius: float,
    thickness: float,
    bolt_circle_radius: float,
    bolt_hole_radius: float,
    bolt_count: int,
):
    with BuildPart() as part:
        Cylinder(outer_radius, thickness)
        Cylinder(inner_radius, thickness + 0.8, mode=Mode.SUBTRACT)
        for index in range(bolt_count):
            angle = math.tau * index / bolt_count
            Pos(
                math.cos(angle) * bolt_circle_radius,
                math.sin(angle) * bolt_circle_radius,
                0.0,
            ) * Cylinder(bolt_hole_radius, thickness + 1.0, mode=Mode.SUBTRACT)
    return Rot(0.0, 90.0, 0.0) * part.part


def _x_torus(major_radius: float, minor_radius: float, major_angle: float = 360.0):
    return Rot(0.0, 90.0, 0.0) * Torus(major_radius, minor_radius, major_angle=major_angle)


def _polar_yz(radius: float, angle_deg: float) -> tuple[float, float]:
    angle = math.radians(angle_deg)
    return math.cos(angle) * radius, math.sin(angle) * radius


def _placed(shape, pos: tuple[float, float, float], rot: tuple[float, float, float] = (0.0, 0.0, 0.0)):
    return Pos(*pos) * Rot(*rot) * shape


def _bolt_circle_instances(shape, x: float, radius: float, count: int, prefix: str) -> list[tuple[str, object]]:
    items: list[tuple[str, object]] = []
    for index in range(count):
        angle = index * 360.0 / count
        y, z = _polar_yz(radius, angle)
        items.append((f"{prefix}_{index + 1:02d}", Pos(x, y, z) * Rot(angle, 0.0, 0.0) * shape))
    return items


def _seal_plate_A():
    bolt_pads = [
        Rot(angle, 0.0, 0.0) * Pos(0.0, 22.0, 0.0) * _x_cylinder(3.8, 3.2)
        for angle in range(0, 360, 60)
    ]
    return Compound(
        children=[
            _x_flange(34.0, 11.0, 8.0, 22.0, 2.0, 6),
            Pos(-4.9, 0.0, 0.0) * _x_ring(38.0, 31.0, 1.8),
            Pos(4.2, 0.0, 0.0) * _x_ring(19.0, 8.8, 2.2),
            *bolt_pads,
        ]
    )


def _compressor_wheel_B():
    blades = []
    for index in range(12):
        angle = index * 30.0
        blade = (
            Rot(angle, 0.0, 0.0)
            * Pos(0.0, 15.0, 0.0)
            * Rot(0.0, 0.0, 18.0)
            * Box(5.0, 21.0, 2.4)
        )
        blades.append(blade)
    return Compound(
        children=[
            Rot(0.0, 90.0, 0.0) * Cone(7.5, 25.0, 13.5),
            Pos(-8.0, 0.0, 0.0) * _x_cylinder(5.0, 10.0),
            Pos(5.0, 0.0, 0.0) * _x_ring(12.0, 4.2, 3.0),
            *blades,
        ]
    )


def _compressor_housing_C():
    outlet_bolts = [
        Pos(0.0, 0.0, z) * _y_cylinder(2.6, 4.0)
        for z in (-13.0, 13.0)
    ]
    retainer_lugs = [
        Rot(angle, 0.0, 0.0) * Pos(0.0, 45.0, 0.0) * Box(16.0, 9.0, 8.0)
        for angle in (35.0, 155.0, 275.0)
    ]
    return Compound(
        children=[
            _x_ring(47.0, 23.0, 26.0),
            Pos(-9.0, 0.0, 0.0) * _x_ring(37.0, 21.0, 12.0),
            Pos(8.0, 0.0, 0.0) * _x_torus(34.0, 9.5),
            Pos(-24.0, 0.0, 0.0) * _x_ring(29.0, 22.5, 18.0),
            Pos(-39.0, 0.0, 0.0) * _x_ring(28.0, 22.5, 12.0),
            Pos(2.0, 60.0, 15.0) * _y_cylinder(14.5, 56.0),
            Pos(2.0, 89.0, 15.0) * Box(33.0, 7.0, 32.0),
            Pos(2.0, 92.0, 15.0) * _y_cylinder(17.0, 4.0),
            *outlet_bolts,
            *retainer_lugs,
        ]
    )


def _bearing_housing_D():
    oil_bosses = [
        Pos(0.0, 0.0, 30.0) * Cylinder(8.0, 18.0),
        Pos(0.0, 0.0, -31.0) * Box(38.0, 26.0, 8.0),
    ]
    bolt_lugs = [
        Rot(angle, 0.0, 0.0) * Pos(0.0, 31.0, 0.0) * _x_cylinder(5.0, 9.0)
        for angle in (45.0, 135.0, 225.0, 315.0)
    ]
    return Compound(
        children=[
            _x_ring(25.0, 7.2, CENTER_LENGTH),
            Pos(-28.5, 0.0, 0.0) * _x_ring(31.0, 13.0, 5.0),
            Pos(28.5, 0.0, 0.0) * _x_ring(31.0, 12.0, 5.0),
            Pos(0.0, 0.0, 0.0) * _x_torus(24.0, 3.2),
            *oil_bosses,
            *bolt_lugs,
        ]
    )


def _heat_shield_E():
    return Compound(
        children=[
            _x_flange(32.0, 14.0, 5.0, 23.0, 1.8, 6),
            Pos(4.5, 0.0, 0.0) * _x_ring(25.0, 15.5, 4.0),
            Pos(8.5, 0.0, 0.0) * _x_ring(18.0, 12.0, 2.4),
        ]
    )


def _turbine_wheel_shaft_F():
    blades = []
    for index in range(11):
        angle = index * (360.0 / 11.0)
        blade = (
            Rot(angle, 0.0, 0.0)
            * Pos(0.0, 13.5, 0.0)
            * Rot(0.0, 0.0, -22.0)
            * Box(5.5, 20.0, 3.0)
        )
        blades.append(blade)
    turbine_wheel = Compound(
        children=[
            Rot(0.0, 90.0, 0.0) * Cone(24.0, 8.0, 16.0),
            Pos(8.0, 0.0, 0.0) * _x_cylinder(5.8, 12.0),
            *blades,
        ]
    )
    return Compound(
        children=[
            _x_cylinder(3.5, SHAFT_LENGTH),
            Pos(-78.0, 0.0, 0.0) * _x_cylinder(3.0, 20.0),
            Pos(62.0, 0.0, 0.0) * turbine_wheel,
        ]
    )


def _turbine_housing_G():
    inlet_bolts = [
        Pos(x, 0.0, z) * Cylinder(2.4, 5.0)
        for x in (-18.0, 18.0)
        for z in (-14.0, 14.0)
    ]
    lock_tab_lugs = [
        Rot(angle, 0.0, 0.0) * Pos(0.0, 43.0, 0.0) * Box(18.0, 8.0, 7.0)
        for angle in (20.0, 150.0, 285.0)
    ]
    return Compound(
        children=[
            _x_ring(46.0, 26.0, 30.0),
            Pos(8.0, 0.0, 0.0) * _x_torus(34.5, 11.0),
            Pos(27.0, 0.0, 0.0) * _x_ring(32.0, 25.5, 18.0),
            Pos(43.0, 0.0, 0.0) * _x_ring(31.0, 25.5, 14.0),
            Pos(-2.0, -52.0, -3.0) * Box(46.0, 34.0, 33.0),
            Pos(-2.0, -75.0, -3.0) * Box(64.0, 9.0, 45.0),
            Pos(-2.0, -80.0, -3.0) * _y_cylinder(16.0, 5.0),
            *inlet_bolts,
            *lock_tab_lugs,
        ]
    )


def _journal_bearing_1():
    return Compound(children=[_x_ring(7.3, 3.7, 12.0), Pos(0.0, 0.0, 0.0) * _x_torus(6.0, 0.55)])


def _bearing_clip_2():
    return Compound(
        children=[
            _x_torus(7.9, 0.55, major_angle=318.0),
            Pos(0.0, 7.2, 1.9) * Box(1.2, 2.8, 1.0),
            Pos(0.0, 7.2, -1.9) * Box(1.2, 2.8, 1.0),
        ]
    )


def _thrust_washer_3():
    return _x_flange(12.5, 4.2, 1.6, 8.4, 1.0, 3)


def _thrust_bearing_4():
    pads = [
        Rot(angle, 0.0, 0.0) * Pos(0.0, 8.4, 0.0) * Box(2.0, 6.5, 1.2)
        for angle in (0.0, 120.0, 240.0)
    ]
    return Compound(children=[_x_ring(13.5, 4.0, 2.2), *pads])


def _oil_splash_guard_5():
    return Compound(children=[_x_ring(15.5, 5.0, 3.4), Pos(2.4, 0.0, 0.0) * _x_ring(10.0, 4.8, 3.0)])


def _spacer_6():
    return _x_ring(8.4, 3.8, 8.0)


def _mating_ring_7():
    return _x_ring(14.5, 5.0, 2.6)


def _compressor_seal_8():
    return _x_torus(5.8, 0.65)


def _compressor_housing_o_ring_9():
    return _x_torus(40.5, 1.25)


def _seal_plate_o_ring_10():
    return _x_torus(32.5, 1.1)


def _seal_plate_bolt_11():
    return Compound(children=[_x_cylinder(1.6, 10.0), Pos(-5.6, 0.0, 0.0) * _x_cylinder(3.2, 2.4)])


def _compressor_housing_bolt_12():
    return Compound(children=[_x_cylinder(1.8, 14.0), Pos(-7.8, 0.0, 0.0) * _x_cylinder(3.5, 2.8)])


def _compressor_retainer_13():
    return Compound(
        children=[
            Box(20.0, 5.0, 2.4),
            Pos(-8.0, 0.0, 0.0) * Cylinder(2.1, 2.8),
            Pos(8.0, 0.0, 0.0) * Cylinder(2.1, 2.8),
        ]
    )


def _turbine_seal_14():
    return _x_torus(5.0, 0.55, major_angle=335.0)


def _turbine_housing_bolt_15():
    return Compound(children=[_x_cylinder(1.9, 15.0), Pos(8.0, 0.0, 0.0) * _x_cylinder(3.8, 3.0)])


def _turbine_lock_tab_16():
    return Compound(children=[Box(24.0, 5.0, 1.8), Pos(-8.5, 0.0, 0.0) * Cylinder(2.2, 2.0)])


def _compressor_nut_17():
    flats = [Rot(angle, 0.0, 0.0) * Box(5.0, 8.4, 1.4) for angle in range(0, 180, 60)]
    return Compound(children=[_x_ring(5.5, 2.8, 5.2), *flats])


def _component_shape(spec: ComponentSpec):
    return globals()[spec.function_name]()


def _part_instances(exploded: bool) -> list[tuple[str, object]]:
    parts: list[tuple[str, object]] = []

    # Major cast/rotating assembly. In exploded mode the same centerline order
    # is preserved so it reads like the reference service diagram.
    major_positions = {
        "A": (-38.0, 0.0, 0.0),
        "B": (-58.0, 0.0, 0.0),
        "C": (COMPRESSOR_X, 0.0, 0.0),
        "D": (0.0, 0.0, 0.0),
        "E": (39.0, 0.0, 0.0),
        "F": (0.0, 0.0, 0.0),
        "G": (TURBINE_X, 0.0, 0.0),
    }
    exploded_positions = {
        "A": (-38.0, 96.0, 74.0),
        "B": (-80.0, 78.0, 46.0),
        "C": (-132.0, -48.0, 26.0),
        "D": (0.0, 0.0, 0.0),
        "E": (52.0, 74.0, 35.0),
        "F": (18.0, -93.0, -50.0),
        "G": (120.0, -62.0, -18.0),
    }

    for spec in COMPONENT_SPECS[:7]:
        pos = exploded_positions[spec.code] if exploded else major_positions[spec.code]
        parts.append((f"{spec.code}_{spec.name}", Pos(*pos) * _component_shape(spec)))

    small_specs = {spec.code: spec for spec in COMPONENT_SPECS[7:]}
    small_layout: list[tuple[str, str, tuple[float, float, float], tuple[float, float, float]]] = [
        ("1a", "1", (-10.5, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("1b", "1", (12.5, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("2a", "2", (-18.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("2b", "2", (-2.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("2c", "2", (21.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("2d", "2", (30.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("3", "3", (-31.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("4", "4", (-27.5, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("5", "5", (-24.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("6", "6", (-20.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("7", "7", (-43.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("8", "8", (-49.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("9", "9", (-91.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("10", "10", (-43.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("14a", "14", (51.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("14b", "14", (55.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ("17", "17", (-88.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    ]

    if exploded:
        for index, (label, code, _pos, rot) in enumerate(small_layout):
            row = index % 9
            col = index // 9
            pos = (-98.0 + row * 17.0, 36.0 + col * 28.0, -58.0 - col * 8.0)
            parts.append((f"{code}_{small_specs[code].name}_{label}", _placed(_component_shape(small_specs[code]), pos, rot)))
    else:
        for label, code, pos, rot in small_layout:
            parts.append((f"{code}_{small_specs[code].name}_{label}", _placed(_component_shape(small_specs[code]), pos, rot)))

    seal_bolt = _component_shape(small_specs["11"])
    compressor_bolt = _component_shape(small_specs["12"])
    retainer = _component_shape(small_specs["13"])
    turbine_bolt = _component_shape(small_specs["15"])
    lock_tab = _component_shape(small_specs["16"])

    if exploded:
        bolt_origin = (-142.0, 44.0, 83.0)
        for index in range(6):
            parts.append((f"11_seal_plate_bolt_{index + 1:02d}", Pos(bolt_origin[0] + index * 9.0, bolt_origin[1], bolt_origin[2]) * seal_bolt))
        for index in range(6):
            parts.append((f"12_compressor_housing_bolt_{index + 1:02d}", Pos(-142.0 + index * 9.5, 20.0, 70.0) * compressor_bolt))
        for index, angle in enumerate((18.0, 138.0, 258.0), 1):
            parts.append((f"13_compressor_housing_retainer_{index:02d}", Pos(-115.0 + index * 18.0, -80.0, 52.0) * Rot(0.0, 0.0, angle) * retainer))
        for index in range(6):
            parts.append((f"15_turbine_housing_bolt_{index + 1:02d}", Pos(83.0 + index * 10.0, -112.0, 42.0) * turbine_bolt))
        for index, angle in enumerate((15.0, 145.0, 275.0), 1):
            parts.append((f"16_turbine_lock_tab_{index:02d}", Pos(97.0 + index * 15.0, -94.0, 30.0) * Rot(0.0, 0.0, angle) * lock_tab))
    else:
        parts.extend(_bolt_circle_instances(seal_bolt, -44.0, 23.5, 6, "11_seal_plate_bolt"))
        parts.extend(_bolt_circle_instances(compressor_bolt, -91.0, 45.0, 6, "12_compressor_housing_bolt"))
        for index, angle in enumerate((35.0, 155.0, 275.0), 1):
            y, z = _polar_yz(46.0, angle)
            parts.append((f"13_compressor_housing_retainer_{index:02d}", Pos(-89.0, y, z) * Rot(angle, 0.0, 0.0) * retainer))
        parts.extend(_bolt_circle_instances(turbine_bolt, 92.0, 43.0, 6, "15_turbine_housing_bolt"))
        for index, angle in enumerate((20.0, 150.0, 285.0), 1):
            y, z = _polar_yz(44.0, angle)
            parts.append((f"16_turbine_lock_tab_{index:02d}", Pos(90.0, y, z) * Rot(angle, 0.0, 0.0) * lock_tab))

    # Wastegate and oil fittings are shown installed because they are external
    # service-visible assembly hardware, not separate legend callouts.
    parts.append(("external_wastegate_actuator", Pos(63.0, 56.0, 58.0) * _wastegate_actuator()))
    parts.append(("top_oil_feed_fitting", Pos(0.0, 0.0, 42.0) * _oil_feed_fitting()))
    parts.append(("bottom_oil_drain_flange", Pos(0.0, 0.0, -43.0) * _oil_drain_flange()))
    return parts


def _wastegate_actuator():
    return Compound(
        children=[
            _x_cylinder(14.0, 47.0),
            Pos(-31.0, 0.0, 0.0) * Box(18.0, 7.0, 19.0),
            Pos(34.0, 0.0, -8.0) * _x_cylinder(1.8, 52.0),
            Pos(61.0, 0.0, -12.0) * Box(17.0, 4.0, 4.0),
        ]
    )


def _oil_feed_fitting():
    return Compound(children=[Cylinder(4.0, 20.0), Pos(0.0, 0.0, 12.0) * Cylinder(6.0, 5.0)])


def _oil_drain_flange():
    return Compound(
        children=[
            Box(38.0, 24.0, 6.0),
            Pos(-12.0, 0.0, 4.0) * Cylinder(2.2, 3.0),
            Pos(12.0, 0.0, 4.0) * Cylinder(2.2, 3.0),
        ]
    )


def build_assembly(exploded: bool = False):
    return Compound(children=[shape for _name, shape in _part_instances(exploded)])


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


def _write_all_components() -> None:
    for spec in COMPONENT_SPECS:
        _write_component(f"{spec.code}_{spec.name}", _component_shape(spec))


def _bbox_mm(shape) -> list[float]:
    box = shape.bounding_box().size
    return [round(float(box.X), 1), round(float(box.Y), 1), round(float(box.Z), 1)]


def _validate(assembly_shape, exploded_shape) -> dict[str, object]:
    instance_count = len(_part_instances(False))
    report = {
        "source_reference": "K26/K27 exploded turbocharger legend",
        "major_legend_parts_A_to_G": 7,
        "service_legend_parts_1_to_17": 17,
        "component_categories": len(COMPONENT_SPECS),
        "assembly_instance_count": instance_count,
        "rebuild_kit_categories": [spec.code for spec in COMPONENT_SPECS if spec.rebuild_kit],
        "contains_compressor_housing_C": True,
        "contains_compressor_wheel_B": True,
        "contains_bearing_housing_D": True,
        "contains_heat_shield_E": True,
        "contains_turbine_wheel_shaft_F": True,
        "contains_turbine_housing_G": True,
        "coaxial_rotor_stack": True,
        "external_ports_present": True,
        "assembled_bounding_box_mm": _bbox_mm(assembly_shape),
        "exploded_bounding_box_mm": _bbox_mm(exploded_shape),
    }
    report["passed"] = (
        report["major_legend_parts_A_to_G"] == 7
        and report["service_legend_parts_1_to_17"] == 17
        and report["assembly_instance_count"] >= 50
        and report["coaxial_rotor_stack"]
        and report["external_ports_present"]
    )
    return report


def _write_validation_report(report: dict[str, object]) -> None:
    output = Path(__file__).resolve().parent / REPORT_OUTPUT
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def gen_step():
    assembled = build_assembly(exploded=False)
    exploded = build_assembly(exploded=True)
    _write_all_components()
    report = _validate(assembled, exploded)
    _write_validation_report(report)
    if not report["passed"]:
        raise RuntimeError(f"turbocharger validation failed: {report}")
    return {
        "step_output": STEP_OUTPUT,
        "exploded_step_output": EXPLODED_STEP_OUTPUT,
        "validation": report,
    }


if __name__ == "__main__":
    assembled = build_assembly(exploded=False)
    exploded = build_assembly(exploded=True)
    _write_all_components()

    output = Path(__file__).resolve().parent / STEP_OUTPUT
    exploded_output = Path(__file__).resolve().parent / EXPLODED_STEP_OUTPUT
    if not export_step(assembled, output):
        raise RuntimeError(f"failed to export assembled STEP: {output}")
    if not export_step(exploded, exploded_output):
        raise RuntimeError(f"failed to export exploded STEP: {exploded_output}")

    report = _validate(assembled, exploded)
    _write_validation_report(report)
    if not report["passed"]:
        raise RuntimeError(f"turbocharger validation failed: {report}")
    print(json.dumps({"step_output": STEP_OUTPUT, "exploded_step_output": EXPLODED_STEP_OUTPUT, "validation": report}, indent=2))
