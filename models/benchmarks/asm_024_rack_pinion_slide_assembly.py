from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_024_rack_pinion_slide_assembly_components"
COMPONENT_REVISION = "asm024-v1-rack-pinion-slide"
TOOTH_XS = tuple(-48.0 + 8.0 * i for i in range(13))
ROLLER_XS = (-32.0, -12.0, 12.0, 32.0)


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


def _y_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Rot(90, 0, 0) * Cylinder(radius, length)


def _z_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Cylinder(radius, length)


def _base_plate():
    pieces = [Box(118.0, 38.0, 5.0), Pos(0.0, -15.0, 4.5) * Box(112.0, 4.0, 8.0), Pos(0.0, 15.0, 4.5) * Box(112.0, 4.0, 8.0)]
    for x in (-50.0, 50.0):
        for y in (-12.0, 12.0):
            pieces.append(_z_cylinder(2.2, 2.5, x=x, y=y, z=5.0))
    return Compound(children=pieces)


def _guide_rail():
    pieces = [Box(110.0, 4.0, 8.0), Pos(0.0, 0.0, 6.0) * Box(104.0, 8.0, 4.0)]
    for x in (-42.0, -14.0, 14.0, 42.0):
        pieces.append(_z_cylinder(1.8, 3.0, x=x, z=6.0))
    return Compound(children=pieces)


def _carriage_block():
    pieces = [Box(42.0, 28.0, 11.0), Pos(0.0, 0.0, 7.0) * Box(34.0, 20.0, 5.0)]
    for x in (-14.0, 14.0):
        for y in (-9.0, 9.0):
            pieces.append(_z_cylinder(1.8, 4.0, x=x, y=y, z=9.0))
    return Compound(children=pieces)


def _rack_bar():
    return Box(104.0, 6.0, 5.0)


def _rack_tooth():
    return Box(5.0, 7.0, 4.0)


def _pinion_gear():
    pieces = [_y_cylinder(8.0, 10.0), _y_cylinder(3.0, 14.0)]
    for x, z in ((0.0, 10.0), (0.0, -10.0), (10.0, 0.0), (-10.0, 0.0), (7.0, 7.0), (-7.0, 7.0), (7.0, -7.0), (-7.0, -7.0)):
        pieces.append(Pos(x, 0.0, z) * Box(3.0, 11.0, 3.0))
    return Compound(children=pieces)


def _drive_shaft():
    return _y_cylinder(2.1, 42.0)


def _slide_roller():
    return _y_cylinder(2.6, 24.0)


def _end_stop():
    return Compound(children=[Box(6.0, 34.0, 18.0), _z_cylinder(2.0, 4.0, z=8.0)])


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    rack_teeth = [_leaf(f"rack_tooth_{idx:02d}", paths["rack_tooth"], x, 0.0, 20.0) for idx, x in enumerate(TOOTH_XS, 1)]
    rollers = []
    for idx, x in enumerate(ROLLER_XS, 1):
        rollers.append(_leaf(f"left_slide_roller_{idx}", paths["slide_roller"], x, -16.0, 17.0))
        rollers.append(_leaf(f"right_slide_roller_{idx}", paths["slide_roller"], x, 16.0, 17.0))
    return [
        _subassembly("base_and_rail_module", [_leaf("slide_base_plate", paths["base_plate"], 0.0, 0.0, 2.5), _leaf("front_guide_rail", paths["guide_rail"], 0.0, -12.0, 10.0), _leaf("rear_guide_rail", paths["guide_rail"], 0.0, 12.0, 10.0)]),
        _subassembly("moving_carriage_module", [_leaf("moving_carriage_block", paths["carriage_block"], 0.0, 0.0, 20.0)] + rollers),
        _subassembly("rack_bar_module", [_leaf("linear_rack_bar", paths["rack_bar"], 0.0, 0.0, 15.0)] + rack_teeth),
        _subassembly("pinion_drive_module", [_leaf("pinion_gear", paths["pinion_gear"], 0.0, -27.0, 26.0), _leaf("drive_shaft", paths["drive_shaft"], 0.0, -27.0, 26.0)]),
        _subassembly("end_stop_module", [_leaf("left_end_stop", paths["end_stop"], -58.0, 0.0, 14.0), _leaf("right_end_stop", paths["end_stop"], 58.0, 0.0, 14.0)]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "base_plate": _write_component("base_plate", _base_plate()),
        "guide_rail": _write_component("guide_rail", _guide_rail()),
        "carriage_block": _write_component("carriage_block", _carriage_block()),
        "rack_bar": _write_component("rack_bar", _rack_bar()),
        "rack_tooth": _write_component("rack_tooth", _rack_tooth()),
        "pinion_gear": _write_component("pinion_gear", _pinion_gear()),
        "drive_shaft": _write_component("drive_shaft", _drive_shaft()),
        "slide_roller": _write_component("slide_roller", _slide_roller()),
        "end_stop": _write_component("end_stop", _end_stop()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_024_rack_pinion_slide_assembly.step"}
