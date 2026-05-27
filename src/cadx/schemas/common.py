from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class BBox(BaseModel):
    x: float
    y: float
    z: float


class Frame(BaseModel):
    origin_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    x_axis: tuple[float, float, float] = (1.0, 0.0, 0.0)
    y_axis: tuple[float, float, float] = (0.0, 1.0, 0.0)
    z_axis: tuple[float, float, float] = (0.0, 0.0, 1.0)


class Transform(BaseModel):
    translation_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation_rpy_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)


class ArtifactRef(BaseModel):
    path: str
    kind: str
    placeholder: bool = False
    notes: list[str] = Field(default_factory=list)


JSONValue = Any
Unit = Literal["mm", "inch"]
