from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class ValidationGateResult(BaseModel):
    id: str
    name: str
    status: Literal["pass", "warning", "fail", "skipped"]
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationReport(BaseModel):
    id: str
    run_id: str
    product_spec_id: str
    status: Literal["pass", "warning", "fail"]
    gates: list[ValidationGateResult]
    metrics: dict[str, Any] = Field(default_factory=dict)
    artifacts: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
