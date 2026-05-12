from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_023_robot_wrist_joint_assembly_components"
COMPONENT_REVISION = "asm023-v1-robot-wrist"
BOLT_POINTS = ((18.0, 18.0), (-18.0, 18.0), (-18.0, -18.0), (18.0, -18.0))


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


def _x_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Rot(0, 90, 0) * Cylinder(radius, length)


def _y_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Rot(90, 0, 0) * Cylinder(radius, length)


def _z_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Cylinder(radius, length)


def _base_flange():
    pieces = [_z_cylinder(24.0, 8.0), _z_cylinder(12.0, 12.0, z=6.0)]
    for x, y in BOLT_POINTS:
        pieces.append(_z_cylinder(2.2, 4.0, x=x, y=y, z=9.0))
    return Compound(children=pieces)


def _yoke_side_plate():
    pieces = [Box(8.0, 34.0, 46.0), Pos(0.0, 0.0, 16.0) * Box(10.0, 28.0, 10.0)]
    for z in (-14.0, 14.0):
        pieces.append(_x_cylinder(5.4, 9.5, z=z))
        pieces.append(_x_cylinder(2.4, 10.0, z=z))
    return Compound(children=pieces)


def _cross_pin():
    return Compound(children=[_x_cylinder(3.0, 52.0), _x_cylinder(4.2, 5.0, x=-26.0), _x_cylinder(4.2, 5.0, x=26.0)])


def _wrist_hub():
    pieces = [_x_cylinder(14.0, 30.0), _x_cylinder(8.0, 38.0), Box(18.0, 18.0, 18.0)]
    for y in (-12.0, 12.0):
        pieces.append(_x_cylinder(2.0, 36.0, y=y))
    return Compound(children=pieces)


def _output_tool_plate():
    pieces = [Box(34.0, 34.0, 6.0), _z_cylinder(10.0, 9.0, z=4.0)]
    for x, y in BOLT_POINTS:
        pieces.append(_z_cylinder(1.8, 4.0, x=x * 0.65, y=y * 0.65, z=8.0))
    return Compound(children=pieces)


def _bearing_cap():
    return Compound(children=[_x_cylinder(9.0, 5.0), _x_cylinder(5.0, 6.0)])


def _cap_screw():
    return Compound(children=[_z_cylinder(1.3, 8.0), _z_cylinder(2.2, 1.8, z=4.9)])


def _encoder_puck():
    return Compound(children=[_y_cylinder(8.0, 5.0), Pos(0.0, 0.0, -5.0) * Box(12.0, 4.0, 8.0)])


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _fastener_children(paths: dict[str, str]) -> list[dict[str, object]]:
    children: list[dict[str, object]] = []
    for idx, (x, y) in enumerate(BOLT_POINTS, 1):
        children.append(_leaf(f"base_cap_screw_{idx}", paths["cap_screw"], x, y, 9.0))
    for idx, (x, z) in enumerate(((-28.0, -14.0), (-28.0, 14.0), (28.0, -14.0), (28.0, 14.0)), 1):
        children.append(_leaf(f"yoke_cap_screw_{idx}", paths["cap_screw"], x, -19.0, 46.0 + z))
    return children


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    return [
        _subassembly("base_flange_module", [_leaf("robot_wrist_base_flange", paths["base_flange"], 0.0, 0.0, 4.0)]),
        _subassembly("fork_yoke_module", [
            _leaf("left_yoke_side_plate", paths["yoke_side_plate"], -28.0, 0.0, 42.0),
            _leaf("right_yoke_side_plate", paths["yoke_side_plate"], 28.0, 0.0, 42.0),
            _leaf("upper_cross_pin", paths["cross_pin"], 0.0, 0.0, 56.0),
            _leaf("lower_cross_pin", paths["cross_pin"], 0.0, 0.0, 28.0),
        ]),
        _subassembly("wrist_hub_module", [
            _leaf("central_wrist_hub", paths["wrist_hub"], 0.0, 0.0, 42.0),
            _leaf("left_bearing_cap", paths["bearing_cap"], -19.0, 0.0, 42.0),
            _leaf("right_bearing_cap", paths["bearing_cap"], 19.0, 0.0, 42.0),
        ]),
        _subassembly("tool_plate_module", [_leaf("output_tool_plate", paths["output_tool_plate"], 0.0, 0.0, 75.0)]),
        _subassembly("encoder_and_fastener_module", [_leaf("rear_encoder_puck", paths["encoder_puck"], 0.0, 22.0, 42.0)] + _fastener_children(paths)),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "base_flange": _write_component("base_flange", _base_flange()),
        "yoke_side_plate": _write_component("yoke_side_plate", _yoke_side_plate()),
        "cross_pin": _write_component("cross_pin", _cross_pin()),
        "wrist_hub": _write_component("wrist_hub", _wrist_hub()),
        "output_tool_plate": _write_component("output_tool_plate", _output_tool_plate()),
        "bearing_cap": _write_component("bearing_cap", _bearing_cap()),
        "cap_screw": _write_component("cap_screw", _cap_screw()),
        "encoder_puck": _write_component("encoder_puck", _encoder_puck()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_023_robot_wrist_joint_assembly.step"}
