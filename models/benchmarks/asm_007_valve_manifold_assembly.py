from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_007_valve_manifold_assembly_components"
COMPONENT_REVISION = "asm007-v1-valve-manifold"


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


def _manifold_body():
    pieces = [
        Box(52.0, 23.0, 16.0),
        _x_cylinder(9.0, 58.0),
        Pos(0.0, 0.0, 10.0) * Box(22.0, 18.0, 12.0),
        Pos(0.0, 0.0, 17.0) * _z_cylinder(5.5, 8.0),
    ]
    return Compound(children=pieces)


def _flange():
    pieces = [_x_cylinder(14.5, 6.0), _x_cylinder(9.5, 7.0)]
    for y in (-8.5, 8.5):
        for z in (-8.5, 8.5):
            pieces.append(Pos(0.0, y, z) * _x_cylinder(1.5, 7.5))
    return Compound(children=pieces)


def _gasket_ring():
    return Compound(children=[_x_cylinder(15.2, 1.4), _x_cylinder(10.0, 1.8)])


def _valve_stem():
    return Compound(children=[_z_cylinder(1.8, 28.0), Pos(0.0, 0.0, 12.0) * _z_cylinder(3.0, 4.0)])


def _hand_wheel():
    pieces = [_z_cylinder(9.5, 2.6), _z_cylinder(2.0, 4.0), Box(19.0, 1.8, 1.4), Box(1.8, 19.0, 1.4)]
    return Compound(children=pieces)


def _mounting_foot():
    return Compound(children=[Box(24.0, 8.0, 5.0), Pos(-6.0, 0.0, 3.5) * _z_cylinder(2.0, 2.5), Pos(6.0, 0.0, 3.5) * _z_cylinder(2.0, 2.5)])


def _cover_plate():
    return Compound(children=[Box(26.0, 20.0, 3.0), Pos(-8.0, 0.0, 2.0) * _z_cylinder(1.6, 2.5), Pos(8.0, 0.0, 2.0) * _z_cylinder(1.6, 2.5)])


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    return [
        _subassembly("manifold_body_module", [
            _leaf("manifold_body_block", paths["manifold_body"], 0.0, 0.0, 17.0),
            _leaf("top_cover_plate", paths["cover_plate"], 0.0, 0.0, 30.0),
        ]),
        _subassembly("inlet_flange_module", [_leaf("inlet_flange", paths["flange"], -40.0, 0.0, 17.0), _leaf("inlet_gasket_ring", paths["gasket_ring"], -35.5, 0.0, 17.0)]),
        _subassembly("outlet_flange_module", [_leaf("outlet_flange", paths["flange"], 40.0, 0.0, 17.0), _leaf("outlet_gasket_ring", paths["gasket_ring"], 35.5, 0.0, 17.0)]),
        _subassembly("valve_stem_module", [_leaf("valve_stem", paths["valve_stem"], 0.0, 0.0, 29.0)]),
        _subassembly("hand_wheel_module", [_leaf("hand_wheel", paths["hand_wheel"], 0.0, 0.0, 41.5)]),
        _subassembly("mounting_foot_module", [_leaf("front_mounting_foot", paths["mounting_foot"], 0.0, -23.5, 3.0), _leaf("rear_mounting_foot", paths["mounting_foot"], 0.0, 23.5, 3.0)]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "manifold_body": _write_component("manifold_body", _manifold_body()),
        "flange": _write_component("flange", _flange()),
        "gasket_ring": _write_component("gasket_ring", _gasket_ring()),
        "valve_stem": _write_component("valve_stem", _valve_stem()),
        "hand_wheel": _write_component("hand_wheel", _hand_wheel()),
        "mounting_foot": _write_component("mounting_foot", _mounting_foot()),
        "cover_plate": _write_component("cover_plate", _cover_plate()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_007_valve_manifold_assembly.step"}
