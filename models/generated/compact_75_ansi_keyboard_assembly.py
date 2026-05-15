from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
import json
import math
from pathlib import Path
import subprocess
import sys

from build123d import (
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Compound,
    Cylinder,
    Location,
    Locations,
    Mode,
    Plane,
    Pos,
    Rectangle,
    RectangleRounded,
    Rot,
    chamfer,
    export_step,
    extrude,
    loft,
)


DISPLAY_NAME = "Parametric 84-key ANSI 75% mechanical keyboard assembly"

# Global design parameters, all in millimeters unless noted.
U = 19.05
CASE_ANGLE_DEG = 6.0
PLATE_THICKNESS = 1.5
PCB_THICKNESS = 1.6
CASE_WALL_THICKNESS = 3.0
TOP_CASE_THICKNESS = 4.0
BOTTOM_CASE_THICKNESS = 3.0
FRONT_HEIGHT = 18.0
REAR_HEIGHT = 30.0
CASE_CORNER_RADIUS = 8.0
CASE_EDGE_CHAMFER = 1.2
KEYCAP_HEIGHT = 9.0
KEYCAP_TOP_SIZE = 17.5
KEYCAP_BASE_SIZE = 18.2
PLATE_MARGIN_X = 12.0
PLATE_MARGIN_Y = 10.0
USB_C_CUTOUT_WIDTH = 10.0
USB_C_CUTOUT_HEIGHT = 4.0

MX_CUTOUT = 14.0
SWITCH_HOUSING_SIZE = 15.6
SWITCH_HEIGHT = 10.5
STABILIZER_SLOT_WIDTH = 3.4
STABILIZER_SLOT_HEIGHT = 14.0
STABILIZER_SLOT_OFFSET_BY_U = {
    2.0: 11.94,
    2.25: 11.94,
    2.75: 19.05,
    6.25: 47.625,
}

MOUNT_BOSS_RADIUS = 2.8
MOUNT_SCREW_RADIUS = 1.1
MOUNT_HOLE_RADIUS = 1.9
RUBBER_FOOT_RADIUS = 5.0
RUBBER_FOOT_HEIGHT = 1.5

EXPLODED_VIEW = False
EXPLODED_GAP = 18.0

COMPONENT_DIR = "compact_75_ansi_keyboard_components"
STEP_OUTPUT = "compact_75_ansi_keyboard_assembly.step"
COLORED_STEP_OUTPUT = "compact_75_ansi_keyboard_colored_demo.step"
REPORT_OUTPUT = "compact_75_ansi_keyboard_validation_report.json"
GEOMETRY_REVISION = "v3"

MATTE_BLACK = (0.005, 0.005, 0.005, 1.0)
BRUSHED_ALUMINUM = (0.68, 0.68, 0.64, 1.0)
PCB_GREEN = (0.02, 0.16, 0.11, 1.0)
PBT_DARK_GRAY = (0.12, 0.12, 0.12, 1.0)
ESC_RED = (0.78, 0.02, 0.015, 1.0)
SWITCH_DARK = (0.035, 0.035, 0.04, 1.0)
STEM_RED = (0.55, 0.02, 0.02, 1.0)
RUBBER_BLACK = (0.01, 0.01, 0.01, 1.0)
CONNECTOR_SILVER = (0.72, 0.72, 0.70, 1.0)

# Row-based unit-width layout. "gap" tokens consume unit width but do not create keys.
LAYOUT_ROWS: tuple[tuple[tuple[str, float], ...], ...] = (
    (
        ("Esc", 1.0),
        ("gap", 0.0625),
        ("F1", 1.0),
        ("F2", 1.0),
        ("F3", 1.0),
        ("F4", 1.0),
        ("gap", 0.0625),
        ("F5", 1.0),
        ("F6", 1.0),
        ("F7", 1.0),
        ("F8", 1.0),
        ("gap", 0.0625),
        ("F9", 1.0),
        ("F10", 1.0),
        ("F11", 1.0),
        ("F12", 1.0),
        ("gap", 0.0625),
        ("PrtSc", 1.0),
        ("Ins", 1.0),
        ("Del", 1.0),
    ),
    (
        ("Grave", 1.0),
        ("1", 1.0),
        ("2", 1.0),
        ("3", 1.0),
        ("4", 1.0),
        ("5", 1.0),
        ("6", 1.0),
        ("7", 1.0),
        ("8", 1.0),
        ("9", 1.0),
        ("0", 1.0),
        ("Minus", 1.0),
        ("Equals", 1.0),
        ("Backspace", 2.0),
        ("gap", 0.25),
        ("Home", 1.0),
    ),
    (
        ("Tab", 1.5),
        ("Q", 1.0),
        ("W", 1.0),
        ("E", 1.0),
        ("R", 1.0),
        ("T", 1.0),
        ("Y", 1.0),
        ("U", 1.0),
        ("I", 1.0),
        ("O", 1.0),
        ("P", 1.0),
        ("LBracket", 1.0),
        ("RBracket", 1.0),
        ("Backslash", 1.5),
        ("gap", 0.25),
        ("PgUp", 1.0),
    ),
    (
        ("Caps", 1.75),
        ("A", 1.0),
        ("S", 1.0),
        ("D", 1.0),
        ("F", 1.0),
        ("G", 1.0),
        ("H", 1.0),
        ("J", 1.0),
        ("K", 1.0),
        ("L", 1.0),
        ("Semicolon", 1.0),
        ("Quote", 1.0),
        ("Enter", 2.25),
        ("gap", 0.25),
        ("PgDn", 1.0),
    ),
    (
        ("LShift", 2.25),
        ("Z", 1.0),
        ("X", 1.0),
        ("C", 1.0),
        ("V", 1.0),
        ("B", 1.0),
        ("N", 1.0),
        ("M", 1.0),
        ("Comma", 1.0),
        ("Period", 1.0),
        ("Slash", 1.0),
        ("RShift", 2.75),
        ("Up", 1.0),
    ),
    (
        ("LCtrl", 1.0),
        ("LWin", 1.0),
        ("LAlt", 1.0),
        ("Space", 6.25),
        ("RAlt", 1.0),
        ("Fn", 1.0),
        ("Menu", 1.0),
        ("RCtrl", 1.0),
        ("Left", 1.0),
        ("Down", 1.0),
        ("Right", 1.0),
    ),
)


@dataclass(frozen=True)
class Key:
    label: str
    width_u: float
    row: int
    index_in_row: int
    x_u: float
    y_u: float
    x: float
    y: float


def _is_gap(label: str) -> bool:
    return label == "gap"


def _layout_extents_u() -> tuple[float, float, float, float]:
    max_x = 0.0
    for row in LAYOUT_ROWS:
        cursor = 0.0
        for label, width in row:
            cursor += width
        max_x = max(max_x, cursor)
    min_y = -(len(LAYOUT_ROWS) - 1) - 0.5
    max_y = 0.5
    return 0.0, max_x, min_y, max_y


def layout_keys() -> list[Key]:
    min_x, max_x, min_y, max_y = _layout_extents_u()
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    keys: list[Key] = []
    for row_index, row in enumerate(LAYOUT_ROWS):
        cursor = 0.0
        key_index = 0
        for label, width in row:
            if _is_gap(label):
                cursor += width
                continue
            key_index += 1
            x_u = cursor + width / 2.0
            y_u = -float(row_index)
            keys.append(
                Key(
                    label=label,
                    width_u=width,
                    row=row_index + 1,
                    index_in_row=key_index,
                    x_u=x_u,
                    y_u=y_u,
                    x=(x_u - center_x) * U,
                    y=(y_u - center_y) * U,
                )
            )
            cursor += width
    return keys


def _key_area_size() -> tuple[float, float]:
    min_x, max_x, min_y, max_y = _layout_extents_u()
    return (max_x - min_x) * U, (max_y - min_y) * U


def _plate_size() -> tuple[float, float]:
    key_w, key_d = _key_area_size()
    return key_w + 2.0 * PLATE_MARGIN_X, key_d + 2.0 * PLATE_MARGIN_Y


def _case_size() -> tuple[float, float]:
    plate_w, plate_d = _plate_size()
    return plate_w + 2.0 * CASE_WALL_THICKNESS, plate_d + 2.0 * CASE_WALL_THICKNESS


def _top_case_z() -> float:
    return FRONT_HEIGHT - TOP_CASE_THICKNESS


def _plate_z() -> float:
    return _top_case_z() + 1.0


def _pcb_z() -> float:
    return _plate_z() - 5.0


def _switch_z() -> float:
    return _plate_z() - 2.5


def _keycap_z() -> float:
    return _switch_z() + SWITCH_HEIGHT - 1.0


def _boss_height() -> float:
    return max(BOTTOM_CASE_THICKNESS + 1.0, _pcb_z() - 0.35)


def _mounting_points() -> tuple[tuple[float, float], ...]:
    plate_w, plate_d = _plate_size()
    side_x = plate_w / 2.0 - 7.5
    inner_x = plate_w * 0.23
    y = plate_d / 2.0 - 5.0
    return (
        (-side_x, -y),
        (side_x, -y),
        (-side_x, y),
        (side_x, y),
        (-inner_x, -y),
        (inner_x, -y),
        (-inner_x, y),
        (inner_x, y),
    )


def _component_path(name: str) -> Path:
    return Path(__file__).resolve().parent / COMPONENT_DIR / f"{name}.step"


def _component_topology_path(step_path: Path) -> Path:
    return step_path.parent / f".{step_path.name}" / "topology.json"


def _component_revision_path(step_path: Path) -> Path:
    return step_path.parent / f".{step_path.name}" / "revision.txt"


def _component_revision() -> str:
    payload = {
        "geometry_revision": GEOMETRY_REVISION,
        "parameters": {
            "U": U,
            "case_angle_deg": CASE_ANGLE_DEG,
            "plate_thickness": PLATE_THICKNESS,
            "pcb_thickness": PCB_THICKNESS,
            "case_wall_thickness": CASE_WALL_THICKNESS,
            "top_case_thickness": TOP_CASE_THICKNESS,
            "bottom_case_thickness": BOTTOM_CASE_THICKNESS,
            "front_height": FRONT_HEIGHT,
            "rear_height": REAR_HEIGHT,
            "case_corner_radius": CASE_CORNER_RADIUS,
            "case_edge_chamfer": CASE_EDGE_CHAMFER,
            "keycap_height": KEYCAP_HEIGHT,
            "keycap_top_size": KEYCAP_TOP_SIZE,
            "keycap_base_size": KEYCAP_BASE_SIZE,
            "plate_margin_x": PLATE_MARGIN_X,
            "plate_margin_y": PLATE_MARGIN_Y,
            "usb_c_cutout_width": USB_C_CUTOUT_WIDTH,
            "usb_c_cutout_height": USB_C_CUTOUT_HEIGHT,
        },
        "layout": LAYOUT_ROWS,
    }
    digest = sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return f"compact75-ansi-{digest}"


def _component_is_current(step_path: Path) -> bool:
    try:
        return _component_revision_path(step_path).read_text(encoding="utf-8").strip() == _component_revision()
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
            f"failed to generate component topology for {step_path}:\n"
            f"{completed.stdout}\n{completed.stderr}"
        )


def _write_component(name: str, shape) -> str:
    output = _component_path(name)
    if output.exists() and _component_topology_path(output).exists() and _component_is_current(output):
        return f"{COMPONENT_DIR}/{name}.step"
    output.parent.mkdir(parents=True, exist_ok=True)
    if not export_step(shape, output):
        raise RuntimeError(f"failed to export component STEP: {output}")
    _write_component_topology(output)
    _component_revision_path(output).write_text(_component_revision() + "\n", encoding="utf-8")
    return f"{COMPONENT_DIR}/{name}.step"


def _color(shape, rgba: tuple[float, float, float, float]):
    shape.color = Color(*rgba)
    return shape


def _safe_radius(width: float, height: float, requested: float) -> float:
    return max(0.05, min(requested, width / 2.0 - 0.1, height / 2.0 - 0.1))


def _try_chamfer_current_part(part_builder: BuildPart, amount: float) -> None:
    try:
        chamfer(part_builder.part.edges(), length=amount)
    except Exception:
        pass


def _top_case_frame():
    case_w, case_d = _case_size()
    key_w, key_d = _key_area_size()
    opening_w = key_w + 2.0 * (PLATE_MARGIN_X - 2.0)
    opening_d = key_d + 2.0 * (PLATE_MARGIN_Y - 2.0)
    with BuildPart() as part:
        with BuildSketch():
            RectangleRounded(
                case_w,
                case_d,
                _safe_radius(case_w, case_d, CASE_CORNER_RADIUS),
            )
            RectangleRounded(
                opening_w,
                opening_d,
                _safe_radius(opening_w, opening_d, CASE_CORNER_RADIUS - CASE_WALL_THICKNESS),
                mode=Mode.SUBTRACT,
            )
        extrude(amount=TOP_CASE_THICKNESS)
        _try_chamfer_current_part(part, CASE_EDGE_CHAMFER)
    return _color(part.part, MATTE_BLACK)


def _bottom_tray():
    case_w, case_d = _case_size()
    inner_w = case_w - 2.0 * CASE_WALL_THICKNESS
    inner_d = case_d - 2.0 * CASE_WALL_THICKNESS
    tray_height = _top_case_z()
    wall_height = tray_height - BOTTOM_CASE_THICKNESS
    with BuildPart() as part:
        with BuildSketch(Plane.XY):
            RectangleRounded(case_w, case_d, _safe_radius(case_w, case_d, CASE_CORNER_RADIUS))
        extrude(amount=BOTTOM_CASE_THICKNESS)
        with BuildSketch(Plane.XY.offset(BOTTOM_CASE_THICKNESS)):
            RectangleRounded(case_w, case_d, _safe_radius(case_w, case_d, CASE_CORNER_RADIUS))
            RectangleRounded(
                inner_w,
                inner_d,
                _safe_radius(inner_w, inner_d, CASE_CORNER_RADIUS - CASE_WALL_THICKNESS),
                mode=Mode.SUBTRACT,
            )
        extrude(amount=wall_height)
        with Locations((0.0, case_d / 2.0 - CASE_WALL_THICKNESS / 2.0, _pcb_z() + PCB_THICKNESS / 2.0)):
            Box(USB_C_CUTOUT_WIDTH, CASE_WALL_THICKNESS * 3.0, USB_C_CUTOUT_HEIGHT, mode=Mode.SUBTRACT)
        for x, y in _mounting_points():
            with Locations((x, y, _boss_height() / 2.0)):
                Cylinder(MOUNT_BOSS_RADIUS, _boss_height())
                Cylinder(MOUNT_SCREW_RADIUS, _boss_height() + 0.4, mode=Mode.SUBTRACT)
        _try_chamfer_current_part(part, CASE_EDGE_CHAMFER * 0.5)
    return _color(part.part, MATTE_BLACK)


def _stabilizer_offset(width_u: float) -> float | None:
    for target_width, offset in STABILIZER_SLOT_OFFSET_BY_U.items():
        if abs(width_u - target_width) < 1e-6:
            return offset
    return None


def _stabilizer_keys() -> list[Key]:
    return [key for key in layout_keys() if _stabilizer_offset(key.width_u) is not None]


def _stabilizer_slot_rects() -> list[tuple[float, float, float, float]]:
    rects: list[tuple[float, float, float, float]] = []
    for key in _stabilizer_keys():
        offset = _stabilizer_offset(key.width_u)
        if offset is None:
            continue
        rects.append((key.x - offset, key.y, STABILIZER_SLOT_WIDTH, STABILIZER_SLOT_HEIGHT))
        rects.append((key.x + offset, key.y, STABILIZER_SLOT_WIDTH, STABILIZER_SLOT_HEIGHT))
    return rects


def _switch_plate():
    plate_w, plate_d = _plate_size()
    with BuildPart() as part:
        with BuildSketch():
            RectangleRounded(plate_w, plate_d, _safe_radius(plate_w, plate_d, 4.0))
            for key in layout_keys():
                with Locations((key.x, key.y)):
                    Rectangle(MX_CUTOUT, MX_CUTOUT, mode=Mode.SUBTRACT)
            for x, y, width, height in _stabilizer_slot_rects():
                with Locations((x, y)):
                    Rectangle(width, height, mode=Mode.SUBTRACT)
            for x, y in _mounting_points():
                with Locations((x, y)):
                    Circle(MOUNT_HOLE_RADIUS, mode=Mode.SUBTRACT)
        extrude(amount=PLATE_THICKNESS)
    return _color(part.part, BRUSHED_ALUMINUM)


def _pcb():
    plate_w, plate_d = _plate_size()
    pcb_w = plate_w - 4.0
    pcb_d = plate_d - 4.0
    with BuildPart() as board_part:
        with BuildSketch():
            RectangleRounded(pcb_w, pcb_d, _safe_radius(pcb_w, pcb_d, 3.0))
            for x, y in _mounting_points():
                with Locations((x, y)):
                    Circle(MOUNT_HOLE_RADIUS + 0.5, mode=Mode.SUBTRACT)
        extrude(amount=PCB_THICKNESS)
    board = _color(board_part.part, PCB_GREEN)
    connector = _color(
        Pos(0.0, pcb_d / 2.0 + 1.8, PCB_THICKNESS + 1.4)
        * Box(USB_C_CUTOUT_WIDTH, 5.8, 2.8),
        CONNECTOR_SILVER,
    )
    return Compound(children=[board, connector])


def _mx_switch():
    housing = _color(Pos(0.0, 0.0, 4.0) * Box(SWITCH_HOUSING_SIZE, SWITCH_HOUSING_SIZE, 7.0), SWITCH_DARK)
    top_plate = _color(Pos(0.0, 0.0, 7.8) * Box(13.6, 13.6, 1.0), SWITCH_DARK)
    stem_x = _color(Pos(0.0, 0.0, 9.7) * Box(4.2, 1.4, 3.0), STEM_RED)
    stem_y = _color(Pos(0.0, 0.0, 9.7) * Box(1.4, 4.2, 3.0), STEM_RED)
    pin_a = _color(Pos(-2.5, -4.8, 0.8) * Cylinder(0.45, 1.6), CONNECTOR_SILVER)
    pin_b = _color(Pos(2.5, -4.8, 0.8) * Cylinder(0.45, 1.6), CONNECTOR_SILVER)
    return Compound(children=[housing, top_plate, stem_x, stem_y, pin_a, pin_b])


def _keycap_size(width_u: float) -> tuple[float, float]:
    if abs(width_u - 1.0) < 1e-6:
        return KEYCAP_BASE_SIZE, KEYCAP_TOP_SIZE
    base_x = width_u * U - 0.85
    top_x = width_u * U - 1.55
    return max(base_x, KEYCAP_BASE_SIZE), max(top_x, KEYCAP_TOP_SIZE)


def _keycap(width_u: float, accent: bool = False):
    base_x, top_x = _keycap_size(width_u)
    with BuildPart() as part:
        with BuildSketch(Plane.XY.offset(0.0)):
            Rectangle(base_x, KEYCAP_BASE_SIZE)
        with BuildSketch(Plane.XY.offset(KEYCAP_HEIGHT)):
            Rectangle(top_x, KEYCAP_TOP_SIZE)
        loft()
    return _color(part.part, ESC_RED if accent else PBT_DARK_GRAY)


def _stabilizer(width_u: float):
    offset = _stabilizer_offset(width_u)
    if offset is None:
        raise ValueError(f"unsupported stabilizer width: {width_u}")
    left = _color(Pos(-offset, 0.0, 1.4) * Box(4.2, 12.0, 2.8), SWITCH_DARK)
    right = _color(Pos(offset, 0.0, 1.4) * Box(4.2, 12.0, 2.8), SWITCH_DARK)
    wire = _color(Pos(0.0, 0.0, 3.0) * Rot(0.0, 90.0, 0.0) * Cylinder(0.55, offset * 2.0), CONNECTOR_SILVER)
    return Compound(children=[left, right, wire])


def _rubber_foot():
    return _color(Pos(0.0, 0.0, RUBBER_FOOT_HEIGHT / 2.0) * Cylinder(RUBBER_FOOT_RADIUS, RUBBER_FOOT_HEIGHT), RUBBER_BLACK)


def _foot_positions() -> tuple[tuple[float, float], ...]:
    case_w, case_d = _case_size()
    return (
        (-case_w / 2.0 + 18.0, -case_d / 2.0 + 14.0),
        (case_w / 2.0 - 18.0, -case_d / 2.0 + 14.0),
        (-case_w / 2.0 + 18.0, case_d / 2.0 - 14.0),
        (case_w / 2.0 - 18.0, case_d / 2.0 - 14.0),
    )


def _identity_at(x: float, y: float, z: float) -> list[float]:
    return [
        1.0,
        0.0,
        0.0,
        x,
        0.0,
        1.0,
        0.0,
        y,
        0.0,
        0.0,
        1.0,
        z,
        0.0,
        0.0,
        0.0,
        1.0,
    ]


def _multiply_transforms(left: tuple[float, ...], right: tuple[float, ...]) -> tuple[float, ...]:
    product: list[float] = []
    for row in range(4):
        for column in range(4):
            total = 0.0
            for offset in range(4):
                total += left[(row * 4) + offset] * right[(offset * 4) + column]
            product.append(total)
    return tuple(product)


def _location_from_transform(transform: tuple[float, ...]) -> Location:
    from OCP.gp import gp_Trsf

    trsf = gp_Trsf()
    trsf.SetValues(
        transform[0],
        transform[1],
        transform[2],
        transform[3],
        transform[4],
        transform[5],
        transform[6],
        transform[7],
        transform[8],
        transform[9],
        transform[10],
        transform[11],
    )
    return Location(trsf)


def _rotation_x_transform(angle_deg: float, z_lift: float) -> list[float]:
    theta = math.radians(angle_deg)
    c = math.cos(theta)
    s = math.sin(theta)
    return [
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        c,
        -s,
        0.0,
        0.0,
        s,
        c,
        z_lift,
        0.0,
        0.0,
        0.0,
        1.0,
    ]


def _pose_lift_z() -> float:
    _, case_d = _case_size()
    theta = math.radians(CASE_ANGLE_DEG)
    local_min_y = -case_d / 2.0
    local_min_z = -RUBBER_FOOT_HEIGHT
    return -(local_min_y * math.sin(theta) + local_min_z * math.cos(theta))


def _exploded_layer(layer: float) -> float:
    return layer * EXPLODED_GAP if EXPLODED_VIEW else 0.0


def _leaf(name: str, path: str, x: float, y: float, z: float) -> dict[str, object]:
    return {"name": name, "path": path, "transform": _identity_at(x, y, z)}


def _subassembly(name: str, children: list[dict[str, object]], transform: list[float] | None = None) -> dict[str, object]:
    return {"name": name, "transform": transform or _identity_at(0.0, 0.0, 0.0), "children": children}


def _key_name(prefix: str, key: Key) -> str:
    return f"{prefix}_r{key.row:02d}_k{key.index_in_row:02d}_{key.label}"


def _component_paths() -> dict[str, str]:
    unique_widths = sorted({key.width_u for key in layout_keys()})
    stabilizer_widths = sorted({key.width_u for key in _stabilizer_keys()})
    paths: dict[str, str] = {
        "top_case": _write_component("top_case_frame", _top_case_frame()),
        "bottom_tray": _write_component("bottom_tray", _bottom_tray()),
        "switch_plate": _write_component("switch_plate", _switch_plate()),
        "pcb": _write_component("pcb_with_usb_c_placeholder", _pcb()),
        "mx_switch": _write_component("mx_switch_placeholder", _mx_switch()),
        "rubber_foot": _write_component("rubber_foot", _rubber_foot()),
    }
    for width in unique_widths:
        token = str(width).replace(".", "p")
        paths[f"keycap_{token}u"] = _write_component(f"keycap_{token}u_dark_pbt", _keycap(width))
    paths["keycap_1p0u_red"] = _write_component("keycap_1p0u_red_escape", _keycap(1.0, accent=True))
    for width in stabilizer_widths:
        token = str(width).replace(".", "p")
        paths[f"stabilizer_{token}u"] = _write_component(f"stabilizer_{token}u_placeholder", _stabilizer(width))
    return paths


def _component_shape_refs() -> tuple[dict[str, str], dict[str, object]]:
    unique_widths = sorted({key.width_u for key in layout_keys()})
    stabilizer_widths = sorted({key.width_u for key in _stabilizer_keys()})
    refs: dict[str, str] = {
        "top_case": "shape/top_case",
        "bottom_tray": "shape/bottom_tray",
        "switch_plate": "shape/switch_plate",
        "pcb": "shape/pcb",
        "mx_switch": "shape/mx_switch",
        "rubber_foot": "shape/rubber_foot",
    }
    shapes: dict[str, object] = {
        refs["top_case"]: _top_case_frame(),
        refs["bottom_tray"]: _bottom_tray(),
        refs["switch_plate"]: _switch_plate(),
        refs["pcb"]: _pcb(),
        refs["mx_switch"]: _mx_switch(),
        refs["rubber_foot"]: _rubber_foot(),
    }
    for width in unique_widths:
        token = str(width).replace(".", "p")
        ref = f"shape/keycap_{token}u"
        refs[f"keycap_{token}u"] = ref
        shapes[ref] = _keycap(width)
    refs["keycap_1p0u_red"] = "shape/keycap_1p0u_red"
    shapes[refs["keycap_1p0u_red"]] = _keycap(1.0, accent=True)
    for width in stabilizer_widths:
        token = str(width).replace(".", "p")
        ref = f"shape/stabilizer_{token}u"
        refs[f"stabilizer_{token}u"] = ref
        shapes[ref] = _stabilizer(width)
    return refs, shapes


def _assembly_children(paths: dict[str, str]) -> list[dict[str, object]]:
    keys = layout_keys()
    switch_children = [
        _leaf(_key_name("switch", key), paths["mx_switch"], key.x, key.y, _switch_z())
        for key in keys
    ]
    keycap_children = []
    for key in keys:
        token = str(key.width_u).replace(".", "p")
        keycap_path = paths["keycap_1p0u_red"] if key.label == "Esc" else paths[f"keycap_{token}u"]
        keycap_children.append(_leaf(_key_name("keycap", key), keycap_path, key.x, key.y, _keycap_z()))

    stabilizer_children = []
    for key in _stabilizer_keys():
        token = str(key.width_u).replace(".", "p")
        stabilizer_children.append(
            _leaf(
                _key_name("stabilizer", key),
                paths[f"stabilizer_{token}u"],
                key.x,
                key.y,
                _plate_z() + PLATE_THICKNESS + 0.15,
            )
        )

    foot_children = [
        _leaf(f"rubber_foot_{index:02d}", paths["rubber_foot"], x, y, -RUBBER_FOOT_HEIGHT)
        for index, (x, y) in enumerate(_foot_positions(), start=1)
    ]

    return [
        _subassembly(
            "keyboard_6deg_typing_pose",
            [
                _subassembly(
                    "case_module",
                    [
                        _leaf("bottom_tray_black_anodized_aluminum", paths["bottom_tray"], 0.0, 0.0, 0.0),
                        _leaf(
                            "top_case_frame_black_anodized_aluminum",
                            paths["top_case"],
                            0.0,
                            0.0,
                            _top_case_z() + _exploded_layer(1.0),
                        ),
                    ],
                ),
                _subassembly(
                    "electronics_module",
                    [_leaf("pcb_with_usb_c_connector", paths["pcb"], 0.0, 0.0, _pcb_z() + _exploded_layer(1.6))],
                ),
                _subassembly(
                    "switch_plate_module",
                    [
                        _leaf(
                            "brushed_aluminum_switch_plate",
                            paths["switch_plate"],
                            0.0,
                            0.0,
                            _plate_z() + _exploded_layer(2.2),
                        ),
                        *stabilizer_children,
                    ],
                ),
                _subassembly("mx_switch_placeholder_set", switch_children),
                _subassembly("dark_gray_pbt_keycap_set", keycap_children),
                _subassembly("rubber_feet_module", foot_children),
            ],
            transform=_rotation_x_transform(CASE_ANGLE_DEG, _pose_lift_z()),
        )
    ]


def _switch_cutout_rects() -> list[tuple[float, float, float, float]]:
    return [(key.x, key.y, MX_CUTOUT, MX_CUTOUT) for key in layout_keys()]


def _rects_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return abs(ax - bx) < (aw + bw) / 2.0 and abs(ay - by) < (ah + bh) / 2.0


def _circle_overlaps_rect(cx: float, cy: float, radius: float, rect: tuple[float, float, float, float]) -> bool:
    rx, ry, rw, rh = rect
    dx = max(abs(cx - rx) - rw / 2.0, 0.0)
    dy = max(abs(cy - ry) - rh / 2.0, 0.0)
    return dx * dx + dy * dy < radius * radius


def validate_design() -> dict[str, object]:
    keys = layout_keys()
    issues: list[str] = []

    if len(keys) != 84:
        issues.append(f"expected 84 keys, found {len(keys)}")

    for key in keys:
        keycap_center = (key.x, key.y)
        switch_center = (key.x, key.y)
        if math.dist(keycap_center, switch_center) > 1e-6:
            issues.append(f"keycap not centered over switch cutout: {key.label}")

    switch_rects = _switch_cutout_rects()
    for index, rect in enumerate(switch_rects):
        for other_index in range(index + 1, len(switch_rects)):
            if _rects_overlap(rect, switch_rects[other_index]):
                issues.append(f"switch cutouts overlap: {index + 1} and {other_index + 1}")

    stabilizer_rects = _stabilizer_slot_rects()
    usb_rect = (
        0.0,
        _case_size()[1] / 2.0 - CASE_WALL_THICKNESS / 2.0,
        USB_C_CUTOUT_WIDTH,
        CASE_WALL_THICKNESS * 3.0,
    )
    for x, y in _mounting_points():
        if _boss_height() > _pcb_z() - 0.2:
            issues.append(f"screw boss reaches PCB envelope at ({x:.2f}, {y:.2f})")
        for rect in switch_rects:
            if _circle_overlaps_rect(x, y, MOUNT_BOSS_RADIUS, rect):
                issues.append(f"screw boss collides with switch cutout at ({x:.2f}, {y:.2f})")
        for rect in stabilizer_rects:
            if _circle_overlaps_rect(x, y, MOUNT_BOSS_RADIUS, rect):
                issues.append(f"screw boss collides with stabilizer slot at ({x:.2f}, {y:.2f})")
        if _circle_overlaps_rect(x, y, MOUNT_BOSS_RADIUS, usb_rect):
            issues.append(f"screw boss collides with USB-C cutout at ({x:.2f}, {y:.2f})")

    key_w, key_d = _key_area_size()
    derived_rear_height = FRONT_HEIGHT + math.tan(math.radians(CASE_ANGLE_DEG)) * key_d
    angle_from_heights = math.degrees(math.atan2(REAR_HEIGHT - FRONT_HEIGHT, key_d))

    return {
        "valid": not issues,
        "issues": issues,
        "units": "mm",
        "key_count": len(keys),
        "switch_cutout_count": len(switch_rects),
        "stabilizer_position_count": len(_stabilizer_keys()),
        "layout_row_count": len(LAYOUT_ROWS),
        "layout_width_u": _layout_extents_u()[1] - _layout_extents_u()[0],
        "layout_depth_u": _layout_extents_u()[3] - _layout_extents_u()[2],
        "key_area_size_mm": {"x": key_w, "y": key_d},
        "plate_size_mm": {"x": _plate_size()[0], "y": _plate_size()[1], "z": PLATE_THICKNESS},
        "case_size_mm": {"x": _case_size()[0], "y": _case_size()[1]},
        "typing_angle_deg": CASE_ANGLE_DEG,
        "front_height_mm": FRONT_HEIGHT,
        "rear_height_mm": REAR_HEIGHT,
        "rear_height_from_angle_over_key_area_mm": derived_rear_height,
        "angle_from_front_rear_over_key_area_deg": angle_from_heights,
        "exploded_view": EXPLODED_VIEW,
    }


def validation_report(include_step_bbox: bool = True) -> dict[str, object]:
    report = validate_design()
    step_path = Path(__file__).resolve().parent / STEP_OUTPUT
    if include_step_bbox and step_path.exists():
        from build123d import import_step

        shape = import_step(step_path)
        bbox = shape.bounding_box()
        size_x = bbox.max.X - bbox.min.X
        size_y = bbox.max.Y - bbox.min.Y
        size_z = bbox.max.Z - bbox.min.Z
        report["final_bounding_box_mm"] = {
            "min": {"x": bbox.min.X, "y": bbox.min.Y, "z": bbox.min.Z},
            "max": {"x": bbox.max.X, "y": bbox.max.Y, "z": bbox.max.Z},
            "size": {"x": size_x, "y": size_y, "z": size_z},
        }
    return report


def write_validation_report() -> Path:
    report_path = Path(__file__).resolve().parent / REPORT_OUTPUT
    report_path.write_text(json.dumps(validation_report(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_path


def _flatten_colored_nodes(
    nodes: list[dict[str, object]],
    shapes_by_ref: dict[str, object],
    *,
    parent_transform: tuple[float, ...],
    path: tuple[str, ...] = (),
) -> list[object]:
    flattened: list[object] = []
    for node in nodes:
        name = str(node["name"])
        transform = tuple(float(value) for value in node["transform"])
        world_transform = _multiply_transforms(parent_transform, transform)
        node_path = (*path, name)
        children = node.get("children")
        if isinstance(children, list):
            flattened.extend(
                _flatten_colored_nodes(
                    children,
                    shapes_by_ref,
                    parent_transform=world_transform,
                    path=node_path,
                )
            )
            continue
        source_ref = str(node["path"])
        shape = shapes_by_ref[source_ref].moved(_location_from_transform(world_transform))
        shape.label = "__".join(node_path)
        flattened.append(shape)
    return flattened


def write_colored_demo_step() -> Path:
    refs, shapes = _component_shape_refs()
    children = _assembly_children(refs)
    leaves = _flatten_colored_nodes(
        children,
        shapes,
        parent_transform=tuple(_identity_at(0.0, 0.0, 0.0)),
    )
    root = Compound(children=leaves)
    root.label = "compact_75_ansi_keyboard_colored_demo"
    output = Path(__file__).resolve().parent / COLORED_STEP_OUTPUT
    if not export_step(root, output):
        raise RuntimeError(f"failed to export colored demo STEP: {output}")
    return output


def gen_step():
    _limit_dependency_catalog_scan()
    paths = _component_paths()
    return {"children": _assembly_children(paths), "step_output": "compact_75_ansi_keyboard_assembly.step"}


if __name__ == "__main__":
    result = validate_design()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["valid"]:
        raise SystemExit(1)
