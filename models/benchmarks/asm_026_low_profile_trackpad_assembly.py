from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_026_low_profile_trackpad_assembly_components"
COMPONENT_REVISION = "asm026-v2-low-profile-trackpad"

FASTENER_XY = ((-46.0, -28.0), (46.0, -28.0), (-46.0, 28.0), (46.0, 28.0))
FOOT_XY = ((-42.0, -25.0), (42.0, -25.0), (-42.0, 25.0), (42.0, 25.0))


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


def _x_cylinder(radius: float, length: float):
    return Rot(0, 90, 0) * Cylinder(radius, length)


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    fasteners = [_leaf(f"trackpad_screw_post_{index}", paths["screw_post"], x, y, 3.0) for index, (x, y) in enumerate(FASTENER_XY, start=1)]
    feet = [_leaf(f"trackpad_rubber_foot_{index}", paths["rubber_foot"], x, y, 0.6) for index, (x, y) in enumerate(FOOT_XY, start=1)]
    return [
        _subassembly("trackpad_chassis_module", [
            _leaf("trackpad_base_chassis", paths["base_chassis"], 0.0, 0.0, 1.5),
            _leaf("left_side_rail", paths["side_rail"], -54.5, 0.0, 3.4),
            _leaf("right_side_rail", paths["side_rail"], 54.5, 0.0, 3.4),
        ]),
        _subassembly("touch_sensor_surface_module", [
            _leaf("glass_touch_surface_panel", paths["touch_surface_panel"], 0.0, 1.5, 4.2),
            _leaf("front_click_zone_strip", paths["front_click_strip"], 0.0, -30.0, 4.8),
            _leaf("rear_capacitive_sensor_bar", paths["sensor_bar"], 0.0, 28.0, 4.7),
        ]),
        _subassembly("haptic_click_module", [
            _leaf("linear_haptic_actuator", paths["haptic_actuator"], 0.0, -8.0, 2.8),
            _leaf("left_click_beam", paths["click_beam"], -24.0, -25.0, 3.2),
            _leaf("right_click_beam", paths["click_beam"], 24.0, -25.0, 3.2),
        ]),
        _subassembly("trackpad_fastener_module", fasteners),
        _subassembly("underside_rubber_foot_module", feet),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "base_chassis": _write_component("base_chassis", Box(112.0, 72.0, 3.0)),
        "touch_surface_panel": _write_component("touch_surface_panel", Box(102.0, 62.0, 1.0)),
        "side_rail": _write_component("side_rail", Box(3.0, 68.0, 2.0)),
        "front_click_strip": _write_component("front_click_strip", Box(92.0, 5.0, 1.1)),
        "sensor_bar": _write_component("sensor_bar", Box(84.0, 3.0, 1.0)),
        "haptic_actuator": _write_component("haptic_actuator", _x_cylinder(2.0, 26.0)),
        "click_beam": _write_component("click_beam", Box(34.0, 3.0, 2.0)),
        "screw_post": _write_component("screw_post", Cylinder(2.1, 4.0)),
        "rubber_foot": _write_component("rubber_foot", Cylinder(3.2, 1.0)),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_026_low_profile_trackpad_assembly.step"}
