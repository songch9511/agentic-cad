from __future__ import annotations

from pydantic import BaseModel, Field


class PackageAvailability(BaseModel):
    name: str
    available: bool
    version: str | None = None


class ReproducibilityReport(BaseModel):
    id: str
    run_id: str
    product_spec_id: str
    workflow_id: str
    template_id: str
    generated_at: str
    python_version: str
    python_version_major: int
    python_version_minor: int
    platform_system: str
    platform_machine: str
    platform_platform: str
    package_availability: list[PackageAvailability] = Field(default_factory=list)
    geometry_backend: str
    validation_status: str
    validation_gate_count: int
    validation_warning_count: int
    validation_fail_count: int
    smoke_commands: list[str] = Field(default_factory=list)
    docker_smoke_status: str
    docker_smoke_note: str
    limitations: list[str] = Field(default_factory=list)
