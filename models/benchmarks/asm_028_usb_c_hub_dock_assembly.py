from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from build123d import Box, Cylinder, Pos, Rot, export_step


COMPONENT_DIR = "asm_028_usb_c_hub_dock_assembly_components"
COMPONENT_REVISION = "asm028-v3-usb-c-hub-dock"

FOOT_XY = ((-36.0, -10.0), (36.0, -10.0), (-36.0, 10.0), (36.0, 10.0))


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


def _x_cylinder(radius: float, length: float):
    return Rot(0, 90, 0) * Cylinder(radius, length)


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0]


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]]) -> dict[str, object]:
    return {"name": name, "transform": _identity_at(0.0, 0.0, 0.0), "children": children}


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    feet = [_leaf(f"hub_rubber_foot_{index}", paths["rubber_foot"], x, y, 0.6) for index, (x, y) in enumerate(FOOT_XY, start=1)]
    return [
        _subassembly("hub_body_module", [
            _leaf("aluminum_hub_main_body", paths["main_body"], 0.0, 0.0, 5.0),
            _leaf("thin_top_lid", paths["top_lid"], 0.0, 0.0, 10.1),
            _leaf("bottom_cover_plate", paths["bottom_plate"], 0.0, 0.0, 0.8),
        ]),
        _subassembly("front_port_row_module", [
            _leaf("usb_a_port_1", paths["usb_a_port"], -28.0, -16.5, 6.0),
            _leaf("usb_a_port_2", paths["usb_a_port"], -12.0, -16.5, 6.0),
            _leaf("usb_a_port_3", paths["usb_a_port"], 4.0, -16.5, 6.0),
            _leaf("usb_c_front_port", paths["usb_c_port"], 21.0, -16.5, 6.0),
            _leaf("status_led_front", paths["status_led"], 36.0, -16.0, 8.0),
        ]),
        _subassembly("rear_expansion_port_module", [
            _leaf("hdmi_port_rear", paths["hdmi_port"], -25.0, 16.5, 6.2),
            _leaf("sd_card_slot_rear", paths["sd_card_slot"], -3.0, 16.5, 6.2),
            _leaf("ethernet_port_rear", paths["ethernet_port"], 24.0, 16.5, 6.2),
        ]),
        _subassembly("usb_c_cable_module", [
            _leaf("integrated_usb_c_cable", paths["usb_c_cable"], -51.0, 0.0, 6.0),
            _leaf("usb_c_plug_connector", paths["usb_c_plug"], -62.0, 0.0, 6.0),
        ]),
        _subassembly("internal_electronics_module", [
            _leaf("controller_chip_block", paths["controller_chip"], 12.0, 0.0, 10.9),
            _leaf("memory_flash_chip_block", paths["memory_chip"], -12.0, 0.0, 10.9),
            _leaf("crystal_oscillator_block", paths["oscillator"], 0.0, 8.0, 10.9),
            _leaf("top_status_led", paths["status_led"], -36.0, 0.0, 11.2),
        ]),
        _subassembly("underside_rubber_foot_module", feet),
    ]


def gen_step():
    _limit_dependency_catalog_scan()
    paths = {
        "main_body": _write_component("main_body", Box(92.0, 30.0, 9.0)),
        "top_lid": _write_component("top_lid", Box(86.0, 26.0, 1.2)),
        "bottom_plate": _write_component("bottom_plate", Box(88.0, 28.0, 1.0)),
        "usb_a_port": _write_component("usb_a_port", Box(12.0, 3.0, 5.0)),
        "usb_c_port": _write_component("usb_c_port", Box(8.0, 3.0, 3.0)),
        "hdmi_port": _write_component("hdmi_port", Box(16.0, 3.0, 5.0)),
        "sd_card_slot": _write_component("sd_card_slot", Box(20.0, 2.5, 2.0)),
        "ethernet_port": _write_component("ethernet_port", Box(14.0, 3.5, 8.0)),
        "usb_c_cable": _write_component("usb_c_cable", _x_cylinder(2.0, 22.0)),
        "usb_c_plug": _write_component("usb_c_plug", Box(12.0, 8.0, 4.0)),
        "controller_chip": _write_component("controller_chip", Box(18.0, 12.0, 1.6)),
        "memory_chip": _write_component("memory_chip", Box(10.0, 8.0, 1.4)),
        "oscillator": _write_component("oscillator", Box(7.0, 4.0, 1.3)),
        "status_led": _write_component("status_led", Cylinder(1.5, 1.0)),
        "rubber_foot": _write_component("rubber_foot", Cylinder(3.2, 1.0)),
    }
    return {"children": _assembly_children(paths), "step_output": "asm_028_usb_c_hub_dock_assembly.step"}
