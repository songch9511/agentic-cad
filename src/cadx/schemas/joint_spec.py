from __future__ import annotations

from typing import Literal
from pydantic import BaseModel


class JointOrigin(BaseModel):
    xyz_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rpy_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)


class JointLimits(BaseModel):
    lower_deg: float | None = None
    upper_deg: float | None = None
    effort: float | None = None
    velocity: float | None = None


class JointDynamics(BaseModel):
    damping: float | None = None
    friction: float | None = None


class JointSpec(BaseModel):
    id: str
    name: str
    type: Literal["fixed", "revolute", "continuous", "prismatic"]
    parent: str
    child: str
    origin: JointOrigin = JointOrigin()
    axis: tuple[float, float, float] | None = None
    limits: JointLimits | None = None
    dynamics: JointDynamics | None = None
