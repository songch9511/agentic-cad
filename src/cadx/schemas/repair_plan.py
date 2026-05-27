from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class RepairAction(BaseModel):
    run_id: str
    status: Literal["noop", "planned"]
    failure_class: str
    source_gate_id: str
    summary: str
    recommended_owner: str
    suggested_actions: list[str] = Field(default_factory=list)
    blocking_artifacts: list[str] = Field(default_factory=list)


class RepairPlan(BaseModel):
    id: str
    run_id: str
    product_spec_id: str
    status: Literal["pass", "warning", "blocked"]
    failure_count: int
    action_count: int
    actions: list[RepairAction] = Field(default_factory=list)
