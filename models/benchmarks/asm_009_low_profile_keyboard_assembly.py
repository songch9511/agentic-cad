from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_009_low_profile_keyboard_assembly_components"
COMPONENT_REVISION = "asm009-v1-low-profile-keyboard"

MAIN_XS = tuple(-55.0 + 10.0 * index for index in range(12))
MAIN_YS = (5.0, -6.5, -18.0)
FUNCTION_XS = MAIN_XS
MODIFIER_LAYOUT = (
    ("left_modifier_key", -56.0, -28.0),
    ("meta_modifier_key", -39.0, -28.0),
    ("right_modifier_key", 30.0, -28.0),
    ("fn_modifier_key", 43.0, -28.0),
)
ARROW_LAYOUT = (
    ("left_arrow_key", 56.0, -30.0),
    ("right_arrow_key", 66.0, -30.0),
    ("up_arrow_key", 61.0, -25.0),
    ("down_arrow_key", 61.0, -35.0),
)


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


def _z_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Cylinder(radius, length)


def _keyboard_base():
    pieces = [
        Box(150.0, 55.0, 3.0),
        Pos(-68.0, -22.0, 2.3) * _z_cylinder(2.0, 1.6),
        Pos(68.0, -22.0, 2.3) * _z_cylinder(2.0, 1.6),
    ]
    return Compound(children=pieces)


def _keybed_panel():
    return Compound(children=[Box(138.0, 42.0, 1.0), Pos(0.0, 14.5, 0.7) * Box(132.0, 1.8, 0.8)])


def _rear_battery_ridge():
    return Compound(children=[_x_cylinder(3.0, 140.0), Pos(0.0, -2.5, -2.2) * Box(140.0, 4.0, 2.0)])


def _keycap():
    return Compound(children=[Box(8.0, 7.0, 1.5), Pos(0.0, 0.0, 0.9) * Box(3.0, 0.6, 0.3)])


def _function_key():
    return Compound(children=[Box(8.0, 5.5, 1.4), Pos(0.0, 0.0, 0.85) * Box(2.6, 0.5, 0.25)])


def _modifier_key():
    return Compound(children=[Box(13.0, 7.0, 1.5), Pos(0.0, 0.0, 0.9) * Box(4.0, 0.6, 0.3)])


def _spacebar_key():
    return Compound(children=[Box(45.0, 7.0, 1.5), Pos(0.0, 0.0, 0.9) * Box(18.0, 0.6, 0.3)])


def _arrow_key():
    return Compound(children=[Box(7.0, 6.0, 1.5), Pos(0.0, 0.0, 0.9) * Box(2.0, 0.5, 0.3)])


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _main_grid(paths: dict[str, str]) -> list[dict[str, object]]:
    children = []
    for row_index, y in enumerate(MAIN_YS, start=1):
        for col_index, x in enumerate(MAIN_XS, start=1):
            children.append(_leaf(f"keycap_r{row_index:02d}_c{col_index:02d}", paths["keycap"], x, y, 6.0))
    return children


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    function_keys = [
        _leaf(f"function_key_{index:02d}", paths["function_key"], x, 18.5, 6.0)
        for index, x in enumerate(FUNCTION_XS, start=1)
    ]
    modifier_keys = [_leaf(name, paths["modifier_key"], x, y, 6.0) for name, x, y in MODIFIER_LAYOUT]
    arrow_keys = [_leaf(name, paths["arrow_key"], x, y, 6.0) for name, x, y in ARROW_LAYOUT]
    return [
        _subassembly("keyboard_base_module", [
            _leaf("keyboard_base_tray", paths["keyboard_base"], 0.0, -1.0, 2.0),
            _leaf("rear_battery_ridge", paths["rear_battery_ridge"], 0.0, 24.0, 6.0),
        ]),
        _subassembly("keybed_module", [_leaf("keybed_panel", paths["keybed_panel"], 0.0, -6.0, 4.0)]),
        _subassembly("function_row_module", [_subassembly("function_key_module", function_keys)]),
        _subassembly("main_key_grid_module", [_subassembly("keycap_module", _main_grid(paths))]),
        _subassembly("modifier_row_module", [*modifier_keys, _leaf("spacebar_key", paths["spacebar_key"], -8.0, -28.0, 6.0)]),
        _subassembly("arrow_cluster_module", [_subassembly("arrow_key_module", arrow_keys)]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "keyboard_base": _write_component("keyboard_base", _keyboard_base()),
        "keybed_panel": _write_component("keybed_panel", _keybed_panel()),
        "rear_battery_ridge": _write_component("rear_battery_ridge", _rear_battery_ridge()),
        "keycap": _write_component("keycap", _keycap()),
        "function_key": _write_component("function_key", _function_key()),
        "modifier_key": _write_component("modifier_key", _modifier_key()),
        "spacebar_key": _write_component("spacebar_key", _spacebar_key()),
        "arrow_key": _write_component("arrow_key", _arrow_key()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_009_low_profile_keyboard_assembly.step"}
