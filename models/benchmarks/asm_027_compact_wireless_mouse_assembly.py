from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_027_compact_wireless_mouse_assembly_components"
COMPONENT_REVISION = "asm027-v3-compact-wireless-mouse"

SKID_XY = ((-26.0, -14.5), (26.0, -14.5), (-26.0, 14.5), (26.0, 14.5))


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


def _y_cylinder(radius: float, length: float):
    return Rot(90, 0, 0) * Cylinder(radius, length)


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    skids = [_leaf(f"mouse_skid_foot_{index}", paths["skid_foot"], x, y, 0.6) for index, (x, y) in enumerate(SKID_XY, start=1)]
    return [
        _subassembly("mouse_shell_module", [
            _leaf("wireless_mouse_lower_shell", paths["lower_shell"], 0.0, 0.0, 3.0),
            _leaf("stepped_palm_shell", paths["palm_shell"], 0.0, 2.0, 9.0),
            _leaf("underside_battery_door", paths["battery_door"], 0.0, 5.0, 1.2),
        ]),
        _subassembly("button_scroll_module", [
            _leaf("left_click_button_panel", paths["button_panel"], -16.0, -12.0, 14.0),
            _leaf("right_click_button_panel", paths["button_panel"], 16.0, -12.0, 14.0),
            _leaf("center_button_spine", paths["center_button_spine"], 0.0, -12.0, 14.2),
            _leaf("ribbed_scroll_wheel", paths["scroll_wheel"], 0.0, -21.0, 14.8),
        ]),
        _subassembly("sensor_led_module", [
            _leaf("optical_sensor_window", paths["optical_sensor"], 0.0, 7.0, 1.7),
            _leaf("front_status_led", paths["status_led"], 0.0, -27.0, 14.4),
            _leaf("dpi_pairing_button", paths["dpi_button"], 0.0, -5.0, 14.5),
        ]),
        _subassembly("side_grip_module", [
            _leaf("left_rubber_side_grip", paths["side_grip"], 0.0, -22.0, 8.0),
            _leaf("right_rubber_side_grip", paths["side_grip"], 0.0, 22.0, 8.0),
        ]),
        _subassembly("underside_skid_module", skids),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "lower_shell": _write_component("lower_shell", Box(78.0, 42.0, 5.0)),
        "palm_shell": _write_component("palm_shell", Box(62.0, 34.0, 7.0)),
        "battery_door": _write_component("battery_door", Box(42.0, 24.0, 1.4)),
        "button_panel": _write_component("button_panel", Box(29.0, 18.0, 1.6)),
        "center_button_spine": _write_component("center_button_spine", Box(4.0, 21.0, 1.8)),
        "scroll_wheel": _write_component("scroll_wheel", _y_cylinder(3.0, 8.0)),
        "side_grip": _write_component("side_grip", Box(36.0, 2.5, 7.0)),
        "optical_sensor": _write_component("optical_sensor", Box(12.0, 9.0, 1.5)),
        "status_led": _write_component("status_led", Cylinder(1.5, 1.0)),
        "dpi_button": _write_component("dpi_button", Box(7.0, 3.0, 1.0)),
        "skid_foot": _write_component("skid_foot", Box(16.0, 4.0, 1.2)),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_027_compact_wireless_mouse_assembly.step"}
