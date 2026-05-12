from __future__ import annotations

from math import cos, pi, sin

from build123d import Box, BuildLine, BuildSketch, Circle, Cylinder, JernArc, Plane, Pos, Rot, sweep


def x_cylinder(radius: float, length: float, *, x: float = 0, y: float = 0, z: float = 0):
    return Pos(x, y, z) * Rot(0, 90, 0) * Cylinder(radius, length)


def z_cylinder(radius: float, length: float, *, x: float = 0, y: float = 0, z: float = 0):
    return Pos(x, y, z) * Cylinder(radius, length)


def x_bolt_holes(
    *,
    count: int,
    pcd: float,
    hole_diameter: float,
    cutter_length: float,
    x: float,
    phase_deg: float = 0,
):
    radius = pcd / 2
    phase = phase_deg * pi / 180
    for index in range(count):
        angle = phase + (2 * pi * index) / count
        yield x_cylinder(
            hole_diameter / 2,
            cutter_length,
            x=x,
            y=radius * cos(angle),
            z=radius * sin(angle),
        )


def z_corner_bolt_holes(
    *,
    center_x: float,
    center_y: float,
    center_z: float,
    x_spacing: float,
    y_spacing: float,
    hole_diameter: float,
    cutter_length: float,
):
    for x_sign in (-1, 1):
        for y_sign in (-1, 1):
            yield z_cylinder(
                hole_diameter / 2,
                cutter_length,
                x=center_x + x_sign * x_spacing / 2,
                y=center_y + y_sign * y_spacing / 2,
                z=center_z,
            )


def rounded_rect_plate_z(
    *,
    length: float,
    width: float,
    thickness: float,
    corner_radius: float,
    x: float = 0,
    y: float = 0,
    z: float = 0,
):
    radius = min(corner_radius, length / 2, width / 2)
    if radius <= 0:
        return Pos(x, y, z) * Box(length, width, thickness)

    shape = Pos(x, y, z) * Box(length - 2 * radius, width, thickness)
    shape += Pos(x, y, z) * Box(length, width - 2 * radius, thickness)
    for x_sign in (-1, 1):
        for y_sign in (-1, 1):
            shape += z_cylinder(
                radius,
                thickness,
                x=x + x_sign * (length / 2 - radius),
                y=y + y_sign * (width / 2 - radius),
                z=z,
            )
    return shape


def capsule_plate_z(
    *,
    length: float,
    width: float,
    thickness: float,
    x: float = 0,
    y: float = 0,
    z: float = 0,
    axis: str = "y",
):
    cap_radius = width / 2
    straight = max(0, length - width)
    if axis == "x":
        shape = Pos(x, y, z) * Box(straight, width, thickness)
        shape += z_cylinder(cap_radius, thickness, x=x - straight / 2, y=y, z=z)
        shape += z_cylinder(cap_radius, thickness, x=x + straight / 2, y=y, z=z)
        return shape

    shape = Pos(x, y, z) * Box(width, straight, thickness)
    shape += z_cylinder(cap_radius, thickness, x=x, y=y - straight / 2, z=z)
    shape += z_cylinder(cap_radius, thickness, x=x, y=y + straight / 2, z=z)
    return shape


def x_to_z_elbow(
    *,
    tube_radius: float,
    bend_radius: float,
    start_x: float,
    y: float = 0,
    start_z: float = 0,
):
    origin = (start_x, y, start_z)
    with BuildLine(Plane.XZ.shift_origin(origin)) as path:
        JernArc((0, 0), (1, 0), bend_radius, 90)
    with BuildSketch(Plane.YZ.shift_origin(origin)) as section:
        Circle(tube_radius)
    return sweep(section.sketch, path.line)
