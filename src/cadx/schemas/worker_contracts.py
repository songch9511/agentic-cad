from __future__ import annotations

from pydantic import BaseModel, Field


class WorkerSkillContract(BaseModel):
    id: str
    label: str
    category: str
    responsible_worker_type: str
    expected_inputs: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    required_artifacts: list[str] = Field(default_factory=list)
    validation_gates: list[str] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)
    status: str = "implemented"


class WorkerContractSet(BaseModel):
    id: str
    run_id: str
    product_spec_id: str
    workflow_id: str
    template_id: str
    generated_at: str
    contracts: list[WorkerSkillContract] = Field(default_factory=list)

