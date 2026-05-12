from __future__ import annotations

import math
from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


DISPLAY_NAME = "BRIEF-001 tracked concept vehicle assembly"

COMPONENT_DIR = "brief_001_tracked_vehicle_assembly_components"
COMPONENT_REVISION = "brief001-v5-side-visible-track-detail"

LENGTH = 120.0
WIDTH = 70.0
HEIGHT = 57.0
TRACK_LENGTH = 120.0
TRACK_WIDTH = 14.0
TRACK_HEIGHT = 22.0
TRACK_Y = 27.4
TRACK_Z = 11.0
LOWER_HULL_LENGTH = 92.0
LOWER_HULL_WIDTH = 38.0
LOWER_HULL_HEIGHT = 14.0
UPPER_HULL_LENGTH = 70.0
UPPER_HULL_WIDTH = 42.0
UPPER_HULL_HEIGHT = 16.0
ROAD_WHEEL_COUNT_PER_SIDE = 5
TRACK_PAD_XS = (-46.0, -33.0, -20.0, -7.0, 7.0, 20.0, 33.0, 46.0)


def _component_path(name: str) -> Path:
    return Path(__file__).resolve().parent / COMPONENT_DIR / f"{name}.step"


def _y_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Rot(90, 0, 0) * Cylinder(radius, length)


def _x_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Rot(0, 90, 0) * Cylinder(radius, length)


def _write_component(name: str, shape) -> str:
    output = _component_path(name)
    if output.exists() and _component_topology_path(output).exists() and _component_is_current(output):
        return f"{COMPONENT_DIR}/{name}.step"
    output.parent.mkdir(parents=True, exist_ok=True)
    if not export_step(shape, output):
        raise RuntimeError(f"failed to export component STEP: {output}")
    _write_component_topology(output)
    _component_revision_path(output).write_text(COMPONENT_REVISION + "\n", encoding="utf-8")
    return f"{COMPONENT_DIR}/{name}.step"


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


def _track_body():
    belt_width = TRACK_WIDTH * 0.56
    top_z = TRACK_HEIGHT / 2 - 1.35
    bottom_z = -TRACK_HEIGHT / 2 + 1.2
    end_x = TRACK_LENGTH / 2 - TRACK_HEIGHT / 4
    side_y = belt_width / 2 + 0.7
    pieces = [
        Pos(0.0, 0.0, top_z) * Box(92.0, belt_width, 2.0),
        Pos(0.0, 0.0, bottom_z) * Box(102.0, belt_width, 2.2),
        Pos(end_x, 0.0, 5.2) * Rot(0, 34, 0) * Box(16.0, belt_width, 2.2),
        Pos(end_x, 0.0, -5.2) * Rot(0, -34, 0) * Box(16.0, belt_width, 2.2),
        Pos(-end_x, 0.0, 5.2) * Rot(0, -34, 0) * Box(16.0, belt_width, 2.2),
        Pos(-end_x, 0.0, -5.2) * Rot(0, 34, 0) * Box(16.0, belt_width, 2.2),
    ]
    for y in (-side_y, side_y):
        pieces.append(Pos(0.0, y, top_z + 0.95) * Box(92.0, 1.1, 1.1))
        pieces.append(Pos(0.0, y, bottom_z - 1.05) * Box(102.0, 1.2, 1.1))
        for x in TRACK_PAD_XS:
            pieces.append(Pos(x, y, top_z + 1.9) * Box(5.2, 2.2, 1.4))
            pieces.append(Pos(x, y, bottom_z - 2.0) * Box(5.4, 2.3, 1.5))
        for x, z, angle in (
            (55.0, 5.8, 34.0),
            (57.5, 0.0, 0.0),
            (55.0, -5.8, -34.0),
            (-55.0, 5.8, -34.0),
            (-57.5, 0.0, 0.0),
            (-55.0, -5.8, 34.0),
        ):
            pieces.append(Pos(x, y, z) * Rot(0, angle, 0) * Box(3.0, 2.2, 5.0))
        for x in (-36.0, -18.0, 0.0, 18.0, 36.0):
            pieces.append(Pos(x + 1.7, y, -1.0) * Rot(0, -18, 0) * Box(12.0, 1.2, 1.0))
        for x in (-30.0, 0.0, 30.0):
            pieces.append(Pos(x, y, 4.0) * Rot(90, 0, 0) * Cylinder(2.6, 1.4))
        for x in (-47.0, -23.0, 1.0, 25.0, 49.0):
            pieces.append(Pos(x, y, 6.2) * Box(9.0, 1.25, 1.8))
    return Compound(children=pieces)


def _track_pad():
    pad = Box(5.8, 5.2, 1.55)
    pad += Pos(0.0, 0.0, 0.75) * Box(3.8, 5.9, 0.8)
    return pad


def _track_end_pad():
    pad = Box(2.2, 5.2, 5.2)
    pad += Pos(0.0, 0.0, 0.0) * Box(2.8, 5.9, 2.8)
    return pad


def _road_wheel():
    wheel = _y_cylinder(7.0, 5.2)
    wheel += _y_cylinder(3.2, 6.4)
    for face_y in (-3.35, 3.35):
        for angle in (0, 90):
            wheel += Pos(0.0, face_y, 0.0) * Rot(0, angle, 0) * Box(11.2, 0.75, 0.9)
    return wheel


def _drive_sprocket():
    sprocket = _y_cylinder(8.8, 6.2)
    sprocket += _y_cylinder(3.0, 7.2)
    for index in range(10):
        angle = 2.0 * math.pi * index / 10.0
        x = math.cos(angle) * 9.4
        z = math.sin(angle) * 9.4
        sprocket += Pos(x, 0.0, z) * Rot(0, -math.degrees(angle), 0) * Box(2.0, 7.0, 2.9)
    for face_y in (-3.65, 3.65):
        for angle in (0, 90):
            sprocket += Pos(0.0, face_y, 0.0) * Rot(0, angle, 0) * Box(13.6, 0.65, 0.75)
    return sprocket


def _idler_wheel():
    idler = _y_cylinder(7.4, 5.8)
    idler += _y_cylinder(2.5, 6.6)
    for face_y in (-3.35, 3.35):
        idler += Pos(0.0, face_y, 0.0) * Box(10.5, 0.65, 0.8)
        idler += Pos(0.0, face_y, 0.0) * Box(0.8, 0.65, 10.5)
    return idler


def _return_roller():
    roller = _y_cylinder(3.5, 4.8)
    roller += _y_cylinder(1.4, 5.6)
    return roller


def _suspension_arm():
    arm = Box(12.5, 2.1, 1.7)
    arm += Pos(-5.2, 0.0, 0.0) * _y_cylinder(1.55, 2.5)
    arm += Pos(5.2, 0.0, 0.0) * _y_cylinder(1.55, 2.5)
    arm += Pos(0.0, 0.0, 1.0) * Box(8.5, 1.6, 0.9)
    return arm


def _side_skirt():
    panels = [
        Pos(0.0, 0.0, 3.1) * Box(94.0, 2.0, 2.2),
        Pos(-38.0, 0.0, 0.1) * Box(12.0, 2.4, 4.8),
        Pos(-12.0, 0.0, 0.1) * Box(12.0, 2.4, 4.8),
        Pos(14.0, 0.0, 0.1) * Box(12.0, 2.4, 4.8),
        Pos(40.0, 0.0, 0.1) * Box(12.0, 2.4, 4.8),
    ]
    return Compound(children=panels)


def _front_guard():
    guard = [
        Pos(0.0, -11.0, 0.0) * Box(5.0, 3.5, 3.0),
        Pos(0.0, 11.0, 0.0) * Box(5.0, 3.5, 3.0),
        Pos(0.8, 0.0, 2.0) * Box(3.2, 28.0, 1.7),
        Pos(-0.6, 0.0, -1.1) * Box(1.6, 24.0, 1.4),
    ]
    return Compound(children=guard)


def _lower_hull():
    tub = Box(76.0, LOWER_HULL_WIDTH, 11.0)
    tub += Pos(41.0, 0.0, 1.1) * Rot(0, 18, 0) * Box(20.0, LOWER_HULL_WIDTH, 5.8)
    tub += Pos(-42.0, 0.0, 0.8) * Rot(0, -12, 0) * Box(17.0, LOWER_HULL_WIDTH, 5.4)
    glacis_cap = Pos(8.0, 0.0, LOWER_HULL_HEIGHT / 2 + 0.2) * Box(68.0, 30.0, 2.5)
    side_sponsons = [
        Pos(1.0, y, 1.0) * Box(76.0, 3.0, 9.0)
        for y in (-LOWER_HULL_WIDTH / 2 - 2.0, LOWER_HULL_WIDTH / 2 + 2.0)
    ]
    tow_points = [
        Pos(50.0, y, -1.8) * Box(5.0, 4.0, 3.0)
        for y in (-10.0, 10.0)
    ]
    rear_blocks = [
        Pos(-47.0, y, -1.2) * Box(4.5, 4.0, 2.2)
        for y in (-11.0, 11.0)
    ]
    return Compound(children=[tub, glacis_cap, *side_sponsons, *tow_points, *rear_blocks])


def _upper_hull():
    hull = Box(UPPER_HULL_LENGTH, UPPER_HULL_WIDTH, 13.5)
    hull += Pos(33.0, 0.0, 1.4) * Rot(0, 14, 0) * Box(15.0, UPPER_HULL_WIDTH, 4.2)
    hull += Pos(-33.0, 0.0, 1.1) * Rot(0, -10, 0) * Box(14.0, UPPER_HULL_WIDTH, 3.8)
    hull += Pos(6.0, 0.0, 7.6) * Box(42.0, 33.0, 2.0)
    hull += Pos(29.0, 0.0, 5.0) * Box(8.0, 18.0, 4.0)
    hull += Pos(-24.0, 0.0, 7.9) * Box(22.0, 24.0, 1.2)
    for x in (-22.0, 20.0):
        hull += Pos(x, -15.2, 8.6) * Box(18.0, 2.1, 1.4)
        hull += Pos(x, 15.2, 8.6) * Box(18.0, 2.1, 1.4)
    return hull


def _deck_plate():
    plate = Box(21.0, 29.0, 1.4)
    plate += Pos(0.0, -9.0, 0.9) * Box(16.0, 1.0, 0.8)
    plate += Pos(0.0, 0.0, 0.9) * Box(16.0, 1.0, 0.8)
    plate += Pos(0.0, 9.0, 0.9) * Box(16.0, 1.0, 0.8)
    return plate


def _hatch():
    hatch = Cylinder(5.6, 1.6)
    hatch += Pos(0.0, 0.0, 1.25) * Box(6.0, 2.0, 1.0)
    return hatch


def _turret_sensor_module():
    return Compound(
        children=[
            Pos(0.0, 0.0, 2.8) * Cylinder(12.0, 5.6),
            Pos(2.5, 0.0, 6.8) * Box(21.0, 15.0, 5.0),
            Pos(-5.5, 0.0, 9.6) * Box(10.0, 10.5, 1.8),
            Pos(8.0, 0.0, 10.4) * Box(8.0, 8.0, 1.3),
        ]
    )


def _optic_block():
    optic = Box(9.5, 10.0, 4.7)
    optic += _x_cylinder(1.55, 1.9, x=5.55, y=-2.8, z=0.65)
    optic += _x_cylinder(1.55, 1.9, x=5.55, y=2.8, z=0.65)
    optic += Pos(5.2, 0.0, -1.1) * Box(1.0, 7.8, 1.2)
    return optic


def _antenna_mast():
    mast = Pos(0.0, 0.0, 4.6) * Cylinder(0.55, 9.2)
    mast += Pos(0.0, 0.0, 9.55) * Cylinder(1.0, 0.7)
    return mast


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [
        1.0,
        0.0,
        0.0,
        x,
        0.0,
        1.0,
        0.0,
        y,
        0.0,
        0.0,
        1.0,
        z,
        0.0,
        0.0,
        0.0,
        1.0,
    ]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _track_module(name: str, y: float, outer_sign: float, paths: dict[str, str]) -> dict[str, object]:
    wheel_y = outer_sign * (TRACK_WIDTH / 2 - 1.2)
    belt_children: list[dict[str, object]] = [
        _leaf(f"{name}_open_track_belt", paths["track_body"], 0.0, 0.0, 0.0),
    ]

    running_children: list[dict[str, object]] = []
    for index, x in enumerate((-36.0, -18.0, 0.0, 18.0, 36.0), start=1):
        running_children.append(_leaf(f"{name}_road_wheel_{index}", paths["road_wheel"], x, wheel_y, -3.4))
    running_children.extend(
        [
            _leaf(f"{name}_front_drive_sprocket", paths["drive_sprocket"], TRACK_LENGTH / 2 - TRACK_HEIGHT / 2, wheel_y, 0.0),
            _leaf(f"{name}_rear_drive_sprocket", paths["drive_sprocket"], -TRACK_LENGTH / 2 + TRACK_HEIGHT / 2, wheel_y, 0.0),
        ]
    )
    children = [
        _subassembly(f"{name}_track_belt_module", belt_children),
        _subassembly(f"{name}_running_gear_module", running_children),
    ]
    return {"name": name, "transform": _identity_at(0.0, y, TRACK_Z), "children": children}


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    return [
        {
            "name": "chassis_module",
            "transform": _identity_at(0.0, 0.0, 0.0),
            "children": [
                _track_module("left_track_module", -TRACK_Y, -1.0, paths),
                _track_module("right_track_module", TRACK_Y, 1.0, paths),
                _leaf("lower_hull", paths["lower_hull"], 0.0, 0.0, 18.0),
            ],
        },
        {
            "name": "upper_body_module",
            "transform": _identity_at(0.0, 0.0, 0.0),
            "children": [
                _leaf("upper_hull", paths["upper_hull"], 4.0, 0.0, 32.0),
                {
                    "name": "deck_detail_module",
                    "transform": _identity_at(0.0, 0.0, 0.0),
                    "children": [
                        _leaf("commander_hatch", paths["hatch"], -7.0, 0.0, 44.0),
                    ],
                },
            ],
        },
        {
            "name": "turret_sensor_module",
            "transform": _identity_at(0.0, 0.0, 0.0),
            "children": [
                _leaf("top_sensor_pod", paths["turret_sensor"], 12.0, 0.0, 45.0),
                _leaf("front_optic_block", paths["optic_block"], 28.0, 0.0, 51.0),
                _leaf("antenna_mast", paths["antenna_mast"], -3.0, -7.0, 47.2),
            ],
        },
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "lower_hull": _write_component("lower_hull", _lower_hull()),
        "upper_hull": _write_component("upper_hull", _upper_hull()),
        "track_body": _write_component("track_body", _track_body()),
        "road_wheel": _write_component("road_wheel", _road_wheel()),
        "drive_sprocket": _write_component("drive_sprocket", _drive_sprocket()),
        "hatch": _write_component("hatch", _hatch()),
        "turret_sensor": _write_component("turret_sensor_module", _turret_sensor_module()),
        "optic_block": _write_component("optic_block", _optic_block()),
        "antenna_mast": _write_component("antenna_mast", _antenna_mast()),
    }
    return {
        "children": _assembly_children(paths),
        "step_output": "brief_001_tracked_vehicle_assembly.step",
    }
