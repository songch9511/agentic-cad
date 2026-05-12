from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_018_mini_drone_motor_arm_assembly_components"
COMPONENT_REVISION = "asm_018_mini_drone_motor_arm_assembly-v2-lite"


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


def _z_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Cylinder(radius, length)


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z), "use_source_colors": False}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children, "use_source_colors": False}


def _hub_core():
    return Compound(
        children=[
            Box(22.0, 22.0, 4.0),
            _z_cylinder(2.2, 2.0, x=-7.0, y=-7.0, z=2.4),
            _z_cylinder(2.2, 2.0, x=7.0, y=-7.0, z=2.4),
            _z_cylinder(2.2, 2.0, x=-7.0, y=7.0, z=2.4),
            _z_cylinder(2.2, 2.0, x=7.0, y=7.0, z=2.4),
        ]
    )


def _battery_pack():
    return Box(18.0, 11.0, 5.0)


def _arm_x():
    return Compound(children=[Box(34.0, 5.0, 3.0), _z_cylinder(2.0, 1.5, x=14.0, z=1.8)])


def _arm_y():
    return Compound(children=[Box(5.0, 34.0, 3.0), _z_cylinder(2.0, 1.5, y=14.0, z=1.8)])


def _motor_can():
    return Compound(children=[_z_cylinder(5.0, 6.0), _z_cylinder(1.8, 2.0, z=4.0)])


def _prop_blade_x():
    return Compound(children=[Box(22.0, 3.0, 0.8), Box(6.0, 5.0, 1.0)])


def _prop_blade_y():
    return Compound(children=[Box(3.0, 22.0, 0.8), Box(5.0, 6.0, 1.0)])


def _landing_leg():
    return Compound(children=[Box(3.0, 3.0, 11.0), Pos(0.0, 0.0, -6.2) * Box(12.0, 3.0, 1.8)])


def _arm_screw():
    return _z_cylinder(1.4, 1.4)


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    motor_centers = [(45.0, 0.0), (-45.0, 0.0), (0.0, 45.0), (0.0, -45.0)]
    return [
        _subassembly(
            "drone_center_hub_module",
            [
                _leaf("center_hub_core", paths["hub_core"], 0.0, 0.0, 10.0),
                _leaf("underslung_battery_pack", paths["battery_pack"], 0.0, 0.0, 5.0),
            ],
        ),
        _subassembly(
            "cross_motor_arm_module",
            [
                _leaf("right_motor_arm", paths["arm_x"], 25.0, 0.0, 11.0),
                _leaf("left_motor_arm", paths["arm_x"], -25.0, 0.0, 11.0),
                _leaf("front_motor_arm", paths["arm_y"], 0.0, 25.0, 11.0),
                _leaf("rear_motor_arm", paths["arm_y"], 0.0, -25.0, 11.0),
            ],
        ),
        _subassembly(
            "four_motor_propeller_module",
            [
                _leaf("brushless_motor_can_right", paths["motor_can"], 45.0, 0.0, 15.0),
                _leaf("brushless_motor_can_left", paths["motor_can"], -45.0, 0.0, 15.0),
                _leaf("brushless_motor_can_front", paths["motor_can"], 0.0, 45.0, 15.0),
                _leaf("brushless_motor_can_rear", paths["motor_can"], 0.0, -45.0, 15.0),
                _leaf("prop_blade_x_right", paths["prop_blade_x"], 45.0, 0.0, 21.0),
                _leaf("prop_blade_x_left", paths["prop_blade_x"], -45.0, 0.0, 21.0),
                _leaf("prop_blade_y_front", paths["prop_blade_y"], 0.0, 45.0, 21.0),
                _leaf("prop_blade_y_rear", paths["prop_blade_y"], 0.0, -45.0, 21.0),
            ],
        ),
        _subassembly(
            "landing_gear_module",
            [
                _leaf("front_right_landing_leg", paths["landing_leg"], 22.0, 22.0, 5.0),
                _leaf("front_left_landing_leg", paths["landing_leg"], -22.0, 22.0, 5.0),
                _leaf("rear_right_landing_leg", paths["landing_leg"], 22.0, -22.0, 5.0),
                _leaf("rear_left_landing_leg", paths["landing_leg"], -22.0, -22.0, 5.0),
            ],
        ),
        _subassembly(
            "arm_fastener_module",
            [
                _leaf("arm_screw_right", paths["arm_screw"], 14.0, 0.0, 14.0),
                _leaf("arm_screw_left", paths["arm_screw"], -14.0, 0.0, 14.0),
                _leaf("arm_screw_front", paths["arm_screw"], 0.0, 14.0, 14.0),
                _leaf("arm_screw_rear", paths["arm_screw"], 0.0, -14.0, 14.0),
            ],
        ),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "hub_core": _write_component("hub_core", _hub_core()),
        "battery_pack": _write_component("battery_pack", _battery_pack()),
        "arm_x": _write_component("arm_x", _arm_x()),
        "arm_y": _write_component("arm_y", _arm_y()),
        "motor_can": _write_component("motor_can", _motor_can()),
        "prop_blade_x": _write_component("prop_blade_x", _prop_blade_x()),
        "prop_blade_y": _write_component("prop_blade_y", _prop_blade_y()),
        "landing_leg": _write_component("landing_leg", _landing_leg()),
        "arm_screw": _write_component("arm_screw", _arm_screw()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_018_mini_drone_motor_arm_assembly.step"}
