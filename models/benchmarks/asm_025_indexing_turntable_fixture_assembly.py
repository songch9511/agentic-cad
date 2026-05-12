from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_025_indexing_turntable_fixture_assembly_components"
COMPONENT_REVISION = "asm025-v1-indexing-turntable"
INDEX_POSITIONS = ((32.0, 0.0), (22.6, 22.6), (0.0, 32.0), (-22.6, 22.6), (-32.0, 0.0), (-22.6, -22.6), (0.0, -32.0), (22.6, -22.6))
CLAMP_POSITIONS = ((42.0, 0.0), (0.0, 42.0), (-42.0, 0.0), (0.0, -42.0))


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
    completed = subprocess.run([sys.executable, str(script), str(step_path)], cwd=repo_root, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"failed to generate component topology for {step_path}:\n{completed.stdout}\n{completed.stderr}")


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


def _z_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Cylinder(radius, length)


def _base_plinth():
    pieces = [_z_cylinder(47.0, 7.0), _z_cylinder(34.0, 12.0, z=6.0)]
    for x, y in CLAMP_POSITIONS:
        pieces.append(Pos(x, y, 8.0) * Box(16.0, 10.0, 5.0))
    return Compound(children=pieces)


def _turntable_disk():
    pieces = [_z_cylinder(36.0, 6.0), _z_cylinder(15.0, 10.0, z=6.0)]
    for x, y in INDEX_POSITIONS:
        pieces.append(_z_cylinder(2.0, 3.0, x=x, y=y, z=5.0))
    return Compound(children=pieces)


def _center_bearing():
    return Compound(children=[_z_cylinder(18.0, 5.0), _z_cylinder(10.0, 8.0, z=4.0)])


def _index_pin():
    return Compound(children=[_z_cylinder(2.0, 13.0), _z_cylinder(3.2, 2.0, z=7.5)])


def _clamp_block():
    return Compound(children=[Box(14.0, 10.0, 9.0), Pos(0.0, 0.0, 5.0) * Box(18.0, 6.0, 4.0)])


def _clamp_screw():
    return Compound(children=[_x_cylinder(1.6, 24.0), _x_cylinder(3.2, 3.0, x=13.5), Pos(-13.0, 0.0, 0.0) * Box(3.0, 8.0, 8.0)])


def _fixture_jaw():
    return Compound(children=[Box(16.0, 5.0, 12.0), Pos(0.0, 2.0, 5.0) * Box(10.0, 4.0, 4.0)])


def _support_foot():
    return Compound(children=[Box(16.0, 12.0, 4.0), _z_cylinder(2.2, 3.0, z=2.5)])


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _clamp_children(paths: dict[str, str]) -> list[dict[str, object]]:
    children: list[dict[str, object]] = []
    for idx, (x, y) in enumerate(CLAMP_POSITIONS, 1):
        children.append(_leaf(f"fixture_clamp_block_{idx}", paths["clamp_block"], x, y, 20.0))
        children.append(_leaf(f"fixture_clamp_screw_{idx}", paths["clamp_screw"], x, y, 27.0))
        children.append(_leaf(f"fixture_jaw_{idx}", paths["fixture_jaw"], x * 0.78, y * 0.78, 27.0))
    return children


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    pins = [_leaf(f"index_pin_{idx}", paths["index_pin"], x, y, 23.0) for idx, (x, y) in enumerate(INDEX_POSITIONS, 1)]
    feet = [
        _leaf("support_foot_1", paths["support_foot"], -34.0, -34.0, -4.0),
        _leaf("support_foot_2", paths["support_foot"], 34.0, -34.0, -4.0),
        _leaf("support_foot_3", paths["support_foot"], -34.0, 34.0, -4.0),
        _leaf("support_foot_4", paths["support_foot"], 34.0, 34.0, -4.0),
    ]
    return [
        _subassembly("base_plinth_module", [_leaf("round_base_plinth", paths["base_plinth"], 0.0, 0.0, 4.0)] + feet),
        _subassembly("turntable_disk_module", [_leaf("rotating_turntable_disk", paths["turntable_disk"], 0.0, 0.0, 16.0), _leaf("center_bearing_stack", paths["center_bearing"], 0.0, 0.0, 12.0)]),
        _subassembly("index_pin_module", pins),
        _subassembly("fixture_clamp_module", _clamp_children(paths)),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "base_plinth": _write_component("base_plinth", _base_plinth()),
        "turntable_disk": _write_component("turntable_disk", _turntable_disk()),
        "center_bearing": _write_component("center_bearing", _center_bearing()),
        "index_pin": _write_component("index_pin", _index_pin()),
        "clamp_block": _write_component("clamp_block", _clamp_block()),
        "clamp_screw": _write_component("clamp_screw", _clamp_screw()),
        "fixture_jaw": _write_component("fixture_jaw", _fixture_jaw()),
        "support_foot": _write_component("support_foot", _support_foot()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_025_indexing_turntable_fixture_assembly.step"}
