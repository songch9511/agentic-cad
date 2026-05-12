from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_029_compact_camera_sensor_module_assembly_components"
COMPONENT_REVISION = "asm029-v2-compact-camera-sensor-module"

MOUNT_XY = ((-19.0, -12.5), (19.0, -12.5), (-19.0, 12.5), (19.0, 12.5))


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


def _x_cylinder(radius: float, length: float):
    return Rot(0, 90, 0) * Cylinder(radius, length)


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    bosses = [_leaf(f"camera_mounting_boss_{index}", paths["mounting_boss"], x, y, 4.0) for index, (x, y) in enumerate(MOUNT_XY, start=1)]
    screws = [_leaf(f"camera_board_screw_{index}", paths["board_screw"], x, y, 6.5) for index, (x, y) in enumerate(MOUNT_XY, start=1)]
    return [
        _subassembly("camera_pcb_module", [
            _leaf("green_pcb_panel", paths["pcb_panel"], 0.0, 0.0, 1.2),
            _leaf("rear_flex_connector", paths["rear_connector"], 0.0, 20.0, 3.0),
            _leaf("folded_flex_ribbon", paths["flex_ribbon"], 0.0, 28.0, 1.0),
        ]),
        _subassembly("sensor_stack_module", [
            _leaf("image_sensor_package", paths["sensor_package"], 0.0, 0.0, 4.0),
            _leaf("image_sensor_window", paths["image_sensor_window"], 0.0, 0.0, 6.1),
        ]),
        _subassembly("lens_barrel_module", [
            _leaf("main_lens_barrel", paths["lens_barrel"], 0.0, 0.0, 11.0),
            _leaf("front_lens_ring", paths["front_lens_ring"], 0.0, 0.0, 17.5),
            _leaf("dark_aperture_disk", paths["aperture_disk"], 0.0, 0.0, 19.0),
        ]),
        _subassembly("mounting_boss_module", bosses),
        _subassembly("board_fastener_module", screws),
        _subassembly("side_spacer_module", [
            _leaf("left_side_spacer", paths["side_spacer"], -20.0, 0.0, 8.0),
            _leaf("right_side_spacer", paths["side_spacer"], 20.0, 0.0, 8.0),
        ]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "pcb_panel": _write_component("pcb_panel", Box(48.0, 34.0, 2.0)),
        "rear_connector": _write_component("rear_connector", Box(24.0, 5.0, 4.0)),
        "sensor_package": _write_component("sensor_package", Box(20.0, 16.0, 3.0)),
        "image_sensor_window": _write_component("image_sensor_window", Box(12.0, 9.0, 1.0)),
        "lens_barrel": _write_component("lens_barrel", Cylinder(8.0, 9.0)),
        "front_lens_ring": _write_component("front_lens_ring", Cylinder(10.0, 2.0)),
        "aperture_disk": _write_component("aperture_disk", Cylinder(4.0, 1.0)),
        "mounting_boss": _write_component("mounting_boss", Cylinder(2.6, 4.0)),
        "board_screw": _write_component("board_screw", Cylinder(1.4, 1.2)),
        "flex_ribbon": _write_component("flex_ribbon", Box(18.0, 12.0, 0.8)),
        "side_spacer": _write_component("side_spacer", _x_cylinder(1.4, 12.0)),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_029_compact_camera_sensor_module_assembly.step"}
