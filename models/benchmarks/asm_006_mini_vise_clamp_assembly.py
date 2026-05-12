from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_006_mini_vise_clamp_assembly_components"
COMPONENT_REVISION = "asm006-v1-mini-vise"


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


def _z_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Cylinder(radius, length)


def _base_frame():
    pieces = [
        Box(90.0, 18.0, 5.0),
        Pos(0.0, -16.0, 4.0) * Box(78.0, 4.0, 6.0),
        Pos(0.0, 16.0, 4.0) * Box(78.0, 4.0, 6.0),
        Pos(-36.0, -16.0, 7.0) * _z_cylinder(2.3, 3.0),
        Pos(-36.0, 16.0, 7.0) * _z_cylinder(2.3, 3.0),
        Pos(36.0, -16.0, 7.0) * _z_cylinder(2.3, 3.0),
        Pos(36.0, 16.0, 7.0) * _z_cylinder(2.3, 3.0),
    ]
    return Compound(children=pieces)


def _jaw_block():
    return Compound(children=[Box(10.0, 38.0, 26.0), Pos(0.0, 0.0, 11.0) * Box(12.0, 30.0, 6.0)])


def _jaw_plate():
    return Compound(children=[Box(2.2, 39.5, 16.0), Pos(0.0, 0.0, 5.5) * Box(2.6, 32.0, 3.0)])


def _screw_spindle():
    return Compound(children=[_x_cylinder(1.8, 75.0), Pos(38.0, 0.0, 0.0) * _x_cylinder(3.4, 5.0)])


def _guide_rod():
    return _x_cylinder(1.45, 72.0)


def _handle_bar():
    return Compound(children=[_y_cylinder(1.25, 43.0), Pos(0.0, -22.5, 0.0) * _y_cylinder(2.6, 3.0), Pos(0.0, 22.5, 0.0) * _y_cylinder(2.6, 3.0)])


def _end_cap():
    return Compound(children=[Box(4.0, 34.0, 9.0), _z_cylinder(2.0, 3.0, y=-12.0, z=5.0), _z_cylinder(2.0, 3.0, y=12.0, z=5.0)])


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    return [
        _subassembly("base_frame_module", [
            _leaf("base_frame_slide", paths["base_frame"], 0.0, 0.0, 3.0),
            _leaf("left_end_cap", paths["end_cap"], -43.0, 0.0, 8.0),
            _leaf("right_end_cap", paths["end_cap"], 43.0, 0.0, 8.0),
        ]),
        _subassembly("fixed_jaw_module", [_leaf("fixed_jaw_body", paths["jaw_block"], -36.0, 0.0, 18.0), _leaf("fixed_jaw_plate", paths["jaw_plate"], -29.8, 0.0, 18.0)]),
        _subassembly("moving_jaw_module", [_leaf("moving_jaw_body", paths["jaw_block"], 18.0, 0.0, 17.0), _leaf("moving_jaw_plate", paths["jaw_plate"], 11.8, 0.0, 17.0)]),
        _subassembly(
            "guide_module",
            [_leaf("upper_guide_rod", paths["guide_rod"], 1.0, -12.5, 15.0), _leaf("lower_guide_rod", paths["guide_rod"], 1.0, 12.5, 15.0)],
        ),
        _subassembly("screw_module", [_leaf("screw_spindle", paths["screw_spindle"], 1.0, 0.0, 22.0), _leaf("handle_bar", paths["handle_bar"], 44.0, 0.0, 22.0)]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "base_frame": _write_component("base_frame", _base_frame()),
        "jaw_block": _write_component("jaw_block", _jaw_block()),
        "jaw_plate": _write_component("jaw_plate", _jaw_plate()),
        "screw_spindle": _write_component("screw_spindle", _screw_spindle()),
        "guide_rod": _write_component("guide_rod", _guide_rod()),
        "handle_bar": _write_component("handle_bar", _handle_bar()),
        "end_cap": _write_component("end_cap", _end_cap()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_006_mini_vise_clamp_assembly.step"}
