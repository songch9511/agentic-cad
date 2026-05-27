from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

from .common import BBox, Unit
from .interface import Interface


class PartRecord(BaseModel):
    id: str
    name: str
    source: Literal["library", "vendor", "generated", "placeholder"]
    category: str
    original_step_path: str | None = None
    normalized_step_path: str | None = None
    mesh_preview_path: str | None = None
    datasheet_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    units: Unit = "mm"
    bbox_mm: BBox | None = None
    mass_g: float | None = None
    material: str | None = None
    interfaces: list[Interface] = Field(default_factory=list)
    immutable_original: bool = True
    design_contract_id: str | None = None
