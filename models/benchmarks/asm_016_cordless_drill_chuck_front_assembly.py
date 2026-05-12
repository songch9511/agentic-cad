from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_016_cordless_drill_chuck_front_assembly_components"
COMPONENT_REVISION = "asm_016_cordless_drill_chuck_front_assembly-v2"


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


def _gearbox_nose():
    return _x_cylinder(13.0, 34.0)


def _torque_ring():
    return _x_cylinder(12.0, 9.0)


def _chuck_sleeve():
    return _x_cylinder(10.0, 28.0)


def _chuck_jaw():
    return Box(18.0, 2.8, 4.5)


def _bit_shank():
    return _x_cylinder(2.2, 38.0)


def _clutch_window():
    return Box(7.0, 2.0, 5.0)


def _case_screw():
    return _x_cylinder(1.7, 4.0)


def _front_led():
    return Box(8.0, 3.0, 4.0)


def _aux_handle_socket():
    return _y_cylinder(4.5, 14.0)


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    jaws = [
        _leaf("upper_chuck_jaw", paths["chuck_jaw"], 36.0, 0.0, 5.0),
        _leaf("lower_left_chuck_jaw", paths["chuck_jaw"], 36.0, -4.5, -2.8),
        _leaf("lower_right_chuck_jaw", paths["chuck_jaw"], 36.0, 4.5, -2.8),
    ]
    clutch_windows = [
        _leaf("torque_number_window_top", paths["clutch_window"], 8.0, 0.0, 13.0),
        _leaf("torque_number_window_left", paths["clutch_window"], 8.0, -13.0, 0.0),
        _leaf("torque_number_window_right", paths["clutch_window"], 8.0, 13.0, 0.0),
    ]
    screws = [
        _leaf("case_screw_top_left", paths["case_screw"], -18.0, -11.0, 9.0),
        _leaf("case_screw_top_right", paths["case_screw"], -18.0, 11.0, 9.0),
        _leaf("case_screw_bottom_left", paths["case_screw"], -18.0, -11.0, -7.0),
        _leaf("case_screw_bottom_right", paths["case_screw"], -18.0, 11.0, -7.0),
    ]
    return [
        _subassembly("front_gearbox_module", [
            _leaf("gearbox_nose_housing", paths["gearbox_nose"], -8.0, 0.0, 0.0),
            _leaf("aux_handle_socket_left", paths["aux_handle_socket"], -4.0, -16.0, 0.0),
            _leaf("aux_handle_socket_right", paths["aux_handle_socket"], -4.0, 16.0, 0.0),
            *screws,
        ]),
        _subassembly("torque_clutch_module", [
            _leaf("numbered_torque_ring", paths["torque_ring"], 12.0, 0.0, 0.0),
            *clutch_windows,
        ]),
        _subassembly("keyless_chuck_module", [
            _leaf("knurled_chuck_sleeve", paths["chuck_sleeve"], 31.0, 0.0, 0.0),
            *jaws,
        ]),
        _subassembly("bit_and_light_module", [
            _leaf("driver_bit_shank", paths["bit_shank"], 57.0, 0.0, 0.0),
            _leaf("front_work_led", paths["front_led"], -2.0, 0.0, -14.0),
        ]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "gearbox_nose": _write_component("gearbox_nose", _gearbox_nose()),
        "torque_ring": _write_component("torque_ring", _torque_ring()),
        "chuck_sleeve": _write_component("chuck_sleeve", _chuck_sleeve()),
        "chuck_jaw": _write_component("chuck_jaw", _chuck_jaw()),
        "bit_shank": _write_component("bit_shank", _bit_shank()),
        "clutch_window": _write_component("clutch_window", _clutch_window()),
        "case_screw": _write_component("case_screw", _case_screw()),
        "front_led": _write_component("front_led", _front_led()),
        "aux_handle_socket": _write_component("aux_handle_socket", _aux_handle_socket()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_016_cordless_drill_chuck_front_assembly.step"}
