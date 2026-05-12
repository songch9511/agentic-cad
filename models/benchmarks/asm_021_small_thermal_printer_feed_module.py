from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_021_small_thermal_printer_feed_module_components"
COMPONENT_REVISION = "asm_021_small_thermal_printer_feed_module-v2-lite"


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
    revision = _component_revision_path(output)
    revision.parent.mkdir(parents=True, exist_ok=True)
    revision.write_text(COMPONENT_REVISION + "\n", encoding="utf-8")
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
    return {"name": name, "path": path, "transform": _identity_at(x, y, z), "use_source_colors": False}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children, "use_source_colors": False}


def _base_frame():
    return Compound(children=[Box(68.0, 40.0, 4.0), Pos(0.0, -18.0, 2.0) * Box(58.0, 3.0, 4.0)])


def _side_plate():
    return Compound(children=[Box(4.0, 38.0, 22.0), _y_cylinder(3.2, 3.0, y=-14.0), _y_cylinder(2.5, 3.0, y=11.0, z=7.0)])


def _roller():
    return _x_cylinder(3.8, 54.0)


def _paper_roll():
    return Compound(children=[_x_cylinder(10.0, 42.0), _x_cylinder(3.0, 46.0)])


def _paper_strip():
    return Box(54.0, 26.0, 0.8)


def _printhead_bar():
    return Box(54.0, 4.0, 5.0)


def _heat_sink_fin():
    return Box(2.0, 11.0, 7.0)


def _gear_disk():
    return _y_cylinder(5.8, 3.0)


def _gear_tooth():
    return Box(4.0, 2.0, 3.0)


def _sensor_flag():
    return Box(4.5, 1.5, 7.0)


def _mount_screw():
    return _z_cylinder(1.3, 1.6)


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    return [
        _subassembly(
            "thermal_printer_chassis_module",
            [
                _leaf("printer_base_frame", paths["base_frame"], 0.0, 0.0, 2.0),
                _leaf("left_side_plate", paths["side_plate"], -34.0, 0.0, 13.0),
                _leaf("right_side_plate", paths["side_plate"], 34.0, 0.0, 13.0),
                _leaf("chassis_mount_screw_front_left", paths["mount_screw"], -26.0, 14.0, 5.0),
                _leaf("chassis_mount_screw_front_right", paths["mount_screw"], 26.0, 14.0, 5.0),
                _leaf("chassis_mount_screw_rear_left", paths["mount_screw"], -26.0, -14.0, 5.0),
                _leaf("chassis_mount_screw_rear_right", paths["mount_screw"], 26.0, -14.0, 5.0),
            ],
        ),
        _subassembly(
            "paper_feed_roller_module",
            [
                _leaf("rubber_platen_roller", paths["roller"], 0.0, -7.0, 17.0),
                _leaf("upper_pinch_roller", paths["roller"], 0.0, -14.0, 25.0),
                _leaf("receipt_paper_roll", paths["paper_roll"], 0.0, 13.0, 29.0),
                _leaf("white_paper_strip", paths["paper_strip"], 0.0, 0.0, 22.0),
            ],
        ),
        _subassembly(
            "printhead_sensor_module",
            [
                _leaf("thermal_printhead_bar", paths["printhead_bar"], 0.0, -16.0, 21.0),
                _leaf("heat_sink_fin_1", paths["heat_sink_fin"], -15.0, -10.0, 29.0),
                _leaf("heat_sink_fin_2", paths["heat_sink_fin"], 0.0, -10.0, 29.0),
                _leaf("heat_sink_fin_3", paths["heat_sink_fin"], 15.0, -10.0, 29.0),
                _leaf("left_paper_sensor_flag", paths["sensor_flag"], -18.0, -18.0, 24.0),
                _leaf("right_paper_sensor_flag", paths["sensor_flag"], 18.0, -18.0, 24.0),
            ],
        ),
        _subassembly(
            "drive_gear_train_module",
            [
                _leaf("large_drive_gear_disk", paths["gear_disk"], 41.0, -19.0, 17.0),
                _leaf("small_idler_gear_disk", paths["gear_disk"], 41.0, -19.0, 28.0),
                _leaf("gear_tooth_large_left", paths["gear_tooth"], 35.0, -21.0, 17.0),
                _leaf("gear_tooth_large_right", paths["gear_tooth"], 47.0, -21.0, 17.0),
                _leaf("gear_tooth_idler_left", paths["gear_tooth"], 36.0, -21.0, 28.0),
                _leaf("gear_tooth_idler_right", paths["gear_tooth"], 46.0, -21.0, 28.0),
            ],
        ),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "base_frame": _write_component("base_frame", _base_frame()),
        "side_plate": _write_component("side_plate", _side_plate()),
        "roller": _write_component("roller", _roller()),
        "paper_roll": _write_component("paper_roll", _paper_roll()),
        "paper_strip": _write_component("paper_strip", _paper_strip()),
        "printhead_bar": _write_component("printhead_bar", _printhead_bar()),
        "heat_sink_fin": _write_component("heat_sink_fin", _heat_sink_fin()),
        "gear_disk": _write_component("gear_disk", _gear_disk()),
        "gear_tooth": _write_component("gear_tooth", _gear_tooth()),
        "sensor_flag": _write_component("sensor_flag", _sensor_flag()),
        "mount_screw": _write_component("mount_screw", _mount_screw()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_021_small_thermal_printer_feed_module.step"}
