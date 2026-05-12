from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_014_bicycle_pedal_crank_assembly_components"
COMPONENT_REVISION = "asm_014_bicycle_pedal_crank_assembly-v2"


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


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _bottom_bracket_shell():
    return _x_cylinder(7.0, 22.0)


def _crank_arm():
    return Box(58.0, 5.0, 6.0)


def _spider_ring():
    return _z_cylinder(12.0, 3.5)


def _chainring_arc():
    return _z_cylinder(22.0, 2.5)


def _pedal_body():
    return Box(22.0, 12.0, 5.0)


def _pedal_axle():
    return _x_cylinder(2.0, 26.0)


def _bearing_cap():
    return _x_cylinder(4.0, 4.0)


def _chainring_bolt():
    return _z_cylinder(1.8, 4.0)


def _reflector_block():
    return Box(10.0, 1.6, 3.0)


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    bolts = [
        _leaf("chainring_bolt_north", paths["chainring_bolt"], 0.0, 16.5, 7.5),
        _leaf("chainring_bolt_east", paths["chainring_bolt"], 16.5, 0.0, 7.5),
        _leaf("chainring_bolt_south", paths["chainring_bolt"], 0.0, -16.5, 7.5),
        _leaf("chainring_bolt_west", paths["chainring_bolt"], -16.5, 0.0, 7.5),
    ]
    reflectors = [
        _leaf("pedal_front_reflector", paths["reflector_block"], 68.0, -9.0, 0.0),
        _leaf("pedal_rear_reflector", paths["reflector_block"], 68.0, 9.0, 0.0),
    ]
    return [
        _subassembly("bottom_bracket_module", [
            _leaf("bottom_bracket_shell", paths["bottom_bracket_shell"], 0.0, 0.0, 0.0),
            _leaf("left_bearing_cap", paths["bearing_cap"], -13.0, 0.0, 0.0),
            _leaf("right_bearing_cap", paths["bearing_cap"], 13.0, 0.0, 0.0),
        ]),
        _subassembly("crank_arm_module", [
            _leaf("drive_side_crank_arm", paths["crank_arm"], 33.0, 0.0, 0.0),
            _leaf("counterweight_crank_arm_stub", paths["crank_arm"], -33.0, 0.0, 0.0),
        ]),
        _subassembly("chainring_spider_module", [
            _leaf("spider_ring", paths["spider_ring"], 0.0, 0.0, 6.0),
            _leaf("outer_chainring", paths["chainring_arc"], 0.0, 0.0, 4.0),
            *bolts,
        ]),
        _subassembly("pedal_module", [
            _leaf("pedal_axle", paths["pedal_axle"], 55.0, 0.0, 0.0),
            _leaf("pedal_platform_body", paths["pedal_body"], 72.0, 0.0, 0.0),
            *reflectors,
        ]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "bottom_bracket_shell": _write_component("bottom_bracket_shell", _bottom_bracket_shell()),
        "crank_arm": _write_component("crank_arm", _crank_arm()),
        "spider_ring": _write_component("spider_ring", _spider_ring()),
        "chainring_arc": _write_component("chainring_arc", _chainring_arc()),
        "pedal_body": _write_component("pedal_body", _pedal_body()),
        "pedal_axle": _write_component("pedal_axle", _pedal_axle()),
        "bearing_cap": _write_component("bearing_cap", _bearing_cap()),
        "chainring_bolt": _write_component("chainring_bolt", _chainring_bolt()),
        "reflector_block": _write_component("reflector_block", _reflector_block()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_014_bicycle_pedal_crank_assembly.step"}
