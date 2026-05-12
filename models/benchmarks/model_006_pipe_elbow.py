from __future__ import annotations

from math import cos, pi, sin

import ezdxf
from ezdxf.enums import TextEntityAlignment

from cad_features import (
    capsule_plate_z,
    rounded_rect_plate_z,
    x_bolt_holes,
    x_cylinder,
    x_to_z_elbow,
    z_corner_bolt_holes,
    z_cylinder,
)


DISPLAY_NAME = "Benchmark MODEL-006 drawing reconstruction"


PIPE_OUTER_RADIUS = 10
PIPE_INNER_RADIUS = 7.5
BEND_START_X = 0
BEND_RADIUS = 18.7
VERTICAL_X = BEND_START_X + BEND_RADIUS
FRONT_FLANGE_X = -42.5
SERVICE_X = -18


def _front_flange():
    shape = x_cylinder(57.5 / 2, 5, x=FRONT_FLANGE_X)
    shape += x_cylinder(18, 1.2, x=-45.6)
    shape += x_cylinder(13, 7, x=-38.5)

    shape -= x_cylinder(10, 13, x=FRONT_FLANGE_X)
    for cutter in x_bolt_holes(
        count=4,
        pcd=47.15,
        hole_diameter=5,
        cutter_length=9,
        x=FRONT_FLANGE_X,
        phase_deg=0,
    ):
        shape -= cutter
    return shape


def _horizontal_pipe():
    shape = x_cylinder(PIPE_OUTER_RADIUS, 42.5, x=-19.5)
    shape -= x_cylinder(PIPE_INNER_RADIUS, 44.5, x=-19.5)
    return shape


def _elbow():
    shape = x_to_z_elbow(
        tube_radius=PIPE_OUTER_RADIUS,
        bend_radius=BEND_RADIUS,
        start_x=BEND_START_X,
    )
    shape -= x_to_z_elbow(
        tube_radius=PIPE_INNER_RADIUS,
        bend_radius=BEND_RADIUS,
        start_x=BEND_START_X,
    )
    return shape


def _vertical_pipe():
    lower_z = BEND_RADIUS
    upper_z = 52.8
    height = upper_z - lower_z
    center_z = lower_z + height / 2
    shape = z_cylinder(PIPE_OUTER_RADIUS, height, x=VERTICAL_X, z=center_z)
    shape -= z_cylinder(PIPE_INNER_RADIUS, height + 2, x=VERTICAL_X, z=center_z)
    return shape


def _top_flange():
    shape = z_cylinder(PIPE_OUTER_RADIUS, 17, x=VERTICAL_X, z=41.5)
    shape += rounded_rect_plate_z(
        length=50,
        width=40,
        thickness=5,
        corner_radius=5,
        x=VERTICAL_X,
        z=52.5,
    )

    shape -= z_cylinder(PIPE_INNER_RADIUS, 26, x=VERTICAL_X, z=42)
    for cutter in z_corner_bolt_holes(
        center_x=VERTICAL_X,
        center_y=0,
        center_z=52.5,
        x_spacing=40,
        y_spacing=30,
        hole_diameter=5,
        cutter_length=10,
    ):
        shape -= cutter
    return shape


def _service_port():
    shape = z_cylinder(PIPE_OUTER_RADIUS, 26, x=SERVICE_X, z=13)
    shape += capsule_plate_z(
        length=35,
        width=25,
        thickness=5,
        x=SERVICE_X,
        z=27.5,
        axis="y",
    )

    shape -= z_cylinder(PIPE_INNER_RADIUS, 30, x=SERVICE_X, z=15)
    shape -= z_cylinder(2.5, 9, x=SERVICE_X, y=-12.5, z=27.5)
    shape -= z_cylinder(2.5, 9, x=SERVICE_X, y=12.5, z=27.5)
    return shape


def gen_step():
    shape = _front_flange()
    shape += _horizontal_pipe()
    shape += _elbow()
    shape += _vertical_pipe()
    shape += _top_flange()
    shape += _service_port()
    shape = shape.clean()

    return {
        "shape": shape,
        "step_output": "model_006_pipe_elbow.step",
        "glb_tolerance": 0.04,
        "glb_angular_tolerance": 0.04,
    }


def _add_text(msp, text, xy, height=2.5, *, layer="TEXT", align=TextEntityAlignment.LEFT):
    entity = msp.add_text(text, dxfattribs={"height": height, "layer": layer})
    entity.set_placement(xy, align=align)
    return entity


def _add_center_mark(msp, center, radius, *, layer="CENTER"):
    x, y = center
    overrun = 5
    msp.add_line((x - radius - overrun, y), (x + radius + overrun, y), dxfattribs={"layer": layer})
    msp.add_line((x, y - radius - overrun), (x, y + radius + overrun), dxfattribs={"layer": layer})


def _add_bolt_circle(msp, center, pcd, count, hole_radius, *, layer="OBJECT"):
    x, y = center
    msp.add_circle(center, pcd / 2, dxfattribs={"layer": "CENTER"})
    for index in range(count):
        angle = (2 * pi * index) / count
        hole_center = (x + pcd * cos(angle) / 2, y + pcd * sin(angle) / 2)
        msp.add_circle(hole_center, hole_radius, dxfattribs={"layer": layer})
        _add_center_mark(msp, hole_center, hole_radius + 1.2)


def _add_rounded_rect(msp, center, length, width, radius, *, layer="OBJECT"):
    x, y = center
    left = x - length / 2
    right = x + length / 2
    bottom = y - width / 2
    top = y + width / 2
    points = [
        (left + radius, bottom),
        (right - radius, bottom),
        (right, bottom + radius),
        (right, top - radius),
        (right - radius, top),
        (left + radius, top),
        (left, top - radius),
        (left, bottom + radius),
        (left + radius, bottom),
    ]
    msp.add_lwpolyline(points, dxfattribs={"layer": layer})
    msp.add_arc((right - radius, bottom + radius), radius, 270, 360, dxfattribs={"layer": layer})
    msp.add_arc((right - radius, top - radius), radius, 0, 90, dxfattribs={"layer": layer})
    msp.add_arc((left + radius, top - radius), radius, 90, 180, dxfattribs={"layer": layer})
    msp.add_arc((left + radius, bottom + radius), radius, 180, 270, dxfattribs={"layer": layer})


def _add_capsule(msp, center, length, width, *, layer="OBJECT"):
    x, y = center
    radius = width / 2
    straight = length - width
    msp.add_line((x - radius, y - straight / 2), (x - radius, y + straight / 2), dxfattribs={"layer": layer})
    msp.add_line((x + radius, y - straight / 2), (x + radius, y + straight / 2), dxfattribs={"layer": layer})
    msp.add_arc((x, y + straight / 2), radius, 0, 180, dxfattribs={"layer": layer})
    msp.add_arc((x, y - straight / 2), radius, 180, 360, dxfattribs={"layer": layer})


def _add_arrow(msp, tip, angle_rad, *, size=2.5, layer="DIM"):
    x, y = tip
    for sign in (-1, 1):
        a = angle_rad + sign * 0.42
        msp.add_line((x, y), (x - size * cos(a), y - size * sin(a)), dxfattribs={"layer": layer})


def _add_dim_h(msp, x1, x2, y, ext_y, label):
    msp.add_line((x1, ext_y), (x1, y), dxfattribs={"layer": "DIM"})
    msp.add_line((x2, ext_y), (x2, y), dxfattribs={"layer": "DIM"})
    msp.add_line((x1, y), (x2, y), dxfattribs={"layer": "DIM"})
    _add_arrow(msp, (x1, y), 0)
    _add_arrow(msp, (x2, y), pi)
    _add_text(msp, label, ((x1 + x2) / 2, y + 2.2), 2.2, layer="DIM", align=TextEntityAlignment.MIDDLE_CENTER)


def _add_dim_v(msp, x, y1, y2, ext_x, label):
    msp.add_line((ext_x, y1), (x, y1), dxfattribs={"layer": "DIM"})
    msp.add_line((ext_x, y2), (x, y2), dxfattribs={"layer": "DIM"})
    msp.add_line((x, y1), (x, y2), dxfattribs={"layer": "DIM"})
    _add_arrow(msp, (x, y1), pi / 2)
    _add_arrow(msp, (x, y2), -pi / 2)
    _add_text(msp, label, (x - 2.6, (y1 + y2) / 2), 2.2, layer="DIM", align=TextEntityAlignment.MIDDLE_CENTER)


def _add_datum(msp, label, xy, *, layer="GD&T"):
    x, y = xy
    msp.add_lwpolyline([(x, y), (x + 8, y), (x + 8, y + 6), (x, y + 6), (x, y)], dxfattribs={"layer": layer})
    _add_text(msp, label, (x + 4, y + 3), 3.0, layer=layer, align=TextEntityAlignment.MIDDLE_CENTER)


def _add_fcf(msp, cells, xy, *, cell_w=18, cell_h=6, layer="GD&T"):
    x, y = xy
    width = cell_w * len(cells)
    for index, cell in enumerate(cells):
        left = x + index * cell_w
        msp.add_lwpolyline(
            [(left, y), (left + cell_w, y), (left + cell_w, y + cell_h), (left, y + cell_h), (left, y)],
            dxfattribs={"layer": layer},
        )
        _add_text(msp, cell, (left + cell_w / 2, y + cell_h / 2), 2.2, layer=layer, align=TextEntityAlignment.MIDDLE_CENTER)
    return width


def _add_leader(msp, start, elbow, text_xy, text, *, layer="DIM"):
    msp.add_line(start, elbow, dxfattribs={"layer": layer})
    msp.add_line(elbow, text_xy, dxfattribs={"layer": layer})
    _add_arrow(msp, start, 0.8, layer=layer)
    _add_text(msp, text, (text_xy[0] + 1.5, text_xy[1] + 1.0), 2.2, layer=layer)


def _setup_dxf():
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    layer_defs = {
        "SHEET": 7,
        "OBJECT": 7,
        "HIDDEN": 8,
        "CENTER": 5,
        "DIM": 3,
        "TEXT": 7,
        "GD&T": 1,
    }
    for layer, color in layer_defs.items():
        if layer not in doc.layers:
            doc.layers.new(layer, dxfattribs={"color": color})
    doc.layers.get("CENTER").dxf.linetype = "CENTER"
    doc.layers.get("HIDDEN").dxf.linetype = "HIDDEN"
    return doc


def _draw_sheet(msp):
    msp.add_lwpolyline([(8, 8), (289, 8), (289, 202), (8, 202), (8, 8)], dxfattribs={"layer": "SHEET"})
    msp.add_lwpolyline([(190, 8), (289, 8), (289, 38), (190, 38), (190, 8)], dxfattribs={"layer": "SHEET"})
    for y in (18, 28):
        msp.add_line((190, y), (289, y), dxfattribs={"layer": "SHEET"})
    for x in (220, 250):
        msp.add_line((x, 8), (x, 38), dxfattribs={"layer": "SHEET"})
    _add_text(msp, "DIMENSION AI", (194, 31), 3.0)
    _add_text(msp, "3D CAD TO GD&T DRAWING", (194, 22), 2.5)
    _add_text(msp, "MODEL-006 PIPE ELBOW", (194, 12), 2.5)
    _add_text(msp, "UNITS", (224, 31), 2.0)
    _add_text(msp, "MM", (255, 31), 2.5)
    _add_text(msp, "STANDARD", (224, 22), 2.0)
    _add_text(msp, "ASME Y14.5 STYLE", (252, 22), 2.0)
    _add_text(msp, "SOURCE STEP", (224, 12), 2.0)
    _add_text(msp, "model_006_pipe_elbow.step", (252, 12), 1.8)


def _draw_front_flange_view(msp, center=(70, 122)):
    x, y = center
    msp.add_circle(center, 57.5 / 2, dxfattribs={"layer": "OBJECT"})
    msp.add_circle(center, 10, dxfattribs={"layer": "OBJECT"})
    msp.add_circle(center, 18, dxfattribs={"layer": "OBJECT"})
    _add_bolt_circle(msp, center, 47.15, 4, 2.5)
    _add_center_mark(msp, center, 31)
    _add_text(msp, "FRONT FLANGE VIEW", (x, y - 42), 2.5, align=TextEntityAlignment.MIDDLE_CENTER)
    _add_datum(msp, "B", (x + 15, y + 12))
    _add_leader(msp, (x + 23.6, y), (x + 42, y + 12), (x + 47, y + 12), "4X DIA 5 THRU ON DIA 47.15 B.C.")
    _add_leader(msp, (x + 10, y), (x + 36, y - 12), (x + 42, y - 12), "DIA 20 PORT / DIA 15 BORE")
    _add_fcf(msp, ["POS", "DIA 0.20 M", "A", "B"], (x + 42, y + 25), cell_w=18)


def _draw_top_flange_view(msp, center=(178, 122)):
    x, y = center
    _add_rounded_rect(msp, center, 50, 40, 5)
    for hx in (-20, 20):
        for hy in (-15, 15):
            msp.add_circle((x + hx, y + hy), 2.5, dxfattribs={"layer": "OBJECT"})
            _add_center_mark(msp, (x + hx, y + hy), 4)
    msp.add_circle(center, 10, dxfattribs={"layer": "OBJECT"})
    msp.add_circle(center, 7.5, dxfattribs={"layer": "HIDDEN"})
    _add_center_mark(msp, center, 23)
    _add_text(msp, "TOP FLANGE VIEW", (x, y - 36), 2.5, align=TextEntityAlignment.MIDDLE_CENTER)
    _add_dim_h(msp, x - 25, x + 25, y - 28, y - 20, "50")
    _add_dim_v(msp, x + 34, y - 20, y + 20, x + 25, "40")
    _add_leader(msp, (x + 20, y + 15), (x + 42, y + 21), (x + 48, y + 21), "4X DIA 5 THRU")
    _add_datum(msp, "C", (x - 4, y + 24))
    _add_fcf(msp, ["POS", "DIA 0.20 M", "A", "B", "C"], (x + 42, y - 1), cell_w=17)


def _draw_side_section_view(msp, origin=(40, 55)):
    x, y = origin
    msp.add_lwpolyline([(x, y), (x + 78, y), (x + 78, y + 20), (x + 4, y + 20), (x + 4, y), (x, y)], dxfattribs={"layer": "OBJECT"})
    msp.add_line((x, y + 2.5), (x + 72, y + 2.5), dxfattribs={"layer": "HIDDEN"})
    msp.add_line((x + 4, y + 17.5), (x + 72, y + 17.5), dxfattribs={"layer": "HIDDEN"})
    msp.add_arc((x + 78, y + 20), 18.7, 270, 360, dxfattribs={"layer": "OBJECT"})
    msp.add_line((x + 96.7, y + 20), (x + 96.7, y + 55), dxfattribs={"layer": "OBJECT"})
    msp.add_line((x + 76.7, y + 20), (x + 76.7, y + 55), dxfattribs={"layer": "OBJECT"})
    _add_dim_v(msp, x - 10, y, y + 20, x, "DIA 20")
    _add_leader(msp, (x + 76, y + 20), (x + 93, y + 35), (x + 104, y + 35), "R18.7 BEND")
    _add_text(msp, "SECTION A-A", (x + 48, y - 12), 2.5, align=TextEntityAlignment.MIDDLE_CENTER)
    _add_datum(msp, "A", (x - 5, y + 24))
    _add_fcf(msp, ["PERP", "0.10", "A"], (x + 108, y + 49), cell_w=18)


def _draw_service_port_view(msp, center=(230, 112)):
    x, y = center
    _add_capsule(msp, center, 35, 25)
    msp.add_circle(center, 10, dxfattribs={"layer": "OBJECT"})
    for hy in (-12.5, 12.5):
        msp.add_circle((x, y + hy), 2.5, dxfattribs={"layer": "OBJECT"})
        _add_center_mark(msp, (x, y + hy), 4)
    _add_center_mark(msp, center, 18)
    _add_text(msp, "SERVICE PORT", (x, y - 31), 2.5, align=TextEntityAlignment.MIDDLE_CENTER)
    _add_leader(msp, (x, y + 12.5), (x + 20, y + 24), (x + 26, y + 24), "2X DIA 5")
    _add_fcf(msp, ["POS", "DIA 0.25 M", "A", "B"], (x + 24, y - 3), cell_w=18)


def _draw_notes(msp):
    notes = [
        "NOTES:",
        "1. REMOVE BURRS AND SHARP EDGES.",
        "2. GENERAL TOLERANCE: +/-0.20 UNLESS OTHERWISE SPECIFIED.",
        "3. DATUM A: FRONT FLANGE MOUNTING FACE.",
        "4. DATUM B: AXIS OF MAIN BORE.",
        "5. DATUM C: TOP FLANGE MOUNTING FACE.",
        "6. GD&T CALLOUTS ARE AUTO-PROPOSED FROM STEP FEATURES FOR DEMO REVIEW.",
    ]
    for index, note in enumerate(notes):
        _add_text(msp, note, (20, 190 - index * 5), 2.2)


def gen_dxf():
    doc = _setup_dxf()
    msp = doc.modelspace()
    _draw_sheet(msp)
    _draw_notes(msp)
    _draw_front_flange_view(msp)
    _draw_top_flange_view(msp)
    _draw_side_section_view(msp)
    _draw_service_port_view(msp)
    return {
        "document": doc,
        "dxf_output": "model_006_pipe_elbow_gdt.dxf",
    }
