from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewChecklistItem(BaseModel):
    id: str
    label: str
    status: str
    evidence_artifacts: list[str] = Field(default_factory=list)
    validation_gates: list[str] = Field(default_factory=list)


class ReviewArtifactGroup(BaseModel):
    id: str
    label: str
    artifacts: list[str] = Field(default_factory=list)


class ReviewState(BaseModel):
    id: str
    run_id: str
    product_spec_id: str
    workflow_id: str
    template_id: str
    generated_at: str
    review_status: str
    validation_status: str
    validation_gate_count: int
    validation_pass_count: int
    validation_warning_count: int
    validation_fail_count: int
    repair_status: str
    repair_action_count: int
    artifact_groups: list[ReviewArtifactGroup] = Field(default_factory=list)
    checklist: list[ReviewChecklistItem] = Field(default_factory=list)
    preview_targets: list[str] = Field(default_factory=list)
    part_provenance_artifacts: list[str] = Field(default_factory=list)
    worker_contract_artifact: str
    limitations: list[str] = Field(default_factory=list)
