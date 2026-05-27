from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

from .common import Transform
from .joint_spec import JointSpec


class AssemblyComponent(BaseModel):
    id: str
    part_record_id: str
    role: str
    instance_name: str
    initial_transform: Transform = Field(default_factory=Transform)
    fixed: bool = False


class MateConstraint(BaseModel):
    id: str
    parent_component: str
    parent_interface: str
    child_component: str
    child_interface: str
    type: Literal["fixed", "revolute", "coincident", "concentric", "parallel"]
    offset_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation_rpy_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)


class AssemblyPlan(BaseModel):
    id: str
    product_spec_id: str
    bom_id: str
    root_frame: str = "world"
    components: list[AssemblyComponent]
    mates: list[MateConstraint] = Field(default_factory=list)
    joints: list[JointSpec] = Field(default_factory=list)
    generated_parts: list[str] = Field(default_factory=list)
