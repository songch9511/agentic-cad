from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_013_toggle_clamp_assembly_components"
COMPONENT_REVISION = "asm_013_toggle_clamp_assembly-v1"


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

def _base_plate():
    return Box(70.0, 28.0, 4.0)


def _mounting_boss():
    return Compound(children=[_z_cylinder(2.6, 3.0), _z_cylinder(1.2, 3.5)])


def _upright_bracket():
    return Compound(children=[Box(8.0, 24.0, 24.0), Box(13.0, 5.0, 20.0, x=0.0) if False else Box(13.0, 5.0, 20.0)])


def _handle_lever():
    return Compound(children=[Box(44.0, 5.0, 5.0), Box(10.0, 7.0, 7.0, x=-18.0) if False else Box(10.0, 7.0, 7.0)])


def _grip_handle():
    return _x_cylinder(3.2, 16.0)


def _link_bar():
    return Compound(children=[Box(30.0, 3.0, 3.0), _z_cylinder(1.6, 4.0, x=-13.0), _z_cylinder(1.6, 4.0, x=13.0)])


def _pivot_pin():
    return _y_cylinder(1.8, 34.0)


def _clamp_screw():
    return _x_cylinder(1.5, 26.0)


def _pressure_pad():
    return Compound(children=[Box(10.0, 10.0, 3.0), _z_cylinder(2.0, 2.5, z=2.0)])


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    bosses = [_leaf(f"mounting_boss_{i}", paths["mounting_boss"], x, y, 5.0) for i, (x, y) in enumerate(((-25.0, -10.0), (25.0, -10.0), (-25.0, 10.0), (25.0, 10.0)), start=1)]
    return [
        _subassembly("toggle_base_module", [_leaf("toggle_base_plate", paths["base_plate"], 0.0, 0.0, 2.5), *bosses, _leaf("upright_bracket", paths["upright_bracket"], -18.0, 0.0, 16.0)]),
        _subassembly("handle_module", [_leaf("handle_lever", paths["handle_lever"], 3.0, 0.0, 30.0), _leaf("rubber_grip_handle", paths["grip_handle"], 31.0, 0.0, 30.0)]),
        _subassembly("link_bar_module", [_leaf("left_link_bar", paths["link_bar"], 8.0, -9.0, 21.0), _leaf("right_link_bar", paths["link_bar"], 8.0, 9.0, 21.0)]),
        _subassembly("pivot_pin_module", [_leaf("rear_pivot_pin", paths["pivot_pin"], -18.0, 0.0, 26.0), _leaf("center_pivot_pin", paths["pivot_pin"], 4.0, 0.0, 24.0), _leaf("front_pivot_pin", paths["pivot_pin"], 24.0, 0.0, 18.0)]),
        _subassembly("clamp_foot_module", [_leaf("clamp_screw", paths["clamp_screw"], 30.0, 0.0, 16.0), _leaf("pressure_pad", paths["pressure_pad"], 43.0, 0.0, 12.0)]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "base_plate": _write_component("base_plate", _base_plate()),
        "mounting_boss": _write_component("mounting_boss", _mounting_boss()),
        "upright_bracket": _write_component("upright_bracket", _upright_bracket()),
        "handle_lever": _write_component("handle_lever", _handle_lever()),
        "grip_handle": _write_component("grip_handle", _grip_handle()),
        "link_bar": _write_component("link_bar", _link_bar()),
        "pivot_pin": _write_component("pivot_pin", _pivot_pin()),
        "clamp_screw": _write_component("clamp_screw", _clamp_screw()),
        "pressure_pad": _write_component("pressure_pad", _pressure_pad()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_013_toggle_clamp_assembly.step"}

