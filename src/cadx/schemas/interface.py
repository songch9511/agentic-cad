from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

from .common import Frame


class InterfaceGeometry(BaseModel):
    kind: Literal["plane", "cylinder", "hole_pattern", "spline", "bbox_proxy"]
    parameters: dict[str, Any] = Field(default_factory=dict)


class InterfaceConstraint(BaseModel):
    type: Literal["coincident", "concentric", "parallel", "distance", "clearance", "fixed", "revolute_axis"]
    value: Any | None = None
    tolerance_mm: float | None = None


class Interface(BaseModel):
    id: str
    name: str
    type: Literal[
        "mounting_hole_pattern",
        "shaft",
        "bearing_bore",
        "servo_spline",
        "flat_mount_face",
        "electrical_connector",
        "custom",
    ]
    frame: Frame = Field(default_factory=Frame)
    geometry: InterfaceGeometry
    constraints: list[InterfaceConstraint] = Field(default_factory=list)
    compatible_with: list[str] = Field(default_factory=list)
