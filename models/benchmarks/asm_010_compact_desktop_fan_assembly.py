from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_010_compact_desktop_fan_assembly_components"
COMPONENT_REVISION = "asm_010_compact_desktop_fan_assembly-v1"


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

def _fan_base():
    return Compound(children=[Box(46.0, 28.0, 5.0), _z_cylinder(2.4, 2.0, x=-18.0, y=-10.0, z=3.0), _z_cylinder(2.4, 2.0, x=18.0, y=-10.0, z=3.0)])


def _stand_post():
    return _z_cylinder(3.0, 34.0)


def _yoke_arm():
    return Compound(children=[Box(4.0, 5.0, 28.0), _y_cylinder(3.0, 6.0, z=13.0)])


def _fan_shroud():
    return Compound(children=[_y_cylinder(24.0, 5.0), _y_cylinder(20.0, 6.0)])


def _fan_hub():
    return _y_cylinder(6.0, 8.0)


def _fan_blade_horizontal():
    return Box(18.0, 1.5, 5.0)


def _fan_blade_vertical():
    return Box(5.0, 1.5, 18.0)


def _grill_bar_horizontal():
    return Box(42.0, 1.0, 1.3)


def _grill_bar_vertical():
    return Box(1.3, 1.0, 42.0)


def _switch_button():
    return Box(6.0, 4.0, 3.0)


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    return [
        _subassembly("fan_base_module", [_leaf("fan_base_plate", paths["fan_base"], 0.0, 0.0, 3.0), _leaf("switch_button", paths["switch_button"], -12.0, -10.0, 7.0)]),
        _subassembly("stand_module", [_leaf("vertical_stand_post", paths["stand_post"], 0.0, 0.0, 21.0), _leaf("left_yoke_arm", paths["yoke_arm"], -26.0, 0.0, 43.0), _leaf("right_yoke_arm", paths["yoke_arm"], 26.0, 0.0, 43.0)]),
        _subassembly("fan_housing_module", [_leaf("fan_shroud_guard", paths["fan_shroud"], 0.0, 0.0, 43.0), _leaf("fan_center_hub", paths["fan_hub"], 0.0, -1.0, 43.0)]),
        _subassembly("fan_blade_module", [_leaf("fan_blade_left", paths["fan_blade_horizontal"], -12.0, -2.5, 43.0), _leaf("fan_blade_right", paths["fan_blade_horizontal"], 12.0, -2.5, 43.0), _leaf("fan_blade_top", paths["fan_blade_vertical"], 0.0, -2.5, 55.0), _leaf("fan_blade_bottom", paths["fan_blade_vertical"], 0.0, -2.5, 31.0)]),
        _subassembly("front_grill_module", [_leaf("grill_bar_horizontal_top", paths["grill_bar_horizontal"], 0.0, -4.0, 53.0), _leaf("grill_bar_horizontal_bottom", paths["grill_bar_horizontal"], 0.0, -4.0, 33.0), _leaf("grill_bar_vertical_left", paths["grill_bar_vertical"], -10.0, -4.0, 43.0), _leaf("grill_bar_vertical_right", paths["grill_bar_vertical"], 10.0, -4.0, 43.0)]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "fan_base": _write_component("fan_base", _fan_base()),
        "stand_post": _write_component("stand_post", _stand_post()),
        "yoke_arm": _write_component("yoke_arm", _yoke_arm()),
        "fan_shroud": _write_component("fan_shroud", _fan_shroud()),
        "fan_hub": _write_component("fan_hub", _fan_hub()),
        "fan_blade_horizontal": _write_component("fan_blade_horizontal", _fan_blade_horizontal()),
        "fan_blade_vertical": _write_component("fan_blade_vertical", _fan_blade_vertical()),
        "grill_bar_horizontal": _write_component("grill_bar_horizontal", _grill_bar_horizontal()),
        "grill_bar_vertical": _write_component("grill_bar_vertical", _grill_bar_vertical()),
        "switch_button": _write_component("switch_button", _switch_button()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_010_compact_desktop_fan_assembly.step"}

