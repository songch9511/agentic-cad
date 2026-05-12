from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_004_linear_rail_carriage_assembly_components"
COMPONENT_REVISION = "asm004-v1-linear-rail"


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


def _y_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Rot(90, 0, 0) * Cylinder(radius, length)


def _z_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Cylinder(radius, length)


def _guide_rail():
    pieces = [
        Box(96.0, 8.0, 5.0),
        Pos(0.0, -6.0, 4.0) * Box(92.0, 3.0, 4.0),
        Pos(0.0, 6.0, 4.0) * Box(92.0, 3.0, 4.0),
        Pos(-39.0, 0.0, 6.0) * _z_cylinder(2.4, 3.0),
        Pos(39.0, 0.0, 6.0) * _z_cylinder(2.4, 3.0),
    ]
    return Compound(children=pieces)


def _carriage_block():
    pieces = [
        Box(34.0, 25.0, 10.0),
        Pos(0.0, -12.5, -1.5) * Box(30.0, 3.0, 7.0),
        Pos(0.0, 12.5, -1.5) * Box(30.0, 3.0, 7.0),
        Pos(-11.0, 0.0, 6.2) * _z_cylinder(2.2, 2.5),
        Pos(11.0, 0.0, 6.2) * _z_cylinder(2.2, 2.5),
    ]
    return Compound(children=pieces)


def _roller():
    return Compound(children=[_y_cylinder(3.8, 5.6), _y_cylinder(2.0, 6.4)])


def _end_stop():
    return Compound(children=[Box(6.0, 31.0, 14.0), Pos(0.0, 0.0, 8.0) * Box(7.5, 16.0, 3.0)])


def _clamp_plate():
    return Compound(children=[Box(32.0, 29.0, 3.0), Pos(-10.5, 0.0, 2.0) * _z_cylinder(1.8, 2.5), Pos(10.5, 0.0, 2.0) * _z_cylinder(1.8, 2.5)])


def _rail_mount_pad():
    return Compound(children=[Box(12.0, 12.0, 3.0), Pos(0.0, 0.0, 2.0) * _z_cylinder(2.0, 2.5)])


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    rollers = [
        _leaf(f"roller_{index}", paths["roller"], x, y, 13.5)
        for index, (x, y) in enumerate(((-21.0, -16.5), (21.0, -16.5), (-21.0, 16.5), (21.0, 16.5)), start=1)
    ]
    return [
        _subassembly("rail_module", [
            _leaf("guide_rail", paths["guide_rail"], 0.0, 0.0, 3.0),
            _leaf("left_rail_mount_pad", paths["rail_mount_pad"], -30.0, 0.0, 10.0),
            _leaf("right_rail_mount_pad", paths["rail_mount_pad"], 30.0, 0.0, 10.0),
        ]),
        _subassembly("carriage_module", [_leaf("moving_carriage_block", paths["carriage_block"], 0.0, 0.0, 14.0)]),
        _subassembly("roller_module", rollers),
        _subassembly("end_stop_module", [_leaf("left_end_stop", paths["end_stop"], -48.0, 0.0, 10.0), _leaf("right_end_stop", paths["end_stop"], 48.0, 0.0, 10.0)]),
        _subassembly("clamp_plate_module", [_leaf("clamp_plate", paths["clamp_plate"], 0.0, 0.0, 23.0)]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "guide_rail": _write_component("guide_rail", _guide_rail()),
        "carriage_block": _write_component("carriage_block", _carriage_block()),
        "roller": _write_component("roller", _roller()),
        "end_stop": _write_component("end_stop", _end_stop()),
        "clamp_plate": _write_component("clamp_plate", _clamp_plate()),
        "rail_mount_pad": _write_component("rail_mount_pad", _rail_mount_pad()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_004_linear_rail_carriage_assembly.step"}
