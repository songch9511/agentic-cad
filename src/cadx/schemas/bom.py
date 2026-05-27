from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class BOMItem(BaseModel):
    id: str
    role: str
    part_query: str
    quantity: int = 1
    selected_part_id: str | None = None
    required_interfaces: list[str] = Field(default_factory=list)
    status: Literal["selected", "missing", "custom_required", "placeholder"] = "missing"


class CustomPartRequest(BaseModel):
    id: str
    role: str
    description: str
    required_interfaces: list[str]
    design_contract_id: str | None = None


class BOM(BaseModel):
    id: str
    product_spec_id: str
    items: list[BOMItem]
    generated_custom_parts: list[CustomPartRequest] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
