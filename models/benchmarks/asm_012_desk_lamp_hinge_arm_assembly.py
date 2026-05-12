from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_012_desk_lamp_hinge_arm_assembly_components"
COMPONENT_REVISION = "asm_012_desk_lamp_hinge_arm_assembly-v1"


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

def _lamp_base():
    return Compound(children=[_z_cylinder(18.0, 4.0), Box(20.0, 8.0, 3.0)])


def _switch_button():
    return Box(6.0, 4.0, 2.5)


def _vertical_link_bar():
    return Box(5.0, 3.0, 32.0)


def _horizontal_link_bar():
    return Box(32.0, 3.0, 5.0)


def _hinge_pin():
    return _y_cylinder(2.2, 38.0)


def _hinge_knob():
    return _y_cylinder(4.0, 4.0)


def _lamp_shade():
    return Compound(children=[Box(28.0, 22.0, 12.0), _x_cylinder(5.5, 29.0, z=-2.0)])


def _light_diffuser():
    return Box(24.0, 18.0, 2.0)


def _cable_tube():
    return _x_cylinder(1.0, 38.0)


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    return [
        _subassembly("lamp_base_module", [_leaf("lamp_base_disc", paths["lamp_base"], 0.0, 0.0, 3.0), _leaf("switch_button", paths["switch_button"], -6.0, -10.0, 6.0)]),
        _subassembly("lower_arm_module", [_leaf("left_lower_link_bar", paths["vertical_link_bar"], -12.0, -14.0, 25.0), _leaf("right_lower_link_bar", paths["vertical_link_bar"], -12.0, 14.0, 25.0)]),
        _subassembly("upper_arm_module", [_leaf("left_upper_link_bar", paths["horizontal_link_bar"], 12.0, -14.0, 48.0), _leaf("right_upper_link_bar", paths["horizontal_link_bar"], 12.0, 14.0, 48.0), _leaf("visible_cable_tube", paths["cable_tube"], 11.0, 0.0, 43.0)]),
        _subassembly("hinge_joint_module", [_leaf("base_hinge_pin", paths["hinge_pin"], -12.0, 0.0, 10.0), _leaf("elbow_hinge_pin", paths["hinge_pin"], -12.0, 0.0, 41.0), _leaf("shade_hinge_pin", paths["hinge_pin"], 33.0, 0.0, 48.0), _leaf("base_hinge_knob", paths["hinge_knob"], -12.0, -21.0, 10.0), _leaf("elbow_hinge_knob", paths["hinge_knob"], -12.0, -21.0, 41.0), _leaf("shade_hinge_knob", paths["hinge_knob"], 33.0, -21.0, 48.0)]),
        _subassembly("lamp_head_module", [_leaf("lamp_shade", paths["lamp_shade"], 45.0, 0.0, 48.0), _leaf("lamp_light_diffuser", paths["light_diffuser"], 45.0, 0.0, 40.5)]),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "lamp_base": _write_component("lamp_base", _lamp_base()),
        "switch_button": _write_component("switch_button", _switch_button()),
        "vertical_link_bar": _write_component("vertical_link_bar", _vertical_link_bar()),
        "horizontal_link_bar": _write_component("horizontal_link_bar", _horizontal_link_bar()),
        "hinge_pin": _write_component("hinge_pin", _hinge_pin()),
        "hinge_knob": _write_component("hinge_knob", _hinge_knob()),
        "lamp_shade": _write_component("lamp_shade", _lamp_shade()),
        "light_diffuser": _write_component("light_diffuser", _light_diffuser()),
        "cable_tube": _write_component("cable_tube", _cable_tube()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_012_desk_lamp_hinge_arm_assembly.step"}

