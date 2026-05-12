from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_003_hinge_latch_assembly_components"
COMPONENT_REVISION = "asm003-v1-hinge-latch"

KNUCKLE_XS = (-25.0, -8.0, 9.0, 26.0)


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


def _leaf_plate():
    pieces = [
        Box(58.0, 11.5, 3.0),
        Pos(-24.0, 0.0, 2.6) * Box(7.0, 10.0, 2.0),
        Pos(24.0, 0.0, 2.6) * Box(7.0, 10.0, 2.0),
        Pos(0.0, 0.0, 3.8) * _x_cylinder(2.0, 50.0),
    ]
    return Compound(children=pieces)


def _hinge_knuckle():
    return Compound(children=[
        _x_cylinder(3.7, 11.0),
        Pos(0.0, 0.0, -3.2) * Box(10.5, 5.0, 2.0),
    ])


def _hinge_pin():
    return _x_cylinder(1.45, 68.0)


def _latch_catch():
    pieces = [
        Box(8.0, 13.0, 4.0),
        Pos(1.0, 0.0, 5.2) * Box(6.0, 9.0, 8.0),
        Pos(-2.5, 0.0, 9.8) * Box(8.0, 3.0, 3.0),
        _y_cylinder(1.6, 13.5, x=-1.5, y=0.0, z=8.8),
    ]
    return Compound(children=pieces)


def _mounting_boss():
    return Compound(children=[
        _z_cylinder(2.8, 3.2),
        _z_cylinder(1.45, 4.0),
    ])


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    base_bosses = [
        _leaf("mounting_boss_base_left", paths["mounting_boss"], -20.0, -10.5, 6.0),
        _leaf("mounting_boss_base_right", paths["mounting_boss"], 20.0, -10.5, 6.0),
    ]
    swing_bosses = [
        _leaf("mounting_boss_swing_left", paths["mounting_boss"], -20.0, 10.5, 6.0),
        _leaf("mounting_boss_swing_right", paths["mounting_boss"], 20.0, 10.5, 6.0),
    ]
    return [
        _subassembly("base_leaf_module", [_leaf("base_leaf_plate", paths["leaf_plate"], 0.0, -9.0, 2.0), *base_bosses]),
        _subassembly("swing_leaf_module", [_leaf("swing_leaf_plate", paths["leaf_plate"], 0.0, 9.0, 2.0), *swing_bosses]),
        _subassembly(
            "hinge_knuckle_module",
            [_leaf(f"hinge_knuckle_{index}", paths["hinge_knuckle"], x, 0.0, 9.5) for index, x in enumerate(KNUCKLE_XS, start=1)],
        ),
        _subassembly("hinge_pin_module", [_leaf("hinge_pin", paths["hinge_pin"], 0.0, 0.0, 9.5)]),
        _subassembly("latch_catch_module", [_leaf("latch_catch_keeper", paths["latch_catch"], 30.0, 8.5, 7.0)]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "leaf_plate": _write_component("leaf_plate", _leaf_plate()),
        "hinge_knuckle": _write_component("hinge_knuckle", _hinge_knuckle()),
        "hinge_pin": _write_component("hinge_pin", _hinge_pin()),
        "latch_catch": _write_component("latch_catch", _latch_catch()),
        "mounting_boss": _write_component("mounting_boss", _mounting_boss()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_003_hinge_latch_assembly.step"}
