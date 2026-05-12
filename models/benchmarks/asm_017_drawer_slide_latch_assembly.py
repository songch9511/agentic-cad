from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_017_drawer_slide_latch_assembly_components"
COMPONENT_REVISION = "asm_017_drawer_slide_latch_assembly-v2"


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


def _cabinet_rail():
    return Box(84.0, 5.0, 9.0)


def _drawer_rail():
    return Box(76.0, 4.0, 7.0)


def _center_slide():
    return Box(66.0, 3.0, 5.0)


def _roller_wheel():
    return _y_cylinder(3.2, 3.0)


def _ball_bearing():
    return _z_cylinder(1.6, 2.0)


def _latch_hook():
    return Box(12.0, 4.0, 9.0)


def _release_tab():
    return Box(18.0, 3.0, 5.0)


def _mount_screw():
    return _z_cylinder(1.8, 3.0)


def _stop_bumper():
    return Box(6.0, 6.0, 6.0)


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    rail_screws = [
        _leaf("cabinet_screw_left_front", paths["mount_screw"], -34.0, -5.0, 7.0),
        _leaf("cabinet_screw_left_rear", paths["mount_screw"], 34.0, -5.0, 7.0),
        _leaf("drawer_screw_right_front", paths["mount_screw"], -30.0, 5.0, -4.0),
        _leaf("drawer_screw_right_rear", paths["mount_screw"], 30.0, 5.0, -4.0),
    ]
    rollers = [
        _leaf("front_upper_roller_wheel", paths["roller_wheel"], -28.0, 0.0, 7.0),
        _leaf("rear_upper_roller_wheel", paths["roller_wheel"], 28.0, 0.0, 7.0),
        _leaf("front_lower_roller_wheel", paths["roller_wheel"], -18.0, 0.0, -6.0),
        _leaf("rear_lower_roller_wheel", paths["roller_wheel"], 18.0, 0.0, -6.0),
    ]
    balls = [
        _leaf("bearing_ball_01", paths["ball_bearing"], -24.0, -2.8, 1.0),
        _leaf("bearing_ball_02", paths["ball_bearing"], -12.0, -2.8, 1.0),
        _leaf("bearing_ball_03", paths["ball_bearing"], 0.0, -2.8, 1.0),
        _leaf("bearing_ball_04", paths["ball_bearing"], 12.0, -2.8, 1.0),
        _leaf("bearing_ball_05", paths["ball_bearing"], 24.0, -2.8, 1.0),
        _leaf("bearing_ball_06", paths["ball_bearing"], 36.0, -2.8, 1.0),
    ]
    return [
        _subassembly("outer_cabinet_rail_module", [
            _leaf("fixed_cabinet_rail", paths["cabinet_rail"], 0.0, -5.0, 2.0),
            *rail_screws[:2],
        ]),
        _subassembly("inner_drawer_rail_module", [
            _leaf("moving_drawer_rail", paths["drawer_rail"], 5.0, 5.0, -2.0),
            *rail_screws[2:],
        ]),
        _subassembly("ball_cage_and_rollers_module", [
            _leaf("center_slide_cage", paths["center_slide"], 4.0, 0.0, 1.0),
            *rollers,
            *balls,
        ]),
        _subassembly("latch_release_module", [
            _leaf("front_latch_hook", paths["latch_hook"], 44.0, 2.0, 5.0),
            _leaf("release_pull_tab", paths["release_tab"], 34.0, 8.0, 9.0),
            _leaf("front_stop_bumper", paths["stop_bumper"], 43.0, -5.0, 2.0),
            _leaf("rear_stop_bumper", paths["stop_bumper"], -43.0, -5.0, 2.0),
        ]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "cabinet_rail": _write_component("cabinet_rail", _cabinet_rail()),
        "drawer_rail": _write_component("drawer_rail", _drawer_rail()),
        "center_slide": _write_component("center_slide", _center_slide()),
        "roller_wheel": _write_component("roller_wheel", _roller_wheel()),
        "ball_bearing": _write_component("ball_bearing", _ball_bearing()),
        "latch_hook": _write_component("latch_hook", _latch_hook()),
        "release_tab": _write_component("release_tab", _release_tab()),
        "mount_screw": _write_component("mount_screw", _mount_screw()),
        "stop_bumper": _write_component("stop_bumper", _stop_bumper()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_017_drawer_slide_latch_assembly.step"}
