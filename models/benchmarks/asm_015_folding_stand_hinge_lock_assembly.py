from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_015_folding_stand_hinge_lock_assembly_components"
COMPONENT_REVISION = "asm_015_folding_stand_hinge_lock_assembly-v2"


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


def _base_foot():
    return Box(64.0, 14.0, 5.0)


def _folding_leg():
    return Box(9.0, 9.0, 58.0)


def _hinge_leaf():
    return Box(28.0, 4.0, 18.0)


def _hinge_pin():
    return _x_cylinder(2.2, 36.0)


def _lock_plate():
    return Box(32.0, 3.5, 9.0)


def _spring_plunger():
    return _x_cylinder(2.0, 24.0)


def _thumb_tab():
    return Box(12.0, 4.0, 8.0)


def _rubber_pad():
    return Box(16.0, 16.0, 4.0)


def _fastener_head():
    return _z_cylinder(1.8, 3.0)


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    hinge_screws = [
        _leaf("hinge_screw_upper_left", paths["fastener_head"], -18.0, -5.0, 23.0),
        _leaf("hinge_screw_upper_right", paths["fastener_head"], 18.0, -5.0, 23.0),
        _leaf("hinge_screw_lower_left", paths["fastener_head"], -18.0, -5.0, 8.0),
        _leaf("hinge_screw_lower_right", paths["fastener_head"], 18.0, -5.0, 8.0),
    ]
    base_screws = [
        _leaf("base_screw_left", paths["fastener_head"], -24.0, 0.0, 5.0),
        _leaf("base_screw_right", paths["fastener_head"], 24.0, 0.0, 5.0),
    ]
    return [
        _subassembly("base_foot_module", [
            _leaf("wide_base_foot", paths["base_foot"], 0.0, 0.0, 2.5),
            _leaf("left_rubber_pad", paths["rubber_pad"], -22.0, 0.0, -2.0),
            _leaf("right_rubber_pad", paths["rubber_pad"], 22.0, 0.0, -2.0),
            *base_screws,
        ]),
        _subassembly("folding_leg_module", [
            _leaf("front_folding_leg", paths["folding_leg"], -12.0, 0.0, 35.0),
            _leaf("rear_folding_leg", paths["folding_leg"], 12.0, 0.0, 35.0),
            _leaf("cross_tie_bar", paths["hinge_pin"], 0.0, 0.0, 60.0),
        ]),
        _subassembly("hinge_knuckle_module", [
            _leaf("fixed_hinge_leaf", paths["hinge_leaf"], 0.0, -5.0, 18.0),
            _leaf("moving_hinge_leaf", paths["hinge_leaf"], 0.0, 5.0, 27.0),
            _leaf("main_hinge_pin", paths["hinge_pin"], 0.0, 0.0, 24.0),
            *hinge_screws,
        ]),
        _subassembly("lock_plunger_module", [
            _leaf("notched_lock_plate", paths["lock_plate"], 0.0, 11.0, 31.0),
            _leaf("spring_plunger", paths["spring_plunger"], 0.0, 17.0, 31.0),
            _leaf("thumb_release_tab", paths["thumb_tab"], 17.0, 21.0, 35.0),
        ]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "base_foot": _write_component("base_foot", _base_foot()),
        "folding_leg": _write_component("folding_leg", _folding_leg()),
        "hinge_leaf": _write_component("hinge_leaf", _hinge_leaf()),
        "hinge_pin": _write_component("hinge_pin", _hinge_pin()),
        "lock_plate": _write_component("lock_plate", _lock_plate()),
        "spring_plunger": _write_component("spring_plunger", _spring_plunger()),
        "thumb_tab": _write_component("thumb_tab", _thumb_tab()),
        "rubber_pad": _write_component("rubber_pad", _rubber_pad()),
        "fastener_head": _write_component("fastener_head", _fastener_head()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_015_folding_stand_hinge_lock_assembly.step"}
