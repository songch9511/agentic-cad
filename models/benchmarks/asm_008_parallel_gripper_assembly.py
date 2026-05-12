from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_008_parallel_gripper_assembly_components"
COMPONENT_REVISION = "asm008-v1-parallel-gripper"


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


def _palm():
    pieces = [
        Box(38.0, 38.0, 10.0),
        Pos(12.0, -12.0, 6.0) * _z_cylinder(2.6, 4.0),
        Pos(12.0, 12.0, 6.0) * _z_cylinder(2.6, 4.0),
        Pos(-12.0, -12.0, 6.0) * _z_cylinder(2.6, 4.0),
        Pos(-12.0, 12.0, 6.0) * _z_cylinder(2.6, 4.0),
    ]
    return Compound(children=pieces)


def _finger():
    return Compound(children=[Box(48.0, 7.5, 8.0), Pos(20.0, 0.0, 4.0) * Box(10.0, 9.0, 8.0)])


def _grip_pad():
    return Compound(children=[Box(8.0, 6.0, 14.0), Pos(0.0, 0.0, 5.5) * Box(9.0, 6.5, 2.0)])


def _pivot_pin():
    return _z_cylinder(2.0, 24.0)


def _link_bar():
    return Compound(children=[Box(42.0, 4.0, 3.5), Pos(-18.0, 0.0, 0.0) * _z_cylinder(1.6, 4.0), Pos(18.0, 0.0, 0.0) * _z_cylinder(1.6, 4.0)])


def _actuator_cylinder():
    return Compound(children=[_x_cylinder(4.2, 28.0), Pos(20.0, 0.0, 0.0) * _x_cylinder(1.6, 24.0), Pos(-16.5, 0.0, 0.0) * Box(4.0, 10.0, 7.0)])


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    pivot_children = []
    for index, (x, y) in enumerate(((-3.0, -24.0), (17.0, -24.0), (-3.0, 24.0), (17.0, 24.0)), start=1):
        pivot_children.append(_leaf(f"pivot_pin_{index}", paths["pivot_pin"], x, y, 14.0))
    return [
        _subassembly("palm_module", [_leaf("palm_base", paths["palm"], -22.0, 0.0, 8.0)]),
        _subassembly("left_finger_module", [_leaf("left_finger_arm", paths["finger"], 20.0, -28.0, 14.0), _leaf("left_grip_pad", paths["grip_pad"], 45.0, -31.0, 14.0)]),
        _subassembly("right_finger_module", [_leaf("right_finger_arm", paths["finger"], 20.0, 28.0, 14.0), _leaf("right_grip_pad", paths["grip_pad"], 45.0, 31.0, 14.0)]),
        _subassembly("linkage_module", [*pivot_children, _leaf("left_link_bar", paths["link_bar"], 7.0, -16.0, 24.0), _leaf("right_link_bar", paths["link_bar"], 7.0, 16.0, 24.0)]),
        _subassembly("actuator_module", [_leaf("actuator_cylinder", paths["actuator_cylinder"], -36.0, 0.0, 20.0)]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "palm": _write_component("palm", _palm()),
        "finger": _write_component("finger", _finger()),
        "grip_pad": _write_component("grip_pad", _grip_pad()),
        "pivot_pin": _write_component("pivot_pin", _pivot_pin()),
        "link_bar": _write_component("link_bar", _link_bar()),
        "actuator_cylinder": _write_component("actuator_cylinder", _actuator_cylinder()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_008_parallel_gripper_assembly.step"}
