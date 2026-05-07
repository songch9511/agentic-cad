from __future__ import annotations

from build123d import Box


DISPLAY_NAME = "Benchmark box 100 x 60 x 20"


def gen_step():
    shape = Box(100, 60, 20)
    return {
        "shape": shape,
        "step_output": "box_100_60_20.step",
    }
