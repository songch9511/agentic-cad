from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class ParameterSpec(BaseModel):
    name: str
    type: Literal["float", "int", "bool", "enum", "string"]
    default: Any
    min_value: float | None = None
    max_value: float | None = None
    units: str | None = None


class GeometricInvariant(BaseModel):
    type: Literal["interface_pose", "bbox_max", "hole_pattern", "axis_alignment", "clearance"]
    target: str
    value: Any
    tolerance_mm: float | None = None


class DesignContract(BaseModel):
    id: str
    target_part_id: str
    contract_type: Literal["external_part_lock", "custom_part", "adapter_part", "replacement_part"]
    locked_interfaces: list[str]
    editable_parameters: dict[str, ParameterSpec] = Field(default_factory=dict)
    geometric_invariants: list[GeometricInvariant] = Field(default_factory=list)
    allowed_operations: list[str] = Field(default_factory=list)
    forbidden_operations: list[str] = Field(default_factory=list)
