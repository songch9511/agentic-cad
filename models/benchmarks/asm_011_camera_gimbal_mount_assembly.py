from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_011_camera_gimbal_mount_assembly_components"
COMPONENT_REVISION = "asm_011_camera_gimbal_mount_assembly-v1"


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
    return Box(48.0, 34.0, 5.0)


def _mounting_boss():
    return Compound(children=[_z_cylinder(2.7, 3.0), _z_cylinder(1.3, 3.5)])


def _yaw_motor():
    return Compound(children=[_z_cylinder(10.0, 10.0), _z_cylinder(6.0, 13.0)])


def _fork_arm():
    return Compound(children=[Box(5.0, 6.0, 34.0), _x_cylinder(2.8, 6.0, z=10.0)])


def _fork_crossbar():
    return Box(36.0, 6.0, 5.0)


def _camera_block():
    return Compound(children=[Box(24.0, 18.0, 16.0), Box(18.0, 20.0, 5.0, z=6.0) if False else Box(18.0, 20.0, 5.0)])


def _lens_barrel():
    return _y_cylinder(6.0, 9.0)


def _pivot_pin():
    return _x_cylinder(2.0, 44.0)


def _side_spacer():
    return _x_cylinder(3.0, 4.0)


def _cable_guard():
    return Compound(children=[_x_cylinder(1.2, 28.0), Box(6.0, 4.0, 4.0, z=0.0) if False else Box(6.0, 4.0, 4.0)])


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    bosses = [_leaf(f"mounting_boss_{i}", paths["mounting_boss"], x, y, 6.0) for i, (x, y) in enumerate(((-17.0, -12.0), (17.0, -12.0), (-17.0, 12.0), (17.0, 12.0)), start=1)]
    return [
        _subassembly("gimbal_base_module", [_leaf("gimbal_base_plate", paths["base_plate"], 0.0, 0.0, 3.0), *bosses]),
        _subassembly("yaw_motor_module", [_leaf("yaw_motor_body", paths["yaw_motor"], 0.0, 0.0, 12.0)]),
        _subassembly("pitch_fork_module", [_leaf("left_fork_arm", paths["fork_arm"], -20.0, 0.0, 31.0), _leaf("right_fork_arm", paths["fork_arm"], 20.0, 0.0, 31.0), _leaf("fork_crossbar", paths["fork_crossbar"], 0.0, 0.0, 49.0)]),
        _subassembly("camera_block_module", [_leaf("camera_block", paths["camera_block"], 0.0, -1.0, 34.0), _leaf("camera_lens_barrel", paths["lens_barrel"], 0.0, -13.0, 34.0)]),
        _subassembly("pivot_pin_module", [_leaf("left_pivot_pin", paths["pivot_pin"], 0.0, 0.0, 34.0), _leaf("left_side_spacer", paths["side_spacer"], -24.0, 0.0, 34.0), _leaf("right_side_spacer", paths["side_spacer"], 24.0, 0.0, 34.0)]),
        _subassembly("cable_guard_module", [_leaf("rear_cable_guard", paths["cable_guard"], 0.0, 12.0, 43.0)]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "base_plate": _write_component("base_plate", _base_plate()),
        "mounting_boss": _write_component("mounting_boss", _mounting_boss()),
        "yaw_motor": _write_component("yaw_motor", _yaw_motor()),
        "fork_arm": _write_component("fork_arm", _fork_arm()),
        "fork_crossbar": _write_component("fork_crossbar", _fork_crossbar()),
        "camera_block": _write_component("camera_block", _camera_block()),
        "lens_barrel": _write_component("lens_barrel", _lens_barrel()),
        "pivot_pin": _write_component("pivot_pin", _pivot_pin()),
        "side_spacer": _write_component("side_spacer", _side_spacer()),
        "cable_guard": _write_component("cable_guard", _cable_guard()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_011_camera_gimbal_mount_assembly.step"}

