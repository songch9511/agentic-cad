from __future__ import annotations

from build123d import Box, Cylinder, Pos


DISPLAY_NAME = "Benchmark four-hole block"


def _through_hole(x: float, y: float):
    return Pos(x, y, 0) * Cylinder(4, 30)


def gen_step():
    shape = Box(100, 60, 20)
    for x in (-30, 30):
        for y in (-15, 15):
            shape -= _through_hole(x, y)
    return {
        "shape": shape,
        "step_output": "four_hole_block.step",
    }
