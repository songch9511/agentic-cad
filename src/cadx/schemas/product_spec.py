from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

from .common import Unit


class MotionRequirement(BaseModel):
    dof: int
    axes: list[Literal["roll", "pitch", "yaw", "linear_x", "linear_y", "linear_z"]]
    range_deg: dict[str, float] = Field(default_factory=dict)
    torque_hint: str | None = None


class FunctionalRequirement(BaseModel):
    id: str
    description: str
    function_type: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    required_motion: MotionRequirement | None = None


class Constraint(BaseModel):
    id: str
    type: Literal["size", "weight", "material", "manufacturing", "interface", "cost"]
    description: str
    value: Any | None = None


class OutputRequirements(BaseModel):
    generate_step: bool = True
    generate_urdf: bool = True
    generate_bom: bool = True
    generate_validation_report: bool = True
    generate_html_report: bool = True


class ProductSpec(BaseModel):
    id: str
    name: str
    description: str
    units: Unit = "mm"
    product_type: str
    workflow_id: str | None = None
    template_id: str | None = None
    functional_requirements: list[FunctionalRequirement]
    constraints: list[Constraint] = Field(default_factory=list)
    preferred_parts: list[str] = Field(default_factory=list)
    avoid_parts: list[str] = Field(default_factory=list)
    output_requirements: OutputRequirements = Field(default_factory=OutputRequirements)
    assumptions: list[str] = Field(default_factory=list)
