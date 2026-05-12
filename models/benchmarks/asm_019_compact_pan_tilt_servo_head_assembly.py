from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_019_compact_pan_tilt_servo_head_assembly_components"
COMPONENT_REVISION = "asm_019_compact_pan_tilt_servo_head_assembly-v2-lite"


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


def _base_plate():
    return Compound(
        children=[
            Box(42.0, 30.0, 4.0),
            _z_cylinder(2.0, 1.6, x=-15.0, y=-10.0, z=2.3),
            _z_cylinder(2.0, 1.6, x=15.0, y=-10.0, z=2.3),
            _z_cylinder(2.0, 1.6, x=-15.0, y=10.0, z=2.3),
            _z_cylinder(2.0, 1.6, x=15.0, y=10.0, z=2.3),
        ]
    )


def _servo_case():
    return Compound(children=[Box(22.0, 16.0, 16.0), _y_cylinder(3.5, 3.0, y=-9.0, z=1.5)])


def _turntable_disk():
    return Compound(children=[_z_cylinder(12.0, 3.0), _z_cylinder(6.0, 2.0, z=2.5)])


def _yoke_side():
    return Compound(children=[Box(4.0, 7.0, 30.0), _x_cylinder(2.8, 5.0, z=10.0)])


def _camera_body():
    return Compound(children=[Box(22.0, 14.0, 12.0), _y_cylinder(4.5, 4.0, y=-9.0)])


def _pivot_pin():
    return _x_cylinder(1.8, 8.0)


def _mount_screw():
    return _z_cylinder(1.3, 1.6)


def _cable_loop():
    return Compound(children=[_y_cylinder(1.6, 16.0), Box(2.0, 4.0, 5.0)])


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    return [
        _subassembly(
            "servo_base_module",
            [
                _leaf("rectangular_base_plate", paths["base_plate"], 0.0, 0.0, 2.0),
                _leaf("base_mount_screw_front_left", paths["mount_screw"], -15.0, 10.0, 5.0),
                _leaf("base_mount_screw_front_right", paths["mount_screw"], 15.0, 10.0, 5.0),
                _leaf("base_mount_screw_rear_left", paths["mount_screw"], -15.0, -10.0, 5.0),
                _leaf("base_mount_screw_rear_right", paths["mount_screw"], 15.0, -10.0, 5.0),
            ],
        ),
        _subassembly(
            "pan_servo_turntable_module",
            [
                _leaf("pan_servo_case", paths["servo_case"], 0.0, 0.0, 14.0),
                _leaf("pan_turntable_disk", paths["turntable_disk"], 0.0, 0.0, 25.0),
            ],
        ),
        _subassembly(
            "tilt_yoke_module",
            [
                _leaf("left_tilt_yoke_side", paths["yoke_side"], -18.0, 0.0, 39.0),
                _leaf("right_tilt_yoke_side", paths["yoke_side"], 18.0, 0.0, 39.0),
                _leaf("tilt_servo_case", paths["servo_case"], 0.0, 0.0, 39.0),
                _leaf("left_pivot_pin", paths["pivot_pin"], -18.0, 0.0, 49.0),
                _leaf("right_pivot_pin", paths["pivot_pin"], 18.0, 0.0, 49.0),
            ],
        ),
        _subassembly(
            "camera_cable_module",
            [
                _leaf("camera_body_with_lens", paths["camera_body"], 0.0, -2.0, 52.0),
                _leaf("rear_cable_loop", paths["cable_loop"], 0.0, 16.0, 36.0),
            ],
        ),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "base_plate": _write_component("base_plate", _base_plate()),
        "servo_case": _write_component("servo_case", _servo_case()),
        "turntable_disk": _write_component("turntable_disk", _turntable_disk()),
        "yoke_side": _write_component("yoke_side", _yoke_side()),
        "camera_body": _write_component("camera_body", _camera_body()),
        "pivot_pin": _write_component("pivot_pin", _pivot_pin()),
        "mount_screw": _write_component("mount_screw", _mount_screw()),
        "cable_loop": _write_component("cable_loop", _cable_loop()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_019_compact_pan_tilt_servo_head_assembly.step"}
