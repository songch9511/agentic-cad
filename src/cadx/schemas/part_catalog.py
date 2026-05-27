from __future__ import annotations

from pydantic import BaseModel, Field


class CatalogSource(BaseModel):
    id: str
    name: str
    source_type: str
    source_uri: str
    provenance_status: str
    license_status: str
    notes: str | None = None


class CatalogPart(BaseModel):
    id: str
    part_id: str | None = None
    name: str
    source_id: str
    source_uri: str
    source_kind: str = "local_seed"
    manufacturer: str | None = None
    model: str | None = None
    category: str
    tags: list[str] = Field(default_factory=list)
    interfaces: list[str] = Field(default_factory=list)
    dimension_tags: list[str] = Field(default_factory=list)
    interface_tags: list[str] = Field(default_factory=list)
    selection_suitability: list[str] = Field(default_factory=list)
    license_status: str = "unspecified"
    provenance_status: str = "unspecified"
    checksum_sha256: str | None = None
    original_step_path: str
    normalized_step_path: str
    immutable_original: bool = True
    metadata_path: str | None = None
    part_record_path: str


class PartSelectionTrace(BaseModel):
    id: str
    run_id: str
    product_spec_id: str
    generated_at: str
    selected_part_id: str
    selected_by: str
    source_id: str
    source_uri: str
    source_kind: str
    catalog_path: str
    part_record_path: str
    original_step_path: str
    normalized_step_path: str
    immutable_original: bool
    checksum_sha256: str | None = None
    candidate_count: int
    candidate_part_ids: list[str] = Field(default_factory=list)
    selection_reason: str
    constraints_matched: list[str] = Field(default_factory=list)
    interface_tags_matched: list[str] = Field(default_factory=list)
    dimension_tags_matched: list[str] = Field(default_factory=list)


class PartCatalog(BaseModel):
    id: str
    run_id: str
    product_spec_id: str
    sources: list[CatalogSource] = Field(default_factory=list)
    parts: list[CatalogPart] = Field(default_factory=list)

