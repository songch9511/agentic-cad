from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_002_wheel_bogie_assembly_components"
COMPONENT_REVISION = "asm002-v1-compact-bogie"

WHEEL_XS = (-30.0, -10.0, 10.0, 30.0)
WHEEL_CENTER_Z = 9.0
BRACKET_Y = 21.0


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
    _component_revision_path(output).write_text(COMPONENT_REVISION + "\n", encoding="utf-8")
    return f"{COMPONENT_DIR}/{name}.step"


def _x_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Rot(0, 90, 0) * Cylinder(radius, length)


def _y_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Rot(90, 0, 0) * Cylinder(radius, length)


def _z_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Cylinder(radius, length)


def _carrier_frame():
    pieces = [
        Box(88.0, 12.0, 5.0),
        Pos(-39.0, 0.0, 0.0) * Box(6.0, 42.0, 5.0),
        Pos(39.0, 0.0, 0.0) * Box(6.0, 42.0, 5.0),
        Pos(0.0, 0.0, 7.5) * Box(68.0, 8.0, 3.0),
    ]
    for x in (-34.0, 34.0):
        for y in (-13.0, 13.0):
            pieces.append(_z_cylinder(2.8, 2.5, x=x, y=y, z=4.0))
    return Compound(children=pieces)


def _side_bracket():
    pieces = [
        Box(82.0, 3.0, 28.0),
        Pos(-34.0, 0.0, 5.0) * Box(6.0, 4.2, 18.0),
        Pos(34.0, 0.0, 5.0) * Box(6.0, 4.2, 18.0),
        Pos(0.0, 0.0, 11.5) * Box(58.0, 4.0, 5.0),
    ]
    for x in WHEEL_XS:
        pieces.append(_y_cylinder(4.2, 4.2, x=x, y=0.0, z=-6.0))
        pieces.append(_y_cylinder(2.1, 4.8, x=x, y=0.0, z=-6.0))
    return Compound(children=pieces)


def _road_wheel():
    pieces = [
        _y_cylinder(8.2, 7.5),
        _y_cylinder(5.6, 8.3),
        _y_cylinder(2.6, 9.0),
    ]
    for face_y in (-4.45, 4.45):
        pieces.append(Pos(0.0, face_y, 0.0) * Box(12.0, 0.7, 1.0))
        pieces.append(Pos(0.0, face_y, 0.0) * Box(1.0, 0.7, 12.0))
    return Compound(children=pieces)


def _axle_rod():
    return _y_cylinder(1.4, 43.5)


def _spacer_bushing():
    pieces = [
        _y_cylinder(2.8, 4.8),
        _y_cylinder(1.6, 5.4),
    ]
    return Compound(children=pieces)


def _spring_shock():
    pieces = [
        _x_cylinder(1.15, 50.0),
        _x_cylinder(2.1, 13.0, x=-18.5),
        _x_cylinder(2.1, 13.0, x=18.5),
        Pos(-25.0, 0.0, 0.0) * Box(4.0, 6.0, 4.0),
        Pos(25.0, 0.0, 0.0) * Box(4.0, 6.0, 4.0),
    ]
    return Compound(children=pieces)


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


def _wheel_set_children(paths: dict[str, str]) -> list[dict[str, object]]:
    wheel_children = [
        _leaf(f"road_wheel_{index}", paths["road_wheel"], x, 0.0, WHEEL_CENTER_Z)
        for index, x in enumerate(WHEEL_XS, start=1)
    ]

    axle_children: list[dict[str, object]] = []
    for index, x in enumerate(WHEEL_XS, start=1):
        axle_children.append(_leaf(f"axle_rod_{index}", paths["axle_rod"], x, 0.0, WHEEL_CENTER_Z))
        axle_children.append(_leaf(f"left_spacer_bushing_{index}", paths["spacer_bushing"], x, -10.5, WHEEL_CENTER_Z))
        axle_children.append(_leaf(f"right_spacer_bushing_{index}", paths["spacer_bushing"], x, 10.5, WHEEL_CENTER_Z))

    return [
        _subassembly("road_wheel_module", wheel_children),
        _subassembly("axle_module", axle_children),
    ]


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    return [
        _subassembly(
            "carrier_frame_module",
            [
                _leaf("carrier_base_rail", paths["carrier_frame"], 0.0, 0.0, 21.0),
                _leaf("simple_spring_shock_cylinder", paths["spring_shock"], 0.0, 0.0, 32.0),
            ],
        ),
        _subassembly(
            "left_bracket_module",
            [_leaf("left_side_plate_bracket", paths["side_bracket"], 0.0, -BRACKET_Y, 15.0)],
        ),
        _subassembly(
            "right_bracket_module",
            [_leaf("right_side_plate_bracket", paths["side_bracket"], 0.0, BRACKET_Y, 15.0)],
        ),
        _subassembly("wheel_set_module", _wheel_set_children(paths)),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "carrier_frame": _write_component("carrier_frame", _carrier_frame()),
        "side_bracket": _write_component("side_bracket", _side_bracket()),
        "road_wheel": _write_component("road_wheel", _road_wheel()),
        "axle_rod": _write_component("axle_rod", _axle_rod()),
        "spacer_bushing": _write_component("spacer_bushing", _spacer_bushing()),
        "spring_shock": _write_component("spring_shock", _spring_shock()),
    }
    return {
        "children": _assembly_children(paths),
        "step_output": "asm_002_wheel_bogie_assembly.step",
    }
