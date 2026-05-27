from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class PreviewTarget(BaseModel):
    id: str
    kind: str
    label: str
    artifact_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class PreviewArtifact(BaseModel):
    id: str
    run_id: str
    product_spec_id: str
    workflow_id: str | None = None
    template_id: str | None = None
    validation_status: str
    validation_gate_count: int
    component_count: int
    urdf_link_count: int
    urdf_joint_count: int
    main_artifacts: dict[str, str]
    preview_targets: list[PreviewTarget] = Field(default_factory=list)
