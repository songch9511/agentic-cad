from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Compound, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_020_wearable_clasp_buckle_hinge_assembly_components"
COMPONENT_REVISION = "asm_020_wearable_clasp_buckle_hinge_assembly-v2-lite"


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


def _z_cylinder(radius: float, length: float, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    return Pos(x, y, z) * Cylinder(radius, length)


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z), "use_source_colors": False}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children, "use_source_colors": False}


def _frame_rail():
    return Box(62.0, 4.0, 3.5)


def _cross_bar():
    return Box(5.0, 28.0, 3.5)


def _keeper_loop():
    return Compound(children=[Box(24.0, 4.0, 3.0), Pos(12.0, 0.0, 0.0) * Box(4.0, 20.0, 3.0)])


def _hinge_knuckle():
    return _x_cylinder(2.8, 11.0)


def _hinge_pin():
    return _x_cylinder(1.2, 62.0)


def _latch_tongue():
    return Compound(children=[Box(38.0, 7.0, 2.8), Pos(15.0, 0.0, 1.6) * Box(8.0, 5.0, 2.5)])


def _release_tab():
    return Box(13.0, 7.0, 2.5)


def _strap_anchor_plate():
    return Compound(children=[Box(22.0, 26.0, 2.4), Box(16.0, 3.0, 3.8)])


def _rivet():
    return _z_cylinder(1.8, 1.8)


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    return [
        _subassembly(
            "buckle_frame_module",
            [
                _leaf("front_frame_rail", paths["frame_rail"], 0.0, 14.0, 6.0),
                _leaf("rear_frame_rail", paths["frame_rail"], 0.0, -14.0, 6.0),
                _leaf("left_frame_cross_bar", paths["cross_bar"], -31.0, 0.0, 6.0),
                _leaf("right_frame_cross_bar", paths["cross_bar"], 31.0, 0.0, 6.0),
                _leaf("front_keeper_loop", paths["keeper_loop"], 40.0, 0.0, 7.0),
            ],
        ),
        _subassembly(
            "multi_knuckle_hinge_module",
            [
                _leaf("full_length_hinge_pin", paths["hinge_pin"], 0.0, -18.0, 9.5),
                _leaf("hinge_knuckle_left", paths["hinge_knuckle"], -22.0, -18.0, 9.5),
                _leaf("hinge_knuckle_center", paths["hinge_knuckle"], 0.0, -18.0, 9.5),
                _leaf("hinge_knuckle_right", paths["hinge_knuckle"], 22.0, -18.0, 9.5),
            ],
        ),
        _subassembly(
            "folding_clasp_latch_module",
            [
                _leaf("center_latch_tongue", paths["latch_tongue"], 0.0, 0.0, 10.5),
                _leaf("raised_release_tab", paths["release_tab"], 15.0, 3.0, 13.0),
            ],
        ),
        _subassembly(
            "strap_connector_and_rivet_module",
            [
                _leaf("left_strap_anchor_plate", paths["strap_anchor_plate"], -50.0, 0.0, 4.0),
                _leaf("right_strap_anchor_plate", paths["strap_anchor_plate"], 50.0, 0.0, 4.0),
                _leaf("rivet_front_left", paths["rivet"], -24.0, 12.0, 8.0),
                _leaf("rivet_front_right", paths["rivet"], 24.0, 12.0, 8.0),
                _leaf("rivet_rear_left", paths["rivet"], -24.0, -12.0, 8.0),
                _leaf("rivet_rear_right", paths["rivet"], 24.0, -12.0, 8.0),
            ],
        ),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "frame_rail": _write_component("frame_rail", _frame_rail()),
        "cross_bar": _write_component("cross_bar", _cross_bar()),
        "keeper_loop": _write_component("keeper_loop", _keeper_loop()),
        "hinge_knuckle": _write_component("hinge_knuckle", _hinge_knuckle()),
        "hinge_pin": _write_component("hinge_pin", _hinge_pin()),
        "latch_tongue": _write_component("latch_tongue", _latch_tongue()),
        "release_tab": _write_component("release_tab", _release_tab()),
        "strap_anchor_plate": _write_component("strap_anchor_plate", _strap_anchor_plate()),
        "rivet": _write_component("rivet", _rivet()),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_020_wearable_clasp_buckle_hinge_assembly.step"}
