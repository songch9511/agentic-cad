from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_005_pulley_tensioner_assembly_components"
COMPONENT_REVISION = "asm005-v1-pulley-tensioner"


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


def _y_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Rot(90, 0, 0) * Cylinder(radius, length)


def _fixed_bracket():
    pieces = [
        Box(22.0, 44.0, 5.0),
        Pos(-2.0, 0.0, 12.0) * Box(16.0, 38.0, 23.0),
        Pos(8.0, -16.0, 9.0) * Box(12.0, 5.0, 16.0),
        Pos(8.0, 16.0, 9.0) * Box(12.0, 5.0, 16.0),
        Pos(-7.0, -15.5, 16.0) * _y_cylinder(2.8, 5.5),
        Pos(-7.0, 15.5, 16.0) * _y_cylinder(2.8, 5.5),
    ]
    return Compound(children=pieces)


def _pivot_arm():
    pieces = [
        Box(50.0, 6.0, 7.0),
        Pos(-21.0, 0.0, 0.0) * _y_cylinder(4.0, 7.0),
        Pos(22.0, 0.0, 0.0) * _y_cylinder(4.5, 7.0),
    ]
    return Compound(children=pieces)


def _pulley_wheel():
    pieces = [_y_cylinder(11.5, 9.5), _y_cylinder(8.6, 10.5), _y_cylinder(2.8, 12.0)]
    for y in (-5.6, 5.6):
        pieces.append(Pos(0.0, y, 0.0) * Box(15.0, 0.7, 1.0))
        pieces.append(Pos(0.0, y, 0.0) * Box(1.0, 0.7, 15.0))
    return Compound(children=pieces)


def _axle_pin():
    return _y_cylinder(1.8, 43.0)


def _spacer_bushing():
    return Compound(children=[_y_cylinder(3.0, 4.8), _y_cylinder(1.7, 5.6)])


def _adjustment_screw():
    pieces = [
        _x_cylinder(1.3, 34.0),
        Pos(18.0, 0.0, 0.0) * _x_cylinder(3.0, 4.0),
        Pos(-18.0, 0.0, 0.0) * Box(3.0, 8.0, 5.0),
    ]
    return Compound(children=pieces)


def _adjustment_knob():
    return Compound(children=[_x_cylinder(3.8, 5.0), Box(2.0, 12.0, 7.0)])


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    return [
        _subassembly("fixed_bracket_module", [_leaf("fixed_bracket_body", paths["fixed_bracket"], -32.0, 0.0, 7.0)]),
        _subassembly("pivot_arm_module", [_leaf("pivot_arm_link", paths["pivot_arm"], 2.0, 0.0, 22.0)]),
        _subassembly("pulley_module", [_leaf("pulley_wheel", paths["pulley_wheel"], 29.0, 0.0, 21.0)]),
        _subassembly(
            "axle_module",
            [
                _leaf("axle_pin", paths["axle_pin"], 29.0, 0.0, 21.0),
                _leaf("left_spacer_bushing", paths["spacer_bushing"], 29.0, -12.0, 21.0),
                _leaf("right_spacer_bushing", paths["spacer_bushing"], 29.0, 12.0, 21.0),
                _leaf("pivot_axle_pin", paths["axle_pin"], -19.0, 0.0, 22.0),
            ],
        ),
        _subassembly("adjustment_screw_module", [
            _leaf("adjustment_screw", paths["adjustment_screw"], 10.0, 0.0, 36.0),
            _leaf("adjustment_knob", paths["adjustment_knob"], 30.0, 0.0, 36.0),
            _leaf("adjustment_lock_block", paths["adjustment_knob"], -8.0, 0.0, 36.0),
        ]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "fixed_bracket": _write_component("fixed_bracket", _fixed_bracket()),
        "pivot_arm": _write_component("pivot_arm", _pivot_arm()),
        "pulley_wheel": _write_component("pulley_wheel", _pulley_wheel()),
        "axle_pin": _write_component("axle_pin", _axle_pin()),
        "spacer_bushing": _write_component("spacer_bushing", _spacer_bushing()),
        "adjustment_screw": _write_component("adjustment_screw", _adjustment_screw()),
        "adjustment_knob": _write_component("adjustment_knob", _adjustment_knob()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_005_pulley_tensioner_assembly.step"}
