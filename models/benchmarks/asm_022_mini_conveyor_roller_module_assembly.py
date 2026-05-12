from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_022_mini_conveyor_roller_module_assembly_components"
COMPONENT_REVISION = "asm022-v1-mini-conveyor"
ROLLER_XS = (-45.0, -27.0, -9.0, 9.0, 27.0, 45.0)
ROLLER_Z = 13.0
RAIL_Y = 25.0


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


def _base_frame():
    pieces = [
        Box(122.0, 10.0, 5.0),
        Pos(-57.0, 0.0, 4.0) * Box(6.0, 50.0, 8.0),
        Pos(57.0, 0.0, 4.0) * Box(6.0, 50.0, 8.0),
        Pos(0.0, -20.0, 2.5) * Box(108.0, 4.0, 6.0),
        Pos(0.0, 20.0, 2.5) * Box(108.0, 4.0, 6.0),
    ]
    for x in (-48.0, -16.0, 16.0, 48.0):
        for y in (-18.0, 18.0):
            pieces.append(_z_cylinder(2.5, 2.4, x=x, y=y, z=6.0))
    return Compound(children=pieces)


def _side_rail():
    pieces = [Box(116.0, 4.0, 18.0), Pos(0.0, 0.0, 8.5) * Box(116.0, 6.0, 3.0)]
    for x in ROLLER_XS:
        pieces.append(_y_cylinder(3.6, 5.5, x=x, z=-3.0))
    return Compound(children=pieces)


def _roller():
    pieces = [_y_cylinder(5.8, 41.0), _y_cylinder(4.5, 43.0), _y_cylinder(1.6, 46.0)]
    for y in (-18.0, 18.0):
        pieces.append(Pos(0.0, y, 0.0) * Box(9.0, 1.0, 1.2))
        pieces.append(Pos(0.0, y, 0.0) * Box(1.2, 1.0, 9.0))
    return Compound(children=pieces)


def _shaft_pin():
    return _y_cylinder(1.5, 52.0)


def _bearing_block():
    return Compound(children=[Box(8.0, 5.0, 8.0), _y_cylinder(2.4, 5.8)])


def _drive_motor():
    return Compound(children=[
        _x_cylinder(7.0, 16.0),
        Pos(-10.0, 0.0, 0.0) * Box(7.0, 16.0, 16.0),
        _x_cylinder(2.0, 10.0, x=12.0),
        Pos(-15.0, 0.0, -8.0) * Box(8.0, 18.0, 3.0),
    ])


def _support_foot():
    return Compound(children=[Box(14.0, 10.0, 4.0), _z_cylinder(2.0, 3.0, z=2.5)])


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _roller_children(paths: dict[str, str]) -> list[dict[str, object]]:
    rollers = [_leaf(f"conveyor_roller_{idx}", paths["roller"], x, 0.0, ROLLER_Z) for idx, x in enumerate(ROLLER_XS, 1)]
    shafts: list[dict[str, object]] = []
    bearings: list[dict[str, object]] = []
    for idx, x in enumerate(ROLLER_XS, 1):
        shafts.append(_leaf(f"roller_shaft_pin_{idx}", paths["shaft_pin"], x, 0.0, ROLLER_Z))
        bearings.append(_leaf(f"left_bearing_block_{idx}", paths["bearing_block"], x, -RAIL_Y, ROLLER_Z))
        bearings.append(_leaf(f"right_bearing_block_{idx}", paths["bearing_block"], x, RAIL_Y, ROLLER_Z))
    return [_subassembly("roller_bank_module", rollers), _subassembly("shaft_pin_module", shafts), _subassembly("bearing_block_module", bearings)]


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    return [
        _subassembly("base_frame_module", [_leaf("conveyor_base_frame", paths["base_frame"], 0.0, 0.0, 4.0)]),
        _subassembly("side_guard_module", [_leaf("left_side_rail_guard", paths["side_rail"], 0.0, -RAIL_Y, 14.0), _leaf("right_side_rail_guard", paths["side_rail"], 0.0, RAIL_Y, 14.0)]),
        _subassembly("roller_bed_module", _roller_children(paths)),
        _subassembly("drive_motor_module", [_leaf("right_angle_drive_motor", paths["drive_motor"], -62.0, -30.0, 16.0)]),
        _subassembly("mounting_foot_module", [
            _leaf("mounting_foot_1", paths["support_foot"], -50.0, -22.0, -4.0),
            _leaf("mounting_foot_2", paths["support_foot"], 50.0, -22.0, -4.0),
            _leaf("mounting_foot_3", paths["support_foot"], -50.0, 22.0, -4.0),
            _leaf("mounting_foot_4", paths["support_foot"], 50.0, 22.0, -4.0),
        ]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "base_frame": _write_component("base_frame", _base_frame()),
        "side_rail": _write_component("side_rail", _side_rail()),
        "roller": _write_component("conveyor_roller", _roller()),
        "shaft_pin": _write_component("roller_shaft_pin", _shaft_pin()),
        "bearing_block": _write_component("bearing_block", _bearing_block()),
        "drive_motor": _write_component("drive_motor", _drive_motor()),
        "support_foot": _write_component("support_foot", _support_foot()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_022_mini_conveyor_roller_module_assembly.step"}
