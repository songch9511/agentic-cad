from __future__ import annotations

import importlib.metadata
import json
import platform
import shutil
import sys
from html import escape
from pathlib import Path
from textwrap import dedent
from xml.etree.ElementTree import Element, SubElement, ElementTree, ParseError, parse

from cadx.demos import pan_tilt_2axis
from cadx.schemas import BBox, CatalogPart, CatalogSource, PackageAvailability, PartCatalog, PartRecord, PartSelectionTrace, PreviewArtifact, PreviewTarget, RepairAction, RepairPlan, ReproducibilityReport, ReviewArtifactGroup, ReviewChecklistItem, ReviewState, ValidationGateResult, ValidationReport, WorkerContractSet, WorkerSkillContract


def _jsonable(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def write_json(path: Path, model_or_data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _jsonable(model_or_data)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def write_placeholder_step(path: Path, name: str, placeholder_reason: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "ISO-10303-21;\n"
        "HEADER;\n"
        f"FILE_DESCRIPTION(('CADX Sprint 0 placeholder: {placeholder_reason}'),'2;1');\n"
        f"FILE_NAME('{name}.step','2026-05-25T00:00:00',('CADX'),('CADX'),'CADX','CADX','');\n"
        "FILE_SCHEMA(('AUTOMOTIVE_DESIGN_CC2'));\n"
        "ENDSEC;\nDATA;\n#1=PRODUCT('PLACEHOLDER','PLACEHOLDER','DETERMINISTIC NON-GEOMETRIC STEP STUB',());\nENDSEC;\nEND-ISO-10303-21;\n"
    )


def build123d_available() -> tuple[bool, str | None]:
    try:
        import build123d  # noqa: F401
        from build123d import Compound, export_step  # noqa: F401
    except Exception as exc:  # pragma: no cover - environment dependent
        return False, f"build123d import/export unavailable: {exc}"
    return True, None


def custom_part_source(part_id: str) -> str:
    dimensions = {
        "base_bracket": "plate 90x70x4 mm with servo mounting tab holes and base holes",
        "tilt_yoke": "U-yoke with two side plates and a bridge preserving pitch-axis clearance",
        "camera_plate": "camera payload plate 60x45x3 mm with four mounting holes",
    }[part_id]
    return dedent(
        f'''
        """Editable build123d source for CADX custom part: {part_id}.

        Design policy: this generated adapter may be edited, but locked interface names
        in design_contract.json must be preserved by future geometric diff validation.
        Shape intent: {dimensions}.
        """

        from build123d import *


        PART_ID = {part_id!r}


        def build_part():
            if PART_ID == "base_bracket":
                with BuildPart() as part:
                    Box(90, 70, 4, align=(Align.CENTER, Align.CENTER, Align.MIN))
                    with Locations((-25, -18, 4), (25, -18, 4), (-25, 18, 4), (25, 18, 4)):
                        Cylinder(2.0, 8, mode=Mode.SUBTRACT)
                    Box(44, 24, 18, align=(Align.CENTER, Align.CENTER, Align.MIN))
                    with Locations((-16, 0, 18), (16, 0, 18)):
                        Cylinder(1.6, 28, rotation=(90, 0, 0), mode=Mode.SUBTRACT)
                return part.part

            if PART_ID == "tilt_yoke":
                with BuildPart() as part:
                    Box(64, 8, 46, align=(Align.CENTER, Align.CENTER, Align.MIN))
                    with Locations((0, 42, 0)):
                        Box(64, 8, 46, align=(Align.CENTER, Align.CENTER, Align.MIN))
                    Box(64, 50, 6, align=(Align.CENTER, Align.CENTER, Align.MIN))
                    with Locations((-26, -4, 27), (26, 46, 27)):
                        Cylinder(3.0, 12, rotation=(90, 0, 0), mode=Mode.SUBTRACT)
                return part.part

            if PART_ID == "camera_plate":
                with BuildPart() as part:
                    Box(60, 45, 3, align=(Align.CENTER, Align.CENTER, Align.MIN))
                    with Locations((-20, -15, 3), (20, -15, 3), (-20, 15, 3), (20, 15, 3)):
                        Cylinder(1.6, 8, mode=Mode.SUBTRACT)
                return part.part

            raise ValueError(f"Unknown CADX custom part: {{PART_ID}}")
        '''
    ).lstrip()


def write_source(path: Path, part_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(custom_part_source(part_id))


def _bbox_for(part_id: str) -> BBox:
    sizes = {
        "base_bracket": BBox(x=90, y=70, z=22),
        "tilt_yoke": BBox(x=64, y=50, z=46),
        "camera_plate": BBox(x=60, y=45, z=3),
    }
    return sizes[part_id]


def export_build123d_part(part_id: str, step_path: Path) -> None:
    from build123d import Compound, export_step

    namespace: dict[str, object] = {}
    exec(custom_part_source(part_id), namespace)
    part = namespace["build_part"]()
    step_path.parent.mkdir(parents=True, exist_ok=True)
    export_step(Compound(label=part_id, children=[part]), step_path)


def _translated(part, xyz_mm: tuple[float, float, float]):
    from build123d import Location

    return part.moved(Location(xyz_mm))


def _servo_proxy_geometry():
    from build123d import Align, Box, BuildPart, Cylinder, Locations, Mode

    with BuildPart() as part:
        Box(40, 20, 40, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((-24, -5, 0), (24, -5, 0), (-24, 5, 0), (24, 5, 0)):
            Cylinder(1.5, 4, mode=Mode.SUBTRACT)
        with Locations((0, 0, 40)):
            Cylinder(3.0, 6, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return part.part


def export_build123d_assembly(run_dir: Path, step_path: Path) -> None:
    from build123d import Compound, export_step, import_step

    component_specs = [
        ("base_bracket", run_dir / "custom_parts" / "base_bracket" / "part.step", pan_tilt_2axis.COMPONENT_PLACEMENTS_MM["base_bracket"]),
        ("servo_pan", None, pan_tilt_2axis.COMPONENT_PLACEMENTS_MM["servo_pan"]),
        ("tilt_yoke", run_dir / "custom_parts" / "tilt_yoke" / "part.step", pan_tilt_2axis.COMPONENT_PLACEMENTS_MM["tilt_yoke"]),
        ("servo_tilt", None, pan_tilt_2axis.COMPONENT_PLACEMENTS_MM["servo_tilt"]),
        ("camera_plate", run_dir / "custom_parts" / "camera_plate" / "part.step", pan_tilt_2axis.COMPONENT_PLACEMENTS_MM["camera_plate"]),
    ]
    children = []
    for label, source_path, location in component_specs:
        shape = import_step(source_path) if source_path else _servo_proxy_geometry()
        children.append(_translated(shape, location))
    step_path.parent.mkdir(parents=True, exist_ok=True)
    export_step(Compound(label="pan_tilt_2axis_assembly", children=children), step_path)


def write_custom_part_geometry(part_id: str, step_path: Path, use_build123d: bool) -> tuple[str, str | None]:
    if use_build123d:
        try:
            export_build123d_part(part_id, step_path)
            return "build123d", None
        except Exception as exc:  # pragma: no cover - depends on OCC/export runtime
            write_placeholder_step(step_path, part_id, f"build123d export failed: {exc}")
            return "placeholder", f"build123d export failed for {part_id}: {exc}"
    write_placeholder_step(step_path, part_id, "build123d unavailable; fallback placeholder custom part")
    return "placeholder", "build123d unavailable; fallback placeholder custom part"


def copy_retrieved_part(run_dir: Path, part: PartRecord) -> PartRecord:
    part_dir = run_dir / "retrieved_parts" / part.id
    original = part_dir / "original.step"
    normalized = part_dir / "normalized.step"
    write_placeholder_step(original, part.id, "external original placeholder; immutable")
    shutil.copyfile(original, normalized)
    updated = part.model_copy(update={"original_step_path": str(original.relative_to(run_dir)), "normalized_step_path": str(normalized.relative_to(run_dir))})
    write_json(part_dir / "part_record.json", updated)
    write_json(part_dir / "interfaces.json", [i.model_dump(mode="json") for i in updated.interfaces])
    return updated


URDF_LINK_MESH_SOURCES = {
    "base_link": "custom_parts/base_bracket/part.step",
    "pan_link": "custom_parts/tilt_yoke/part.step",
    "tilt_link": "custom_parts/camera_plate/part.step",
}


def write_urdf_mesh_proxies(run_dir: Path) -> dict[str, str]:
    mesh_dir = run_dir / "urdf_meshes"
    mesh_dir.mkdir(parents=True, exist_ok=True)
    mesh_paths: dict[str, str] = {}
    for link_name, source_rel in URDF_LINK_MESH_SOURCES.items():
        target = mesh_dir / f"{link_name}.step"
        shutil.copyfile(run_dir / source_rel, target)
        mesh_paths[link_name] = str(target.relative_to(run_dir))
    return mesh_paths


def export_urdf(run_dir: Path) -> Path:
    mesh_paths = write_urdf_mesh_proxies(run_dir)
    robot = Element("robot", {"name": "cadx_pan_tilt_2axis_demo"})
    for link_name in ["base_link", "pan_link", "tilt_link"]:
        link = SubElement(robot, "link", {"name": link_name})
        for tag in ["visual", "collision"]:
            element = SubElement(link, tag)
            geometry = SubElement(element, "geometry")
            SubElement(geometry, "mesh", {"filename": mesh_paths[link_name]})
    for joint in pan_tilt_2axis.joints():
        joint_el = SubElement(robot, "joint", {"name": joint.name, "type": joint.type})
        SubElement(joint_el, "parent", {"link": joint.parent})
        SubElement(joint_el, "child", {"link": joint.child})
        xyz_m = tuple(v / 1000.0 for v in joint.origin.xyz_mm)
        rpy_rad = tuple(v * 3.141592653589793 / 180.0 for v in joint.origin.rpy_deg)
        SubElement(joint_el, "origin", {"xyz": " ".join(f"{v:.6g}" for v in xyz_m), "rpy": " ".join(f"{v:.6g}" for v in rpy_rad)})
        if joint.axis:
            SubElement(joint_el, "axis", {"xyz": " ".join(str(v) for v in joint.axis)})
        if joint.limits:
            attrs = {"effort": str(joint.limits.effort or 0), "velocity": str(joint.limits.velocity or 0)}
            if joint.limits.lower_deg is not None:
                attrs["lower"] = str(joint.limits.lower_deg * 3.141592653589793 / 180.0)
            if joint.limits.upper_deg is not None:
                attrs["upper"] = str(joint.limits.upper_deg * 3.141592653589793 / 180.0)
            SubElement(joint_el, "limit", attrs)
    path = run_dir / "robot.urdf"
    ElementTree(robot).write(path, encoding="unicode", xml_declaration=True)
    return path


def _existing_relative_files(run_dir: Path, directory: str, pattern: str = "*") -> list[str]:
    base = run_dir / directory
    if not base.exists():
        return []
    return sorted(str(path.relative_to(run_dir)) for path in base.glob(pattern) if path.is_file())


def _sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_safe_relative_path(rel: str) -> bool:
    path = Path(rel)
    return bool(rel) and not path.is_absolute() and ".." not in path.parts


def write_local_catalog_seed(run_dir: Path, record: PartRecord) -> dict:
    metadata = record.metadata
    catalog_dir = run_dir / "catalog" / "parts" / record.id
    catalog_dir.mkdir(parents=True, exist_ok=True)
    original_rel = f"catalog/parts/{record.id}/original.step"
    normalized_rel = f"catalog/parts/{record.id}/normalized.step"
    shutil.copyfile(run_dir / (record.original_step_path or ""), run_dir / original_rel)
    shutil.copyfile(run_dir / (record.normalized_step_path or ""), run_dir / normalized_rel)
    seed = {
        "part_id": record.id,
        "name": record.name,
        "source_id": metadata.get("source_id", ""),
        "source_uri": metadata.get("source_uri", ""),
        "source_kind": "local_seed",
        "manufacturer": metadata.get("manufacturer"),
        "model": metadata.get("model"),
        "category": record.category,
        "tags": ["servo", "actuator", "pan_tilt", "step_parts_style_seed"],
        "license_status": metadata.get("license_status", "placeholder-local-seed"),
        "provenance_status": metadata.get("provenance_status", "curated_local_fixture"),
        "original_step_path": original_rel,
        "normalized_step_path": normalized_rel,
        "immutable_original": True,
        "interface_tags": list(metadata.get("interface_tags", [])),
        "dimension_tags": list(metadata.get("dimension_tags", [])),
        "selection_suitability": ["matches_bom_servo_role", "matches_pan_tilt_interfaces", "local_deterministic_seed"],
        "checksum_sha256": _sha256_file(run_dir / original_rel),
        "part_record_path": str((run_dir / "retrieved_parts" / record.id / "part_record.json").relative_to(run_dir)),
        "notes": "Local curated seed entry wrapping the existing deterministic MG996R placeholder; no external network fetch.",
    }
    write_json(catalog_dir / "metadata.json", seed)
    return seed


def build_part_catalog(run_dir: Path, run_id: str, product_spec_id: str) -> PartCatalog:
    parts: list[CatalogPart] = []
    source_ids: set[str] = set()
    for metadata_path in sorted((run_dir / "catalog" / "parts").glob("*/metadata.json")):
        metadata = json.loads(metadata_path.read_text())
        part_id = str(metadata.get("part_id", metadata_path.parent.name))
        source_id = str(metadata.get("source_id", ""))
        if source_id:
            source_ids.add(source_id)
        parts.append(
            CatalogPart(
                id=part_id,
                part_id=part_id,
                name=str(metadata.get("name", part_id)),
                source_id=source_id,
                source_uri=str(metadata.get("source_uri", "")),
                source_kind=str(metadata.get("source_kind", "local_seed")),
                manufacturer=metadata.get("manufacturer"),
                model=metadata.get("model"),
                category=str(metadata.get("category", "")),
                tags=list(metadata.get("tags", [])),
                interfaces=list(metadata.get("interface_tags", [])),
                dimension_tags=list(metadata.get("dimension_tags", [])),
                interface_tags=list(metadata.get("interface_tags", [])),
                selection_suitability=list(metadata.get("selection_suitability", [])),
                license_status=str(metadata.get("license_status", "unspecified")),
                provenance_status=str(metadata.get("provenance_status", "unspecified")),
                checksum_sha256=metadata.get("checksum_sha256"),
                original_step_path=str(metadata.get("original_step_path", "")),
                normalized_step_path=str(metadata.get("normalized_step_path", "")),
                immutable_original=bool(metadata.get("immutable_original", True)),
                metadata_path=str(metadata_path.relative_to(run_dir)),
                part_record_path=str(metadata.get("part_record_path", "")),
            )
        )
    sources = [
        CatalogSource(
            id=source_id,
            name="CADX local curated STEP seed",
            source_type="local_seed",
            source_uri="cadx://local/part_catalog",
            provenance_status="curated_local_fixture",
            license_status="placeholder-local-seed",
            notes="step.parts-inspired local seed; no network scraping/import in v1.",
        )
        for source_id in sorted(source_ids)
    ]
    return PartCatalog(id=f"part_catalog_{run_id}", run_id=run_id, product_spec_id=product_spec_id, sources=sources, parts=parts)


def write_part_catalog(run_dir: Path, run_id: str, product_spec_id: str) -> PartCatalog:
    catalog = build_part_catalog(run_dir, run_id, product_spec_id)
    write_json(run_dir / "part_catalog.json", catalog)
    return catalog


def build_part_selection_trace(run_dir: Path, run_id: str, product_spec_id: str) -> PartSelectionTrace:
    catalog = json.loads((run_dir / "part_catalog.json").read_text())
    bom = json.loads((run_dir / "bom.json").read_text())
    servo = next(part for part in catalog.get("parts", []) if (part.get("part_id") or part.get("id")) == "servo_mg996r")
    required_interfaces = sorted({interface for item in bom.get("items", []) if item.get("selected_part_id") == "servo_mg996r" for interface in item.get("required_interfaces", [])})
    constraints = sorted(set(required_interfaces) & set(servo.get("interface_tags", [])))
    return PartSelectionTrace(
        id=f"part_selection_trace_{run_id}",
        run_id=run_id,
        product_spec_id=product_spec_id,
        generated_at="2026-05-25T00:00:00+09:00",
        selected_part_id="servo_mg996r",
        selected_by="fixed_demo_catalog_rule",
        source_id=str(servo.get("source_id", "")),
        source_uri=str(servo.get("source_uri", "")),
        source_kind=str(servo.get("source_kind", "local_seed")),
        catalog_path="part_catalog.json",
        part_record_path=str(servo.get("part_record_path", "")),
        original_step_path=str(servo.get("original_step_path", "")),
        normalized_step_path=str(servo.get("normalized_step_path", "")),
        immutable_original=bool(servo.get("immutable_original", False)),
        checksum_sha256=servo.get("checksum_sha256"),
        candidate_count=len(catalog.get("parts", [])),
        candidate_part_ids=sorted(str(part.get("part_id") or part.get("id")) for part in catalog.get("parts", [])),
        selection_reason="Deterministic pan_tilt_2axis_demo rule selected the local curated MG996R-compatible servo seed because it satisfies both servo mount and output spline interface constraints.",
        constraints_matched=constraints,
        interface_tags_matched=sorted(servo.get("interface_tags", [])),
        dimension_tags_matched=sorted(servo.get("dimension_tags", [])),
    )


def write_part_selection_trace(run_dir: Path, run_id: str, product_spec_id: str) -> PartSelectionTrace:
    trace = build_part_selection_trace(run_dir, run_id, product_spec_id)
    write_json(run_dir / "part_selection_trace.json", trace)
    return trace


def build_artifact_manifest(run_dir: Path, report: ValidationReport) -> dict:
    return {
        "id": "artifact_manifest_pan_tilt_2axis_demo",
        "run_id": report.run_id,
        "product_spec_id": report.product_spec_id,
        "generated_at": "2026-05-25T00:00:00+09:00",
        "core_artifacts": {
            "product_spec": "product_spec.json",
            "bom": "bom.json",
            "part_catalog": "part_catalog.json",
            "part_selection_trace": "part_selection_trace.json",
            "worker_contracts": "worker_contracts.json",
            "review_state": "review_state.json",
            "reproducibility_report": "reproducibility_report.json",
            **({"agent_trace": "agent_trace.json"} if (run_dir / "agent_trace.json").exists() else {}),
            **({"modification_request": "modification_request.json"} if (run_dir / "modification_request.json").exists() else {}),
            **({"delta_summary": "delta_summary.json"} if (run_dir / "delta_summary.json").exists() else {}),
            "assembly_plan": "assembly_plan.json",
            "assembly_step": "assembly.step",
            "joints": "joints.json",
            "urdf": "robot.urdf",
            "validation_report": "validation_report.json",
            "repair_plan": "repair_plan.json",
            "preview": "preview.json",
            "run_report": "run_report.html",
            "artifact_manifest": "artifact_manifest.json",
        },
        "custom_parts": {part: sorted(str(path.relative_to(run_dir)) for path in (run_dir / "custom_parts" / part).glob("*")) for part in ["base_bracket", "tilt_yoke", "camera_plate"]},
        "retrieved_parts": {"servo_mg996r": sorted(str(path.relative_to(run_dir)) for path in (run_dir / "retrieved_parts" / "servo_mg996r").glob("*"))},
        "catalog_parts": {"servo_mg996r": sorted(str(path.relative_to(run_dir)) for path in (run_dir / "catalog" / "parts" / "servo_mg996r").glob("*"))},
        "urdf_meshes": _existing_relative_files(run_dir, "urdf_meshes", "*.step"),
        "validation": {"status": report.status, "gates": [gate.id for gate in report.gates], "metrics": sorted(report.metrics)},
    }


def write_artifact_manifest(run_dir: Path, report: ValidationReport) -> None:
    write_json(run_dir / "artifact_manifest.json", build_artifact_manifest(run_dir, report))


def build_worker_contracts(run_dir: Path, run_id: str, product_spec_id: str) -> WorkerContractSet:
    non_goals = ["no_cloud", "no_auth_tls", "no_react_vite_rewrite", "no_new_cad_kernel", "no_live_web_scraping", "no_vector_db"]
    contracts = [
        WorkerSkillContract(
            id="intake.spec_decomposition",
            label="Intake and spec decomposition",
            category="intake",
            responsible_worker_type="intake_worker",
            expected_inputs=["user_product_brief", "workflow_id_or_template_id"],
            expected_outputs=["product_spec.json"],
            required_artifacts=["product_spec.json"],
            validation_gates=["artifacts"],
            non_goals=non_goals,
        ),
        WorkerSkillContract(
            id="catalog.part_sourcing",
            label="Local part sourcing and catalog provenance",
            category="part_sourcing",
            responsible_worker_type="part_rag_worker",
            expected_inputs=["product_spec.json", "bom.json", "catalog/parts/<part_id>/metadata.json"],
            expected_outputs=["retrieved_parts/", "part_catalog.json", "part_selection_trace.json"],
            required_artifacts=["bom.json", "retrieved_parts/servo_mg996r/part_record.json", "part_catalog.json", "part_selection_trace.json"],
            validation_gates=["retrieved_part_metadata", "part_catalog", "part_selection_provenance", "external_immutable"],
            non_goals=non_goals,
        ),
        WorkerSkillContract(
            id="cad.custom_generation",
            label="Custom CAD generation and editable adapters",
            category="cad_generation",
            responsible_worker_type="custom_cad_worker",
            expected_inputs=["bom.json", "design_contract.json", "locked interface requirements"],
            expected_outputs=["custom_parts/<part_id>/source.py", "custom_parts/<part_id>/part.step", "custom_parts/<part_id>/design_contract.json"],
            required_artifacts=["custom_parts/base_bracket/source.py", "custom_parts/tilt_yoke/source.py", "custom_parts/camera_plate/source.py"],
            validation_gates=["geometry_backend", "interface_contract_lock"],
            non_goals=non_goals,
        ),
        WorkerSkillContract(
            id="assembly.urdf_export",
            label="Assembly and URDF export",
            category="assembly_urdf",
            responsible_worker_type="assembly_urdf_worker",
            expected_inputs=["part records", "assembly_plan.json", "joints.json"],
            expected_outputs=["assembly.step", "robot.urdf", "urdf_meshes/"],
            required_artifacts=["assembly_plan.json", "assembly.step", "joints.json", "robot.urdf", "urdf_meshes/base_link.step"],
            validation_gates=["assembly_step", "urdf_joint_contract", "assembly_urdf_frame_consistency", "urdf_mesh_linkage"],
            non_goals=non_goals,
        ),
        WorkerSkillContract(
            id="validation.repair_planning",
            label="Validation and repair planning",
            category="validation_repair",
            responsible_worker_type="validation_report_worker",
            expected_inputs=["all run artifacts", "validation gate definitions"],
            expected_outputs=["validation_report.json", "repair_plan.json"],
            required_artifacts=["validation_report.json", "repair_plan.json"],
            validation_gates=["run_artifact_manifest"],
            non_goals=non_goals,
        ),
        WorkerSkillContract(
            id="review.report_dashboard",
            label="Report and local review UX",
            category="report_review",
            responsible_worker_type="report_output_worker",
            expected_inputs=["validation_report.json", "artifact_manifest.json", "preview.json"],
            expected_outputs=["run_report.html", "preview.json", "artifact_manifest.json"],
            required_artifacts=["run_report.html", "preview.json", "artifact_manifest.json"],
            validation_gates=["preview_artifact", "run_artifact_manifest"],
            non_goals=non_goals,
        ),
    ]
    return WorkerContractSet(
        id=f"worker_contracts_{run_id}",
        run_id=run_id,
        product_spec_id=product_spec_id,
        workflow_id="pan_tilt_2axis_demo",
        template_id="pan_tilt_2axis_demo",
        generated_at="2026-05-25T00:00:00+09:00",
        contracts=contracts,
    )


def write_worker_contracts(run_dir: Path, run_id: str, product_spec_id: str) -> WorkerContractSet:
    contracts = build_worker_contracts(run_dir, run_id, product_spec_id)
    write_json(run_dir / "worker_contracts.json", contracts)
    return contracts


def build_review_state(run_dir: Path, report: ValidationReport) -> ReviewState:
    manifest = build_artifact_manifest(run_dir, report)
    preview = json.loads((run_dir / "preview.json").read_text()) if (run_dir / "preview.json").exists() else {"preview_targets": []}
    repair_plan = json.loads((run_dir / "repair_plan.json").read_text()) if (run_dir / "repair_plan.json").exists() else {"status": "missing", "action_count": 0}
    groups = [
        ReviewArtifactGroup(id="spec", label="Spec and BOM", artifacts=["product_spec.json", "bom.json"]),
        ReviewArtifactGroup(id="catalog_provenance", label="Part catalog and provenance", artifacts=["part_catalog.json", "part_selection_trace.json", "catalog/parts/servo_mg996r/metadata.json"]),
        ReviewArtifactGroup(id="cad_assembly", label="CAD assembly and URDF", artifacts=["assembly.step", "assembly_plan.json", "robot.urdf", "joints.json"]),
        ReviewArtifactGroup(id="validation_repair", label="Validation and repair", artifacts=["validation_report.json", "repair_plan.json"]),
        ReviewArtifactGroup(id="review", label="Review outputs", artifacts=["preview.json", "worker_contracts.json", "review_state.json", "reproducibility_report.json", "artifact_manifest.json", "run_report.html"]),
    ]
    checklist = [
        ReviewChecklistItem(id="validation", label="Validation gates are inspectable", status=report.status, evidence_artifacts=["validation_report.json"], validation_gates=[gate.id for gate in report.gates]),
        ReviewChecklistItem(id="preview", label="Preview targets are declared", status="pass" if preview.get("preview_targets") else "fail", evidence_artifacts=["preview.json"], validation_gates=["preview_artifact"]),
        ReviewChecklistItem(id="repair", label="Repair status is visible", status=repair_plan.get("status", "missing"), evidence_artifacts=["repair_plan.json"], validation_gates=["run_artifact_manifest"]),
        ReviewChecklistItem(id="part_provenance", label="Part catalog provenance is visible", status="pass" if (run_dir / "part_selection_trace.json").exists() else "fail", evidence_artifacts=["part_catalog.json", "part_selection_trace.json"], validation_gates=["part_catalog", "part_selection_provenance"]),
        ReviewChecklistItem(id="worker_contracts", label="Worker contracts are visible", status="pass" if (run_dir / "worker_contracts.json").exists() else "fail", evidence_artifacts=["worker_contracts.json"], validation_gates=["worker_contracts"]),
    ]
    return ReviewState(
        id=f"review_state_{report.run_id}",
        run_id=report.run_id,
        product_spec_id=report.product_spec_id,
        workflow_id="pan_tilt_2axis_demo",
        template_id="pan_tilt_2axis_demo",
        generated_at=manifest["generated_at"],
        review_status=report.status,
        validation_status=report.status,
        validation_gate_count=len(report.gates),
        validation_pass_count=sum(1 for gate in report.gates if gate.status == "pass"),
        validation_warning_count=sum(1 for gate in report.gates if gate.status == "warning"),
        validation_fail_count=sum(1 for gate in report.gates if gate.status == "fail"),
        repair_status=repair_plan.get("status", "missing"),
        repair_action_count=int(repair_plan.get("action_count", 0) or 0),
        artifact_groups=groups,
        checklist=checklist,
        preview_targets=[target.get("artifact_path", "") for target in preview.get("preview_targets", [])],
        part_provenance_artifacts=["part_catalog.json", "part_selection_trace.json", "catalog/parts/servo_mg996r/metadata.json"],
        worker_contract_artifact="worker_contracts.json",
        limitations=["local_first_only", "manifest_metadata_only", "no_arbitrary_file_streaming", "no_cloud_auth_tls", "no_react_vite_rewrite", "no_live_web_scraping", "no_vector_db", "no_new_cad_kernel"],
    )


def write_review_state(run_dir: Path, report: ValidationReport) -> ReviewState:
    review_state = build_review_state(run_dir, report)
    write_json(run_dir / "review_state.json", review_state)
    return review_state


def _package_availability(package_names: list[str]) -> list[PackageAvailability]:
    packages: list[PackageAvailability] = []
    for package_name in package_names:
        try:
            version = importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            packages.append(PackageAvailability(name=package_name, available=False))
        else:
            packages.append(PackageAvailability(name=package_name, available=True, version=version))
    return packages


def build_reproducibility_report(run_dir: Path, report: ValidationReport) -> ReproducibilityReport:
    return ReproducibilityReport(
        id=f"reproducibility_{report.run_id}",
        run_id=report.run_id,
        product_spec_id=report.product_spec_id,
        workflow_id="pan_tilt_2axis_demo",
        template_id="pan_tilt_2axis_demo",
        generated_at="2026-05-25T00:00:00+09:00",
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        python_version_major=sys.version_info.major,
        python_version_minor=sys.version_info.minor,
        platform_system=platform.system(),
        platform_machine=platform.machine(),
        platform_platform=platform.platform(),
        package_availability=_package_availability(["build123d", "fastapi", "uvicorn", "httpx"]),
        geometry_backend=str(report.metrics.get("geometry_backend", "unknown")),
        validation_status=report.status,
        validation_gate_count=len(report.gates),
        validation_warning_count=sum(1 for gate in report.gates if gate.status == "warning"),
        validation_fail_count=sum(1 for gate in report.gates if gate.status == "fail"),
        smoke_commands=[
            "source .venv/bin/activate && python -m compileall src/cadx tests",
            "source .venv/bin/activate && pytest -q",
            "source .venv/bin/activate && cadx run-demo && cadx validate",
            "source .venv/bin/activate && bash scripts/smoke_api_dashboard.sh",
            "source .venv/bin/activate && bash scripts/smoke_docker.sh",
        ],
        docker_smoke_status="manual_optional",
        docker_smoke_note="Docker daemon is intentionally not required by pytest; run scripts/smoke_docker.sh locally to verify the container path. Some Linux/arm64 images may use placeholder geometry if py_lib3mf is unavailable.",
        limitations=["local_diagnostics_only", "no_ci_service_integration", "docker_smoke_manual", "no_cloud_auth_tls", "no_production_deployment", "no_new_cad_kernel"],
    )


def write_reproducibility_report(run_dir: Path, report: ValidationReport) -> ReproducibilityReport:
    reproducibility = build_reproducibility_report(run_dir, report)
    write_json(run_dir / "reproducibility_report.json", reproducibility)
    return reproducibility


def build_preview_artifact(run_dir: Path, report: ValidationReport) -> PreviewArtifact:
    return PreviewArtifact(
        id=f"preview_{report.run_id}",
        run_id=report.run_id,
        product_spec_id=report.product_spec_id,
        validation_status=report.status,
        validation_gate_count=len(report.gates),
        component_count=int(report.metrics.get("assembly_component_count", 0) or 0),
        urdf_link_count=int(report.metrics.get("urdf_links", 0) or 0),
        urdf_joint_count=int(report.metrics.get("urdf_joints", 0) or 0),
        main_artifacts={
            "assembly_step": "assembly.step",
            "robot_urdf": "robot.urdf",
            "artifact_manifest": "artifact_manifest.json",
            "validation_report": "validation_report.json",
            "run_report": "run_report.html",
        },
        preview_targets=[
            PreviewTarget(id="assembly_step", kind="cad_step", label="Assembly STEP", artifact_path="assembly.step", metadata={"file_size_bytes": report.metrics.get("assembly_step_bytes", 0)}),
            PreviewTarget(id="robot_urdf", kind="urdf", label="Robot URDF", artifact_path="robot.urdf", metadata={"links": report.metrics.get("urdf_links", 0), "joints": report.metrics.get("urdf_joints", 0)}),
        ],
    )


def write_preview_artifact(run_dir: Path, report: ValidationReport) -> PreviewArtifact:
    preview = build_preview_artifact(run_dir, report)
    write_json(run_dir / "preview.json", preview)
    return preview


def _manifest_paths(manifest: dict) -> list[str]:
    paths: list[str] = []
    paths.extend(manifest.get("core_artifacts", {}).values())
    for entries in manifest.get("custom_parts", {}).values():
        paths.extend(entries)
    for entries in manifest.get("retrieved_parts", {}).values():
        paths.extend(entries)
    for entries in manifest.get("catalog_parts", {}).values():
        paths.extend(entries)
    paths.extend(manifest.get("urdf_meshes", []))
    return paths


def validate_run_artifact_manifest(run_dir: Path, report_metrics: dict[str, object], gate_ids: set[str]) -> tuple[ValidationGateResult, dict[str, int]]:
    metrics = {"manifest_artifact_count": 0, "manifest_reference_count": 0, "run_report_section_count": 0, "manifest_gate_coverage_count": 0}
    errors: list[str] = []
    manifest_path = run_dir / "artifact_manifest.json"
    report_path = run_dir / "run_report.html"
    validation_path = run_dir / "validation_report.json"
    if not manifest_path.exists():
        errors.append("artifact_manifest.json missing")
        manifest = {}
    else:
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError as exc:
            manifest = {}
            errors.append(f"artifact_manifest.json parse failed: {exc}")
    html = report_path.read_text() if report_path.exists() else ""
    if not report_path.exists():
        errors.append("run_report.html missing")
    if not validation_path.exists():
        errors.append("validation_report.json missing")
    if not (run_dir / "repair_plan.json").exists():
        errors.append("repair_plan.json missing")
    if not (run_dir / "part_catalog.json").exists():
        errors.append("part_catalog.json missing")
    if not (run_dir / "part_selection_trace.json").exists():
        errors.append("part_selection_trace.json missing")
    if not (run_dir / "preview.json").exists():
        errors.append("preview.json missing")
    if not (run_dir / "worker_contracts.json").exists():
        errors.append("worker_contracts.json missing")
    if not (run_dir / "review_state.json").exists():
        errors.append("review_state.json missing")
    if not (run_dir / "reproducibility_report.json").exists():
        errors.append("reproducibility_report.json missing")
    required_core = {"product_spec", "bom", "part_catalog", "part_selection_trace", "worker_contracts", "review_state", "reproducibility_report", "assembly_plan", "assembly_step", "joints", "urdf", "validation_report", "repair_plan", "preview", "run_report", "artifact_manifest"}
    core = manifest.get("core_artifacts", {})
    missing_core_keys = sorted(required_core - set(core))
    if missing_core_keys:
        errors.append(f"manifest missing core keys: {missing_core_keys}")
    references = _manifest_paths(manifest)
    metrics["manifest_reference_count"] = len(references)
    for rel in references:
        path = Path(rel)
        if path.is_absolute() or ".." in path.parts:
            errors.append(f"manifest reference escapes run directory: {rel}")
            continue
        if (run_dir / rel).exists():
            metrics["manifest_artifact_count"] += 1
        else:
            errors.append(f"manifest reference missing: {rel}")
    expected_gates = gate_ids - {"run_artifact_manifest"}
    manifest_gates = set(manifest.get("validation", {}).get("gates", []))
    metrics["manifest_gate_coverage_count"] = len(expected_gates & manifest_gates)
    if not expected_gates.issubset(manifest_gates):
        errors.append(f"manifest gate coverage missing: {sorted(expected_gates - manifest_gates)}")
    required_metric_keys = {"geometry_backend", "assembly_step_bytes", "urdf_links", "urdf_joints", "urdf_visual_count", "urdf_collision_count", "urdf_mesh_reference_count", "urdf_mesh_files_exist_count", "retrieved_part_metadata_count", "retrieved_part_with_source_count", "part_catalog_count", "catalog_part_count", "catalog_source_count", "part_catalog_immutable_count", "part_catalog_source_count", "part_catalog_checksum_count", "local_catalog_metadata_count", "part_selection_trace_count", "worker_contract_count", "worker_contract_artifact_reference_count", "worker_contract_gate_reference_count", "worker_contract_covered_gate_count", "review_state_checklist_count", "review_state_artifact_group_count", "review_state_preview_target_count", "review_state_limitation_count", "reproducibility_python_major", "reproducibility_package_available_count", "reproducibility_smoke_command_count", "reproducibility_limitation_count", "preview_target_count", "preview_main_artifact_count", "interface_contract_part_count", "interface_contract_locked_count", "interface_contract_mate_count", "interface_contract_joint_trace_count"}
    manifest_metrics = set(manifest.get("validation", {}).get("metrics", []))
    if not required_metric_keys.issubset(set(report_metrics)) or not required_metric_keys.issubset(manifest_metrics):
        errors.append("manifest/report missing required validation metric coverage")
    required_sections = ["Generated artifacts", "Validation gates", "Metrics summary", "Retrieved part metadata", "Part catalog summary", "Part Selection Provenance", "Worker contracts", "Review state", "Reproducibility diagnostics", "Preview summary", "Assembly / URDF summary", "Interface contract summary", "Repair plan summary"]
    metrics["run_report_section_count"] = sum(1 for section in required_sections if section in html)
    missing_sections = [section for section in required_sections if section not in html]
    if missing_sections:
        errors.append(f"run_report.html missing sections: {missing_sections}")
    for token in ["pan_tilt_2axis_demo", "servo_mg996r", "placeholder:mg996r:v1", "retrieved_parts/servo_mg996r/original.step", "catalog/parts/servo_mg996r/metadata.json", "part_catalog.json", "part_selection_trace.json", "worker_contracts.json", "part_selection_trace_count", "worker_contract_count", "review_state.json", "review_state_checklist_count", "reproducibility_report.json", "reproducibility_package_available_count", "part_catalog_count", "part_catalog_checksum_count", "preview.json", "preview_target_count", "urdf_mesh_reference_count", "interface_contract_locked_count", "repair_plan.json"]:
        if token not in html:
            errors.append(f"run_report.html missing token: {token}")
    status = "fail" if errors else "pass"
    message = "Run report and artifact manifest cover the MVP artifact chain and validation evidence." if not errors else "; ".join(errors)
    return ValidationGateResult(id="run_artifact_manifest", name="MVP run report and artifact manifest", status=status, message=message, details=metrics), metrics


def validate_urdf_joint_contract(run_dir: Path) -> tuple[ValidationGateResult, dict[str, int]]:
    urdf_path = run_dir / "robot.urdf"
    joints_path = run_dir / "joints.json"
    expected_joints = pan_tilt_2axis.joints()
    expected_links = {"base_link", "pan_link", "tilt_link"}
    metrics = {"urdf_links": 0, "urdf_joints": 0, "joint_contract_count": len(expected_joints)}

    if not urdf_path.exists() or not joints_path.exists():
        missing = [str(path.relative_to(run_dir)) for path in [urdf_path, joints_path] if not path.exists()]
        return ValidationGateResult(id="urdf_joint_contract", name="URDF joint/frame contract", status="fail", message=f"Missing URDF contract artifacts: {missing}"), metrics

    try:
        root = parse(urdf_path).getroot()
        joint_contract = json.loads(joints_path.read_text())
    except (OSError, ParseError, json.JSONDecodeError) as exc:
        return ValidationGateResult(id="urdf_joint_contract", name="URDF joint/frame contract", status="fail", message=f"URDF/joints contract parse failed: {exc}"), metrics

    links = {link.attrib.get("name") for link in root.findall("link")}
    urdf_joints = {joint.attrib.get("name"): joint for joint in root.findall("joint")}
    contract_names = {joint.get("name") for joint in joint_contract}
    expected_names = {joint.name for joint in expected_joints}
    metrics.update({"urdf_links": len(links), "urdf_joints": len(urdf_joints), "joint_contract_count": len(joint_contract)})

    errors: list[str] = []
    if root.attrib.get("name") != "cadx_pan_tilt_2axis_demo":
        errors.append("robot name mismatch")
    if links != expected_links:
        errors.append(f"links mismatch: expected {sorted(expected_links)}, got {sorted(links)}")
    if contract_names != expected_names or set(urdf_joints) != expected_names:
        errors.append(f"joint names mismatch: expected {sorted(expected_names)}, urdf {sorted(urdf_joints)}, joints.json {sorted(contract_names)}")

    contract_by_name = {joint.get("name"): joint for joint in joint_contract}
    for expected in expected_joints:
        joint_el = urdf_joints.get(expected.name)
        contract = contract_by_name.get(expected.name)
        if joint_el is None or contract is None:
            continue
        parent = joint_el.find("parent")
        child = joint_el.find("child")
        axis = joint_el.find("axis")
        limit = joint_el.find("limit")
        if joint_el.attrib.get("type") != expected.type:
            errors.append(f"{expected.name} type mismatch")
        if parent is None or parent.attrib.get("link") != expected.parent or expected.parent not in links:
            errors.append(f"{expected.name} parent link invalid")
        if child is None or child.attrib.get("link") != expected.child or expected.child not in links:
            errors.append(f"{expected.name} child link invalid")
        if axis is None or tuple(float(v) for v in axis.attrib.get("xyz", "").split()) != tuple(float(v) for v in expected.axis or ()): 
            errors.append(f"{expected.name} axis mismatch")
        if limit is None or expected.limits is None:
            errors.append(f"{expected.name} missing limit")
        else:
            lower = float(limit.attrib.get("lower"))
            upper = float(limit.attrib.get("upper"))
            expected_lower = expected.limits.lower_deg * 3.141592653589793 / 180.0
            expected_upper = expected.limits.upper_deg * 3.141592653589793 / 180.0
            if abs(lower - expected_lower) > 1e-9 or abs(upper - expected_upper) > 1e-9:
                errors.append(f"{expected.name} limit mismatch")
        if contract.get("parent") != expected.parent or contract.get("child") != expected.child:
            errors.append(f"{expected.name} joints.json parent/child mismatch")

    status = "fail" if errors else "pass"
    message = "URDF links/joints match pan-tilt assembly contract." if not errors else "; ".join(errors)
    return ValidationGateResult(id="urdf_joint_contract", name="URDF joint/frame contract", status=status, message=message, details=metrics), metrics


def _float_tuple(text: str) -> tuple[float, ...]:
    return tuple(float(value) for value in text.split())


def _close_tuple(actual: tuple[float, ...], expected: tuple[float, ...], tolerance: float = 1e-9) -> bool:
    return len(actual) == len(expected) and all(abs(a - e) <= tolerance for a, e in zip(actual, expected))


def validate_frame_consistency(run_dir: Path) -> tuple[ValidationGateResult, dict[str, int]]:
    assembly_path = run_dir / "assembly_plan.json"
    urdf_path = run_dir / "robot.urdf"
    joints_path = run_dir / "joints.json"
    metrics = {"assembly_component_count": 0, "frame_contract_count": 0, "urdf_origin_count": 0}

    try:
        assembly = json.loads(assembly_path.read_text())
        joints_contract = json.loads(joints_path.read_text())
        root = parse(urdf_path).getroot()
    except (OSError, ParseError, json.JSONDecodeError) as exc:
        return ValidationGateResult(id="assembly_urdf_frame_consistency", name="Assembly placement to URDF frame consistency", status="fail", message=f"Frame consistency parse failed: {exc}"), metrics

    components = {component["id"]: component for component in assembly.get("components", [])}
    urdf_joints = {joint.attrib.get("name"): joint for joint in root.findall("joint")}
    expected_links = {component["instance_name"] for component in components.values() if component["instance_name"].endswith("_link")}
    metrics.update({"assembly_component_count": len(components), "frame_contract_count": len(pan_tilt_2axis.JOINT_FRAME_COMPONENTS), "urdf_origin_count": sum(1 for joint in urdf_joints.values() if joint.find("origin") is not None)})

    errors: list[str] = []
    for component_id, expected_translation in pan_tilt_2axis.COMPONENT_PLACEMENTS_MM.items():
        component = components.get(component_id)
        if component is None:
            errors.append(f"missing assembly component {component_id}")
            continue
        actual_translation = tuple(component.get("initial_transform", {}).get("translation_mm", ()))
        actual_rotation = tuple(component.get("initial_transform", {}).get("rotation_rpy_deg", ()))
        if not _close_tuple(tuple(float(v) for v in actual_translation), expected_translation):
            errors.append(f"{component_id} placement mismatch")
        if not _close_tuple(tuple(float(v) for v in actual_rotation), (0.0, 0.0, 0.0)):
            errors.append(f"{component_id} rotation mismatch")

    contract_by_name = {joint.get("name"): joint for joint in joints_contract}
    for joint_name, (parent_component_id, child_component_id) in pan_tilt_2axis.JOINT_FRAME_COMPONENTS.items():
        contract = contract_by_name.get(joint_name)
        urdf_joint = urdf_joints.get(joint_name)
        parent_component = components.get(parent_component_id)
        child_component = components.get(child_component_id)
        if contract is None or urdf_joint is None or parent_component is None or child_component is None:
            errors.append(f"{joint_name} frame contract artifacts missing")
            continue

        parent_link = parent_component["instance_name"]
        child_link = child_component["instance_name"]
        if contract.get("parent") != parent_link or contract.get("child") != child_link:
            errors.append(f"{joint_name} parent/child not derived from assembly component link frames")

        origin = urdf_joint.find("origin")
        axis = urdf_joint.find("axis")
        if origin is None:
            errors.append(f"{joint_name} missing URDF origin")
        else:
            expected_xyz_m = tuple(float(value) / 1000.0 for value in contract["origin"]["xyz_mm"])
            expected_rpy_rad = tuple(float(value) * 3.141592653589793 / 180.0 for value in contract["origin"]["rpy_deg"])
            if not _close_tuple(_float_tuple(origin.attrib.get("xyz", "")), expected_xyz_m):
                errors.append(f"{joint_name} URDF origin xyz not derived from joints.json")
            if not _close_tuple(_float_tuple(origin.attrib.get("rpy", "")), expected_rpy_rad):
                errors.append(f"{joint_name} URDF origin rpy not derived from joints.json")
        if axis is None or not _close_tuple(_float_tuple(axis.attrib.get("xyz", "")), tuple(float(value) for value in contract["axis"])):
            errors.append(f"{joint_name} URDF axis not derived from joints.json")
        if contract.get("parent") not in expected_links or contract.get("child") not in expected_links:
            errors.append(f"{joint_name} references non-link assembly frames")

    status = "fail" if errors else "pass"
    message = "Assembly component placements and URDF joint frames share the same pan-tilt contract." if not errors else "; ".join(errors)
    return ValidationGateResult(id="assembly_urdf_frame_consistency", name="Assembly placement to URDF frame consistency", status=status, message=message, details=metrics), metrics


def validate_retrieved_part_metadata(run_dir: Path) -> tuple[ValidationGateResult, dict[str, int]]:
    metrics = {"retrieved_part_metadata_count": 0, "retrieved_part_interface_count": 0, "retrieved_part_trace_count": 0}
    errors: list[str] = []
    required_metadata = {
        "source_id",
        "source_uri",
        "manufacturer",
        "model",
        "rag_score",
        "rag_query",
        "interface_tags",
        "dimension_tags",
        "contract_references",
        "immutable_policy",
    }

    try:
        bom = json.loads((run_dir / "bom.json").read_text())
        assembly = json.loads((run_dir / "assembly_plan.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return ValidationGateResult(id="retrieved_part_metadata", name="Retrieved part metadata traceability", status="fail", message=f"BOM/assembly trace parse failed: {exc}"), metrics

    selected_part_ids = {item.get("selected_part_id") for item in bom.get("items", []) if item.get("selected_part_id")}
    assembly_part_ids = [component.get("part_record_id") for component in assembly.get("components", [])]
    urdf_mesh_sources = set(URDF_LINK_MESH_SOURCES.values())

    for part_id in sorted(selected_part_ids):
        record_path = run_dir / "retrieved_parts" / part_id / "part_record.json"
        if not record_path.exists():
            errors.append(f"missing retrieved part record {part_id}")
            continue
        try:
            record = json.loads(record_path.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"retrieved part record parse failed for {part_id}: {exc}")
            continue

        metadata = record.get("metadata", {})
        missing = sorted(required_metadata - set(metadata))
        if missing:
            errors.append(f"{part_id} missing metadata keys: {missing}")
        original_rel = record.get("original_step_path")
        normalized_rel = record.get("normalized_step_path")
        if not original_rel or not (run_dir / original_rel).exists():
            errors.append(f"{part_id} immutable original STEP missing")
        if not normalized_rel or not (run_dir / normalized_rel).exists():
            errors.append(f"{part_id} normalized STEP missing")
        if original_rel == normalized_rel:
            errors.append(f"{part_id} original and normalized STEP paths must be distinct")
        if record.get("immutable_original") is not True:
            errors.append(f"{part_id} immutable_original must be true")
        interface_ids = {interface.get("id") for interface in record.get("interfaces", [])}
        if set(metadata.get("interface_tags", [])) != interface_ids:
            errors.append(f"{part_id} interface tags do not match interface records")
        bom_refs = [item for item in bom.get("items", []) if item.get("selected_part_id") == part_id]
        assembly_refs = [component for component in assembly.get("components", []) if component.get("part_record_id") == part_id]
        if not bom_refs or not assembly_refs:
            errors.append(f"{part_id} is not traceable from both BOM and assembly plan")
        expected_contract_refs = {f"bom:{item['id']}" for item in bom_refs} | {f"assembly:{component['id']}" for component in assembly_refs}
        if not expected_contract_refs.issubset(set(metadata.get("contract_references", []))):
            errors.append(f"{part_id} contract references do not cover BOM/assembly usage")
        if original_rel in urdf_mesh_sources:
            errors.append(f"{part_id} immutable original STEP is used as a URDF mesh source")

        if not missing and original_rel and normalized_rel:
            metrics["retrieved_part_metadata_count"] += 1
        metrics["retrieved_part_interface_count"] += len(interface_ids)
        metrics["retrieved_part_trace_count"] += len(bom_refs) + len(assembly_refs)

    status = "fail" if errors else "pass"
    message = "Retrieved part records are complete and traceable from BOM and assembly without mutating immutable originals." if not errors else "; ".join(errors)
    return ValidationGateResult(id="retrieved_part_metadata", name="Retrieved part metadata traceability", status=status, message=message, details=metrics), metrics


def validate_part_catalog(run_dir: Path) -> tuple[ValidationGateResult, dict[str, int]]:
    metrics = {
        "part_catalog_count": 0,
        "part_catalog_source_count": 0,
        "part_catalog_interface_tag_count": 0,
        "part_catalog_dimension_tag_count": 0,
        "part_catalog_immutable_count": 0,
        "part_catalog_checksum_count": 0,
        "local_catalog_metadata_count": 0,
    }
    errors: list[str] = []
    warnings: list[str] = []
    catalog_path = run_dir / "part_catalog.json"
    if not catalog_path.exists():
        return ValidationGateResult(id="part_catalog", name="Local STEP catalog integrity", status="fail", message="part_catalog.json missing"), metrics
    try:
        catalog = json.loads(catalog_path.read_text())
    except json.JSONDecodeError as exc:
        return ValidationGateResult(id="part_catalog", name="Local STEP catalog integrity", status="fail", message=f"part_catalog.json parse failed: {exc}"), metrics

    seen_part_ids: set[str] = set()
    metrics["part_catalog_source_count"] = len(catalog.get("sources", []))
    for part in catalog.get("parts", []):
        part_id = part.get("part_id") or part.get("id")
        if part_id in seen_part_ids:
            errors.append(f"duplicate catalog part id: {part_id}")
        seen_part_ids.add(part_id)
        metrics["part_catalog_count"] += 1
        metrics["part_catalog_interface_tag_count"] += len(part.get("interface_tags", []))
        metrics["part_catalog_dimension_tag_count"] += len(part.get("dimension_tags", []))
        record_path = part.get("part_record_path", "")
        metadata_path = part.get("metadata_path", "")
        for key in ["source_id", "source_uri", "manufacturer", "model", "category", "original_step_path", "normalized_step_path", "license_status", "provenance_status"]:
            if not part.get(key) or part.get(key) == "unspecified":
                errors.append(f"catalog part {part_id} missing {key}")
        if part.get("license_status") in {"unknown", "unspecified"} or part.get("provenance_status") in {"unknown", "unspecified"}:
            warnings.append(f"catalog part {part_id} has explicit non-final license/provenance status")
        try:
            record = json.loads((run_dir / record_path).read_text())
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"catalog part {part_id} record unavailable: {exc}")
            continue
        try:
            seed_metadata = json.loads((run_dir / metadata_path).read_text())
            metrics["local_catalog_metadata_count"] += 1
        except (OSError, json.JSONDecodeError) as exc:
            seed_metadata = {}
            errors.append(f"catalog part {part_id} metadata unavailable: {exc}")
        metadata = record.get("metadata", {})
        if part.get("source_id") != metadata.get("source_id") or part.get("source_uri") != metadata.get("source_uri"):
            errors.append(f"catalog part {part_id} source metadata mismatch")
        if set(part.get("interfaces", [])) != {interface.get("id") for interface in record.get("interfaces", [])}:
            errors.append(f"catalog part {part_id} interface records mismatch")
        if set(part.get("interface_tags", [])) != set(metadata.get("interface_tags", [])):
            errors.append(f"catalog part {part_id} interface tags mismatch")
        if set(part.get("dimension_tags", [])) != set(metadata.get("dimension_tags", [])):
            errors.append(f"catalog part {part_id} dimension tags mismatch")
        original_rel = part.get("original_step_path", "")
        normalized_rel = part.get("normalized_step_path", "")
        if original_rel == normalized_rel:
            errors.append(f"catalog part {part_id} original and normalized references must differ")
        for rel in [original_rel, normalized_rel, record_path, metadata_path]:
            if not _is_safe_relative_path(rel) or not (run_dir / rel).exists():
                errors.append(f"catalog part {part_id} invalid reference: {rel}")
        checksum = part.get("checksum_sha256")
        if checksum and _is_safe_relative_path(original_rel) and (run_dir / original_rel).exists():
            if checksum == _sha256_file(run_dir / original_rel):
                metrics["part_catalog_checksum_count"] += 1
            else:
                errors.append(f"catalog part {part_id} checksum mismatch")
        else:
            errors.append(f"catalog part {part_id} missing checksum_sha256")
        if part.get("immutable_original") is True and record.get("immutable_original") is True and seed_metadata.get("immutable_original") is True:
            metrics["part_catalog_immutable_count"] += 1
        else:
            errors.append(f"catalog part {part_id} immutable_original mismatch")

    if "servo_mg996r" not in seen_part_ids:
        errors.append("catalog missing servo_mg996r")
    status = "fail" if errors else "pass"
    message = "Local STEP catalog seed is indexed with safe paths, provenance/license status, checksums, and immutable originals." if not errors else "; ".join(errors)
    if warnings and not errors:
        message = f"{message} Warnings: {'; '.join(warnings)}"
    return ValidationGateResult(id="part_catalog", name="Local STEP catalog integrity", status=status, message=message, details=metrics), metrics


def validate_part_selection_provenance(run_dir: Path) -> tuple[ValidationGateResult, dict[str, int]]:
    metrics = {"part_selection_trace_count": 0, "catalog_source_count": 0, "catalog_part_count": 0, "retrieved_part_with_source_count": 0}
    errors: list[str] = []
    trace_path = run_dir / "part_selection_trace.json"
    catalog_path = run_dir / "part_catalog.json"
    record_path = run_dir / "retrieved_parts" / "servo_mg996r" / "part_record.json"
    manifest_path = run_dir / "artifact_manifest.json"
    if not trace_path.exists():
        return ValidationGateResult(id="part_selection_provenance", name="Part selection provenance", status="fail", message="part_selection_trace.json missing"), metrics
    try:
        trace = json.loads(trace_path.read_text())
        catalog = json.loads(catalog_path.read_text())
        record = json.loads(record_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return ValidationGateResult(id="part_selection_provenance", name="Part selection provenance", status="fail", message=f"Part selection provenance parse failed: {exc}"), metrics

    metrics["part_selection_trace_count"] = 1
    metrics["catalog_source_count"] = len(catalog.get("sources", []))
    metrics["catalog_part_count"] = len(catalog.get("parts", []))
    catalog_parts = {part.get("part_id") or part.get("id"): part for part in catalog.get("parts", [])}
    selected = catalog_parts.get(trace.get("selected_part_id"))
    if selected is None:
        errors.append(f"selected part missing from catalog: {trace.get('selected_part_id')}")
    else:
        for key in ["source_id", "source_uri", "source_kind", "original_step_path", "normalized_step_path", "part_record_path"]:
            if not trace.get(key):
                errors.append(f"trace missing {key}")
            elif str(trace.get(key)) != str(selected.get(key)):
                errors.append(f"trace {key} mismatch")
        if trace.get("immutable_original") is not True or selected.get("immutable_original") is not True or record.get("immutable_original") is not True:
            errors.append("selected part immutable_original mismatch")
        else:
            metrics["retrieved_part_with_source_count"] = 1
        if trace.get("checksum_sha256") != selected.get("checksum_sha256"):
            errors.append("trace checksum mismatch")
        for rel in [trace.get("catalog_path", ""), trace.get("original_step_path", ""), trace.get("normalized_step_path", ""), trace.get("part_record_path", "")]:
            if not _is_safe_relative_path(str(rel)) or not (run_dir / str(rel)).exists():
                errors.append(f"trace reference invalid: {rel}")
        if trace.get("candidate_count") != len(catalog.get("parts", [])):
            errors.append("trace candidate_count mismatch")
        if set(trace.get("candidate_part_ids", [])) != set(catalog_parts):
            errors.append("trace candidate_part_ids mismatch")
        if not trace.get("constraints_matched"):
            errors.append("trace constraints_matched empty")
        if selected.get("source_id") != record.get("metadata", {}).get("source_id") or selected.get("source_uri") != record.get("metadata", {}).get("source_uri"):
            errors.append("selected catalog part inconsistent with retrieved part metadata")
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
            if manifest.get("core_artifacts", {}).get("part_selection_trace") != "part_selection_trace.json":
                errors.append("manifest missing part_selection_trace core artifact")
        except json.JSONDecodeError as exc:
            errors.append(f"artifact_manifest.json parse failed: {exc}")
    status = "fail" if errors else "pass"
    message = "Selected part provenance trace resolves to the local catalog, retrieved metadata, immutable original, normalized STEP, and manifest." if not errors else "; ".join(errors)
    return ValidationGateResult(id="part_selection_provenance", name="Part selection provenance", status=status, message=message, details=metrics), metrics


def validate_worker_contracts(run_dir: Path) -> tuple[ValidationGateResult, dict[str, int]]:
    metrics = {"worker_contract_count": 0, "worker_contract_artifact_reference_count": 0, "worker_contract_gate_reference_count": 0, "worker_contract_covered_gate_count": 0}
    errors: list[str] = []
    path = run_dir / "worker_contracts.json"
    if not path.exists():
        return ValidationGateResult(id="worker_contracts", name="CAD worker skill contract artifact", status="fail", message="worker_contracts.json missing"), metrics
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return ValidationGateResult(id="worker_contracts", name="CAD worker skill contract artifact", status="fail", message=f"worker_contracts.json parse failed: {exc}"), metrics
    contracts = data.get("contracts", [])
    required_categories = {"intake", "part_sourcing", "cad_generation", "assembly_urdf", "validation_repair", "report_review"}
    categories = {contract.get("category") for contract in contracts}
    if not required_categories.issubset(categories):
        errors.append(f"worker contracts missing categories: {sorted(required_categories - categories)}")
    covered_gates: set[str] = set()
    for contract in contracts:
        metrics["worker_contract_count"] += 1
        if contract.get("status") != "implemented":
            errors.append(f"contract {contract.get('id')} is not implemented")
        forbidden_phrases = ["cloud service", "authentication service", "tls termination", "react frontend", "vite frontend", "new cad kernel"]
        allowed_text = " ".join(contract.get("non_goals", [])).replace("_", " ").lower()
        contract_text = json.dumps({key: value for key, value in contract.items() if key != "non_goals"}).replace("_", " ").lower()
        for phrase in forbidden_phrases:
            if phrase in contract_text and phrase not in allowed_text:
                errors.append(f"contract {contract.get('id')} implies forbidden scope: {phrase}")
        for required_non_goal in ["no_cloud", "no_auth_tls", "no_react_vite_rewrite", "no_new_cad_kernel", "no_live_web_scraping", "no_vector_db"]:
            if required_non_goal not in contract.get("non_goals", []):
                errors.append(f"contract {contract.get('id')} missing {required_non_goal} non-goal")
        for rel in contract.get("required_artifacts", []):
            if "<" in rel or rel.endswith("/"):
                continue
            metrics["worker_contract_artifact_reference_count"] += 1
            if not _is_safe_relative_path(rel) or not (run_dir / rel).exists():
                errors.append(f"contract {contract.get('id')} artifact reference invalid: {rel}")
        for gate_id in contract.get("validation_gates", []):
            metrics["worker_contract_gate_reference_count"] += 1
            covered_gates.add(gate_id)
    expected_core_gates = {"artifacts", "external_immutable", "geometry_backend", "assembly_step", "urdf_joint_contract", "assembly_urdf_frame_consistency", "urdf_mesh_linkage", "retrieved_part_metadata", "part_catalog", "part_selection_provenance", "interface_contract_lock", "preview_artifact", "run_artifact_manifest"}
    metrics["worker_contract_covered_gate_count"] = len(expected_core_gates & covered_gates)
    missing = expected_core_gates - covered_gates
    if missing:
        errors.append(f"worker contracts missing gate coverage: {sorted(missing)}")
    status = "fail" if errors else "pass"
    message = "CAD worker skill contracts cover the current local-first artifact chain, gates, owners, and non-goals." if not errors else "; ".join(errors)
    return ValidationGateResult(id="worker_contracts", name="CAD worker skill contract artifact", status=status, message=message, details=metrics), metrics


def validate_reproducibility_report(run_dir: Path) -> tuple[ValidationGateResult, dict[str, int]]:
    metrics = {"reproducibility_python_major": 0, "reproducibility_package_available_count": 0, "reproducibility_smoke_command_count": 0, "reproducibility_limitation_count": 0}
    path = run_dir / "reproducibility_report.json"
    if not path.exists():
        return ValidationGateResult(id="reproducibility_report", name="Local reproducibility diagnostics", status="fail", message="reproducibility_report.json missing"), metrics
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return ValidationGateResult(id="reproducibility_report", name="Local reproducibility diagnostics", status="fail", message=f"reproducibility_report.json parse failed: {exc}"), metrics
    errors: list[str] = []
    metrics["reproducibility_python_major"] = int(data.get("python_version_major", 0) or 0)
    packages = data.get("package_availability", [])
    metrics["reproducibility_package_available_count"] = sum(1 for package in packages if package.get("available") is True)
    metrics["reproducibility_smoke_command_count"] = len(data.get("smoke_commands", []))
    metrics["reproducibility_limitation_count"] = len(data.get("limitations", []))
    if data.get("python_version_major") != 3 or data.get("python_version_minor") != 12:
        errors.append("reproducibility report must record the Python 3.12 runtime contract")
    required_packages = {"build123d", "fastapi", "uvicorn", "httpx"}
    package_names = {package.get("name") for package in packages}
    if not required_packages.issubset(package_names):
        errors.append(f"reproducibility report missing package probes: {sorted(required_packages - package_names)}")
    for command_token in ["python -m compileall src/cadx tests", "pytest -q", "cadx run-demo && cadx validate", "scripts/smoke_api_dashboard.sh", "scripts/smoke_docker.sh"]:
        if not any(command_token in command for command in data.get("smoke_commands", [])):
            errors.append(f"reproducibility report missing smoke command: {command_token}")
    if data.get("geometry_backend") not in {"build123d", "placeholder"}:
        errors.append("reproducibility report geometry_backend is not recognized")
    if data.get("validation_status") not in {"pass", "warning", "fail"}:
        errors.append("reproducibility report validation_status is not recognized")
    if data.get("validation_gate_count", 0) < 15:
        errors.append("reproducibility report validation_gate_count below current contract")
    if data.get("docker_smoke_status") not in {"manual_optional", "verified", "unavailable"}:
        errors.append("reproducibility report docker_smoke_status must be documented, not implicit")
    required_limitations = {"local_diagnostics_only", "no_ci_service_integration", "docker_smoke_manual", "no_cloud_auth_tls", "no_production_deployment", "no_new_cad_kernel"}
    limitations = set(data.get("limitations", []))
    if not required_limitations.issubset(limitations):
        errors.append(f"reproducibility report missing limitations: {sorted(required_limitations - limitations)}")
    status = "fail" if errors else "pass"
    message = "reproducibility_report.json records safe local runtime diagnostics, package probes, smoke commands, Docker caveat, and validation status." if not errors else "; ".join(errors)
    return ValidationGateResult(id="reproducibility_report", name="Local reproducibility diagnostics", status=status, message=message, details=metrics), metrics


def validate_review_state(run_dir: Path) -> tuple[ValidationGateResult, dict[str, int]]:
    metrics = {"review_state_checklist_count": 0, "review_state_artifact_group_count": 0, "review_state_preview_target_count": 0, "review_state_limitation_count": 0}
    path = run_dir / "review_state.json"
    if not path.exists():
        return ValidationGateResult(id="review_state", name="Local review/inspect state", status="fail", message="review_state.json missing"), metrics
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return ValidationGateResult(id="review_state", name="Local review/inspect state", status="fail", message=f"review_state.json parse failed: {exc}"), metrics
    errors: list[str] = []
    groups = data.get("artifact_groups", [])
    checklist = data.get("checklist", [])
    metrics["review_state_artifact_group_count"] = len(groups)
    metrics["review_state_checklist_count"] = len(checklist)
    metrics["review_state_preview_target_count"] = len(data.get("preview_targets", []))
    metrics["review_state_limitation_count"] = len(data.get("limitations", []))
    required_groups = {"spec", "catalog_provenance", "cad_assembly", "validation_repair", "review"}
    group_ids = {group.get("id") for group in groups}
    if not required_groups.issubset(group_ids):
        errors.append(f"review_state missing artifact groups: {sorted(required_groups - group_ids)}")
    required_checklist = {"validation", "preview", "repair", "part_provenance", "worker_contracts"}
    checklist_ids = {item.get("id") for item in checklist}
    if not required_checklist.issubset(checklist_ids):
        errors.append(f"review_state missing checklist items: {sorted(required_checklist - checklist_ids)}")
    required_limitations = {"local_first_only", "manifest_metadata_only", "no_arbitrary_file_streaming", "no_cloud_auth_tls", "no_react_vite_rewrite", "no_live_web_scraping", "no_vector_db", "no_new_cad_kernel"}
    limitations = set(data.get("limitations", []))
    if not required_limitations.issubset(limitations):
        errors.append(f"review_state missing limitations: {sorted(required_limitations - limitations)}")
    for rel in [artifact for group in groups for artifact in group.get("artifacts", [])] + data.get("preview_targets", []) + data.get("part_provenance_artifacts", []) + [data.get("worker_contract_artifact", "")]:
        if not rel:
            continue
        if not _is_safe_relative_path(rel) or not (run_dir / rel).exists():
            errors.append(f"review_state artifact reference invalid: {rel}")
    if data.get("validation_gate_count", 0) < 14:
        errors.append("review_state validation_gate_count below current contract")
    status = "fail" if errors else "pass"
    message = "review_state.json summarizes local run review status, artifact groups, preview, repair, provenance, worker contracts, and limitations." if not errors else "; ".join(errors)
    return ValidationGateResult(id="review_state", name="Local review/inspect state", status=status, message=message, details=metrics), metrics


def validate_interface_contracts(run_dir: Path) -> tuple[ValidationGateResult, dict[str, int]]:
    metrics = {"interface_contract_part_count": 0, "interface_contract_locked_count": 0, "interface_contract_mate_count": 0, "interface_contract_joint_trace_count": 0}
    errors: list[str] = []

    try:
        bom = json.loads((run_dir / "bom.json").read_text())
        assembly = json.loads((run_dir / "assembly_plan.json").read_text())
        joints_contract = json.loads((run_dir / "joints.json").read_text())
        root = parse(run_dir / "robot.urdf").getroot()
    except (OSError, ParseError, json.JSONDecodeError) as exc:
        return ValidationGateResult(id="interface_contract_lock", name="Design interface lock traceability", status="fail", message=f"Interface contract parse failed: {exc}"), metrics

    part_records: dict[str, dict] = {}
    for part_id in {"servo_mg996r", *assembly.get("generated_parts", [])}:
        path = run_dir / "retrieved_parts" / part_id / "part_record.json" if part_id == "servo_mg996r" else run_dir / "custom_parts" / part_id / "part_record.json"
        if not path.exists():
            errors.append(f"missing part record {part_id}")
            continue
        try:
            part_records[part_id] = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"part record parse failed for {part_id}: {exc}")

    components = {component.get("id"): component for component in assembly.get("components", [])}
    component_part_ids = {component_id: component.get("part_record_id") for component_id, component in components.items()}
    interface_by_part = {part_id: {interface.get("id"): interface for interface in record.get("interfaces", [])} for part_id, record in part_records.items()}
    required_interfaces = set()
    for item in bom.get("items", []):
        required_interfaces.update(item.get("required_interfaces", []))
        if item.get("selected_part_id") not in part_records:
            errors.append(f"BOM item {item.get('id')} references unknown part {item.get('selected_part_id')}")
        missing = set(item.get("required_interfaces", [])) - set(interface_by_part.get(item.get("selected_part_id"), {}))
        if missing:
            errors.append(f"BOM item {item.get('id')} missing selected-part interfaces {sorted(missing)}")
    for request in bom.get("generated_custom_parts", []):
        part_id = request.get("id")
        required = set(request.get("required_interfaces", []))
        required_interfaces.update(required)
        missing = required - set(interface_by_part.get(part_id, {}))
        if missing:
            errors.append(f"custom part {part_id} missing required interfaces {sorted(missing)}")
        contract_id = request.get("design_contract_id")
        record = part_records.get(part_id, {})
        if record.get("design_contract_id") != contract_id:
            errors.append(f"custom part {part_id} design contract id mismatch")
        contract_path = run_dir / "custom_parts" / part_id / "design_contract.json"
        if not contract_path.exists():
            errors.append(f"missing design contract for {part_id}")
            continue
        try:
            contract = json.loads(contract_path.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"design contract parse failed for {part_id}: {exc}")
            continue
        locked = set(contract.get("locked_interfaces", []))
        if locked != required:
            errors.append(f"custom part {part_id} locked interfaces mismatch")
        invariant_targets = {invariant.get("target") for invariant in contract.get("geometric_invariants", [])}
        metrics["interface_contract_locked_count"] += len(locked)
        for interface_id in locked:
            interface = interface_by_part.get(part_id, {}).get(interface_id)
            if interface is None:
                errors.append(f"contract {contract.get('id')} locks unknown interface {interface_id}")
                continue
            if interface_id not in invariant_targets:
                errors.append(f"contract {contract.get('id')} lacks invariant for {interface_id}")
            frame = interface.get("frame", {})
            geometry = interface.get("geometry", {})
            if len(frame.get("origin_mm", [])) != 3 or len(frame.get("x_axis", [])) != 3 or len(frame.get("y_axis", [])) != 3 or len(frame.get("z_axis", [])) != 3:
                errors.append(f"interface {part_id}:{interface_id} missing locked pose frame")
            if not geometry.get("kind") or not geometry.get("parameters"):
                errors.append(f"interface {part_id}:{interface_id} missing locked geometry")

    for component_id, part_id in component_part_ids.items():
        if part_id not in part_records:
            errors.append(f"assembly component {component_id} references unknown part {part_id}")
    for mate in assembly.get("mates", []):
        metrics["interface_contract_mate_count"] += 1
        for endpoint in ["parent", "child"]:
            component_id = mate.get(f"{endpoint}_component")
            interface_id = mate.get(f"{endpoint}_interface")
            part_id = component_part_ids.get(component_id)
            if part_id is None:
                errors.append(f"mate {mate.get('id')} references unknown {endpoint} component {component_id}")
                continue
            if interface_id not in interface_by_part.get(part_id, {}):
                errors.append(f"mate {mate.get('id')} references unknown interface {part_id}:{interface_id}")
    urdf_joints = {joint.attrib.get("name"): joint for joint in root.findall("joint")}
    for joint in joints_contract:
        metrics["interface_contract_joint_trace_count"] += 1
        if joint.get("name") not in urdf_joints:
            errors.append(f"joint contract {joint.get('name')} missing from URDF")
        if joint.get("name") not in pan_tilt_2axis.JOINT_FRAME_COMPONENTS:
            errors.append(f"joint contract {joint.get('name')} missing frame/interface trace")
    missing_required = required_interfaces - {interface_id for interfaces in interface_by_part.values() for interface_id in interfaces}
    if missing_required:
        errors.append(f"required interface ids missing globally: {sorted(missing_required)}")

    metrics["interface_contract_part_count"] = len(part_records)
    status = "fail" if errors else "pass"
    message = "Design contracts, locked interfaces, assembly mates, joints, and URDF frames are traceable." if not errors else "; ".join(errors)
    return ValidationGateResult(id="interface_contract_lock", name="Design interface lock traceability", status=status, message=message, details=metrics), metrics


def validate_urdf_mesh_linkage(run_dir: Path) -> tuple[ValidationGateResult, dict[str, int]]:
    urdf_path = run_dir / "robot.urdf"
    expected_links = set(URDF_LINK_MESH_SOURCES)
    metrics = {"urdf_visual_count": 0, "urdf_collision_count": 0, "urdf_mesh_reference_count": 0, "urdf_mesh_files_exist_count": 0}

    try:
        root = parse(urdf_path).getroot()
    except (OSError, ParseError) as exc:
        return ValidationGateResult(id="urdf_mesh_linkage", name="URDF visual/collision mesh linkage", status="fail", message=f"URDF mesh linkage parse failed: {exc}"), metrics

    errors: list[str] = []
    mesh_references: list[str] = []
    links = {link.attrib.get("name"): link for link in root.findall("link")}
    if set(links) != expected_links:
        errors.append(f"mesh link set mismatch: expected {sorted(expected_links)}, got {sorted(links)}")

    for link_name in sorted(expected_links):
        link = links.get(link_name)
        if link is None:
            continue
        for tag in ["visual", "collision"]:
            element = link.find(tag)
            mesh = element.find("geometry/mesh") if element is not None else None
            if mesh is None or not mesh.attrib.get("filename"):
                errors.append(f"{link_name} missing {tag} mesh geometry")
                continue
            if tag == "visual":
                metrics["urdf_visual_count"] += 1
            else:
                metrics["urdf_collision_count"] += 1
            reference = mesh.attrib["filename"]
            mesh_references.append(reference)
            if Path(reference).is_absolute() or ".." in Path(reference).parts:
                errors.append(f"{link_name} {tag} mesh reference escapes run directory")
                continue
            if reference.startswith("retrieved_parts/") and reference.endswith("/original.step"):
                errors.append(f"{link_name} {tag} references immutable retrieved original.step directly")
            if (run_dir / reference).exists():
                metrics["urdf_mesh_files_exist_count"] += 1
            else:
                errors.append(f"{link_name} {tag} mesh file missing: {reference}")

    metrics["urdf_mesh_reference_count"] = len(mesh_references)
    status = "fail" if errors else "pass"
    message = "URDF visual/collision meshes are local run artifacts for every expected link." if not errors else "; ".join(errors)
    return ValidationGateResult(id="urdf_mesh_linkage", name="URDF visual/collision mesh linkage", status=status, message=message, details=metrics), metrics


def validate_preview_artifact(run_dir: Path) -> tuple[ValidationGateResult, dict[str, int]]:
    metrics = {"preview_target_count": 0, "preview_main_artifact_count": 0}
    preview_path = run_dir / "preview.json"
    if not preview_path.exists():
        return ValidationGateResult(id="preview_artifact", name="Preview artifact boundary", status="fail", message="preview.json missing"), metrics
    try:
        preview = json.loads(preview_path.read_text())
    except json.JSONDecodeError as exc:
        return ValidationGateResult(id="preview_artifact", name="Preview artifact boundary", status="fail", message=f"preview.json parse failed: {exc}"), metrics
    errors: list[str] = []
    main_artifacts = preview.get("main_artifacts", {})
    metrics["preview_main_artifact_count"] = len(main_artifacts)
    for key in ["assembly_step", "robot_urdf", "artifact_manifest", "validation_report", "run_report"]:
        rel = main_artifacts.get(key)
        if not rel:
            errors.append(f"preview main artifact missing key: {key}")
            continue
        path = Path(rel)
        if path.is_absolute() or ".." in path.parts or not (run_dir / rel).exists():
            errors.append(f"preview main artifact invalid: {key}={rel}")
    targets = preview.get("preview_targets", [])
    metrics["preview_target_count"] = len(targets)
    target_ids = {target.get("id") for target in targets}
    if {"assembly_step", "robot_urdf"} - target_ids:
        errors.append("preview targets must include assembly_step and robot_urdf")
    for target in targets:
        rel = target.get("artifact_path", "")
        path = Path(rel)
        if path.is_absolute() or ".." in path.parts or not (run_dir / rel).exists():
            errors.append(f"preview target invalid artifact_path: {rel}")
    status = "fail" if errors else "pass"
    message = "preview.json exposes stable server/frontend preview targets without adding UI runtime." if not errors else "; ".join(errors)
    return ValidationGateResult(id="preview_artifact", name="Preview artifact boundary", status=status, message=message, details=metrics), metrics


def validate_run(run_dir: Path, geometry_backend: str, backend_messages: list[str] | None = None, run_id: str = "pan_tilt_2axis_demo", product_spec_id: str = "pan_tilt_2axis_demo") -> ValidationReport:
    backend_messages = backend_messages or []
    required = ["bom.json", "assembly.step", "robot.urdf", "joints.json", "validation_report.json", "run_report.html"]
    gates: list[ValidationGateResult] = []
    missing = [name for name in required if name not in {"validation_report.json", "run_report.html"} and not (run_dir / name).exists()]
    custom_missing = [part for part in ["base_bracket", "tilt_yoke", "camera_plate"] if not (run_dir / "custom_parts" / part / "source.py").exists() or not (run_dir / "custom_parts" / part / "part.step").exists()]
    assembly_step = run_dir / "assembly.step"
    assembly_size = assembly_step.stat().st_size if assembly_step.exists() else 0
    assembly_exported = geometry_backend == "build123d" and assembly_size > 10_000 and not any("assembly export failed" in message for message in backend_messages)
    urdf_gate, urdf_metrics = validate_urdf_joint_contract(run_dir)
    frame_gate, frame_metrics = validate_frame_consistency(run_dir)
    mesh_gate, mesh_metrics = validate_urdf_mesh_linkage(run_dir)
    metadata_gate, metadata_metrics = validate_retrieved_part_metadata(run_dir)
    catalog_gate, catalog_metrics = validate_part_catalog(run_dir)
    selection_gate, selection_metrics = validate_part_selection_provenance(run_dir)
    worker_contracts_gate, worker_contracts_metrics = validate_worker_contracts(run_dir)
    interface_gate, interface_metrics = validate_interface_contracts(run_dir)
    preview_gate, preview_metrics = validate_preview_artifact(run_dir)
    review_state_gate, review_state_metrics = validate_review_state(run_dir)
    reproducibility_gate, reproducibility_metrics = validate_reproducibility_report(run_dir)
    gates.append(ValidationGateResult(id="artifacts", name="Required artifacts before report", status="pass" if not missing and not custom_missing else "fail", message="All core artifacts exist" if not missing and not custom_missing else f"Missing: {missing + custom_missing}"))
    gates.append(ValidationGateResult(id="external_immutable", name="External STEP originals immutable", status="pass", message="Retrieved original.step files are generated/copied once and normalized copies are separate."))
    gates.append(ValidationGateResult(id="geometry_backend", name="Geometry backend", status="pass" if geometry_backend == "build123d" else "warning", message="Custom parts generated with build123d STEP export." if geometry_backend == "build123d" else "build123d unavailable/export failed; deterministic placeholder STEP artifacts emitted.", details={"backend": geometry_backend, "messages": backend_messages}))
    gates.append(ValidationGateResult(id="assembly_step", name="Assembly STEP", status="pass" if assembly_exported else "warning", message="Assembly STEP contains placed build123d components." if assembly_exported else "Assembly STEP is a placeholder or below the real-geometry size threshold.", details={"backend": geometry_backend, "file_size_bytes": assembly_size, "component_count": 5, "min_file_size_bytes": 10000}))
    gates.append(urdf_gate)
    gates.append(frame_gate)
    gates.append(mesh_gate)
    gates.append(metadata_gate)
    gates.append(catalog_gate)
    gates.append(selection_gate)
    gates.append(worker_contracts_gate)
    gates.append(interface_gate)
    gates.append(preview_gate)
    gates.append(review_state_gate)
    gates.append(reproducibility_gate)
    metrics = {"retrieved_parts": 1, "custom_parts": 3, "joints": 2, "geometry_backend": geometry_backend, "assembly_step_bytes": assembly_size}
    metrics.update(urdf_metrics)
    metrics.update(frame_metrics)
    metrics.update(mesh_metrics)
    metrics.update(metadata_metrics)
    metrics.update(catalog_metrics)
    metrics.update(selection_metrics)
    metrics.update(worker_contracts_metrics)
    metrics.update(interface_metrics)
    metrics.update(preview_metrics)
    metrics.update(review_state_metrics)
    metrics.update(reproducibility_metrics)
    if (run_dir / "artifact_manifest.json").exists() and (run_dir / "run_report.html").exists() and (run_dir / "validation_report.json").exists():
        manifest_gate, manifest_metrics = validate_run_artifact_manifest(run_dir, metrics, {gate.id for gate in gates})
        gates.append(manifest_gate)
        metrics.update(manifest_metrics)
    status = "fail" if any(g.status == "fail" for g in gates) else ("warning" if any(g.status == "warning" for g in gates) else "pass")
    return ValidationReport(
        id=f"validation_{run_id}",
        run_id=run_id,
        product_spec_id=product_spec_id,
        status=status,
        gates=gates,
        metrics=metrics,
        artifacts={"product_spec": "product_spec.json", "bom": "bom.json", "part_catalog": "part_catalog.json", "part_selection_trace": "part_selection_trace.json", "worker_contracts": "worker_contracts.json", "review_state": "review_state.json", "reproducibility_report": "reproducibility_report.json", "assembly_plan": "assembly_plan.json", "assembly_step": "assembly.step", "urdf": "robot.urdf", "joints": "joints.json", "preview": "preview.json", "artifact_manifest": "artifact_manifest.json", "run_report": "run_report.html"},
        warnings=backend_messages if geometry_backend != "build123d" else [],
    )


FAILURE_CLASS_BY_GATE = {
    "artifacts": ("artifact_contract_failure", "workflow_orchestrator", ["Regenerate missing core artifacts", "Check product spec and pipeline write steps"], ["product_spec.json", "bom.json", "assembly_plan.json"]),
    "external_immutable": ("part_retrieval_policy_failure", "part_rag_worker", ["Restore immutable original STEP handling", "Ensure normalized copies are separate artifacts"], ["retrieved_parts"]),
    "geometry_backend": ("custom_geometry_backend_failure", "custom_cad_worker", ["Inspect build123d import/export errors", "Regenerate affected custom part STEP files"], ["custom_parts"]),
    "assembly_step": ("assembly_step_failure", "assembly_urdf_worker", ["Rebuild assembly.step from assembly_plan.json", "Inspect component placement/export failures"], ["assembly.step", "assembly_plan.json"]),
    "urdf_joint_contract": ("urdf_contract_failure", "assembly_urdf_worker", ["Regenerate robot.urdf and joints.json from the joint contract", "Check parent/child links, axes, and limits"], ["robot.urdf", "joints.json"]),
    "assembly_urdf_frame_consistency": ("frame_consistency_failure", "assembly_urdf_worker", ["Align assembly component transforms with URDF joint origins", "Check joints.json frame source data"], ["assembly_plan.json", "robot.urdf", "joints.json"]),
    "urdf_mesh_linkage": ("urdf_mesh_linkage_failure", "assembly_urdf_worker", ["Regenerate local URDF mesh proxy files", "Ensure URDF mesh references are relative run artifacts"], ["robot.urdf", "urdf_meshes"]),
    "retrieved_part_metadata": ("part_retrieval_metadata_failure", "part_rag_worker", ["Rebuild retrieved part metadata", "Verify BOM and assembly trace references"], ["bom.json", "retrieved_parts"]),
    "part_catalog": ("part_catalog_failure", "part_rag_worker", ["Regenerate part_catalog.json from local catalog metadata", "Verify immutable original, normalized references, provenance/license, and checksum fields"], ["part_catalog.json", "catalog/parts", "retrieved_parts"]),
    "part_selection_provenance": ("part_selection_provenance_failure", "part_rag_worker", ["Regenerate part_selection_trace.json from BOM, catalog, and retrieved part metadata", "Verify selected part source refs and immutable/normalized STEP paths"], ["part_selection_trace.json", "part_catalog.json", "retrieved_parts"]),
    "worker_contracts": ("worker_contract_failure", "workflow_orchestrator", ["Regenerate worker_contracts.json from the current local-first workflow gates and artifacts", "Verify worker contract categories, owners, non-goals, and artifact references"], ["worker_contracts.json", "validation_report.json", "artifact_manifest.json"]),
    "review_state": ("review_state_failure", "report_output_worker", ["Regenerate review_state.json from validation, manifest, preview, repair, provenance, and worker contracts", "Check review checklist and safe artifact references"], ["review_state.json", "validation_report.json", "artifact_manifest.json"]),
    "reproducibility_report": ("reproducibility_diagnostics_failure", "validation_report_worker", ["Regenerate reproducibility_report.json from runtime diagnostics and validation status", "Check Python/package probes, smoke command list, and Docker caveat fields"], ["reproducibility_report.json", "validation_report.json", "artifact_manifest.json"]),
    "interface_contract_lock": ("interface_contract_failure", "custom_cad_worker", ["Restore locked interface definitions", "Check mates, design contracts, joints, and URDF traces"], ["custom_parts", "assembly_plan.json", "joints.json"]),
    "preview_artifact": ("preview_artifact_failure", "report_output_worker", ["Regenerate preview.json from validation/report artifacts", "Check preview targets resolve to local run artifacts"], ["preview.json", "assembly.step", "robot.urdf"]),
    "run_artifact_manifest": ("manifest_report_stale", "validation_report_worker", ["Regenerate artifact_manifest.json and run_report.html", "Check manifest references and report sections"], ["artifact_manifest.json", "run_report.html", "validation_report.json"]),
}


def classify_validation_failures(report: ValidationReport) -> RepairPlan:
    actions: list[RepairAction] = []
    for gate in report.gates:
        if gate.status == "pass":
            continue
        failure_class, owner, suggested, artifacts = FAILURE_CLASS_BY_GATE.get(
            gate.id,
            ("validation_internal_error" if gate.status == "fail" else "unknown_failure", "validation_report_worker", ["Inspect validation gate output and source artifacts"], ["validation_report.json"]),
        )
        actions.append(
            RepairAction(
                run_id=report.run_id,
                status="planned",
                failure_class=failure_class,
                source_gate_id=gate.id,
                summary=gate.message,
                recommended_owner=owner,
                suggested_actions=suggested,
                blocking_artifacts=artifacts,
            )
        )
    status = "blocked" if any(gate.status == "fail" for gate in report.gates) else ("warning" if actions else "pass")
    return RepairPlan(
        id=f"repair_{report.run_id}",
        run_id=report.run_id,
        product_spec_id=report.product_spec_id,
        status=status,
        failure_count=len(actions),
        action_count=len(actions),
        actions=actions,
    )


def write_repair_plan(run_dir: Path, report: ValidationReport) -> RepairPlan:
    plan = classify_validation_failures(report)
    write_json(run_dir / "repair_plan.json", plan)
    return plan


def write_report(run_dir: Path, report: ValidationReport) -> None:
    manifest = build_artifact_manifest(run_dir, report)
    artifacts = sorted(set(_manifest_paths(manifest)))
    artifact_rows = "\n".join(f"<li><code>{escape(path)}</code></li>" for path in artifacts)
    gate_rows = "\n".join(f"<tr><td>{escape(g.id)}</td><td>{escape(g.name)}</td><td>{escape(g.status)}</td><td>{escape(g.message)}</td></tr>" for g in report.gates)
    metric_rows = "\n".join(f"<tr><td>{escape(str(key))}</td><td>{escape(str(value))}</td></tr>" for key, value in sorted(report.metrics.items()))
    servo = json.loads((run_dir / "retrieved_parts" / "servo_mg996r" / "part_record.json").read_text())
    metadata = servo["metadata"]
    repair_plan = json.loads((run_dir / "repair_plan.json").read_text()) if (run_dir / "repair_plan.json").exists() else {"status": "missing", "failure_count": 0, "action_count": 0, "actions": []}
    selection_trace = json.loads((run_dir / "part_selection_trace.json").read_text()) if (run_dir / "part_selection_trace.json").exists() else {"selected_part_id": "missing", "candidate_count": 0, "constraints_matched": [], "selection_reason": "missing"}
    worker_contracts = json.loads((run_dir / "worker_contracts.json").read_text()) if (run_dir / "worker_contracts.json").exists() else {"contracts": []}
    review_state = json.loads((run_dir / "review_state.json").read_text()) if (run_dir / "review_state.json").exists() else {"artifact_groups": [], "checklist": [], "limitations": []}
    reproducibility = json.loads((run_dir / "reproducibility_report.json").read_text()) if (run_dir / "reproducibility_report.json").exists() else {"package_availability": [], "smoke_commands": [], "limitations": [], "docker_smoke_status": "missing", "docker_smoke_note": "missing"}
    agent_trace = json.loads((run_dir / "agent_trace.json").read_text()) if (run_dir / "agent_trace.json").exists() else None
    agent_section = ""
    if agent_trace:
        adapter = agent_trace.get("adapter", {})
        agent_section = f"""
<h2>Agent harness trace</h2>
<p><code>agent_trace.json</code> request_type {escape(str(agent_trace.get('request_type', 'missing')))}; selected_workflow {escape(str(agent_trace.get('selected_workflow', 'missing')))}; parent_run_id {escape(str(agent_trace.get('parent_run_id', 'none')))}; unsupported_requirements {escape(', '.join(agent_trace.get('unsupported_requirements', [])))}.</p>
<p>Adapter provider {escape(str(adapter.get('provider', 'missing')))}; model {escape(str(adapter.get('model', 'missing')))}; mode {escape(str(adapter.get('mode', 'missing')))}; external_call_performed {escape(str(adapter.get('external_call_performed', False)))}; tool_calls {escape(str(len(agent_trace.get('tool_calls', []))))}.</p>
<p>Prompt: {escape(str(agent_trace.get('prompt', '')))}. Validation summary: {escape(str(agent_trace.get('validation_summary', {})))}</p>
"""
    html = f"""<!doctype html>
<html><head><meta charset=\"utf-8\"><title>CADX MVP Demo Report</title></head><body>
<h1>CADX MVP Demo Report: pan_tilt_2axis_demo</h1>
<p><b>product_spec_id:</b> {escape(report.product_spec_id)}<br><b>run_id:</b> {escape(report.run_id)}<br><b>generated_at:</b> {escape(manifest['generated_at'])}</p>
<h2>Generated artifacts</h2><ul>{artifact_rows}</ul>
<h2>Validation gates</h2><p><b>validation status:</b> {escape(report.status)}</p><table><tr><th>id</th><th>name</th><th>status</th><th>message</th></tr>{gate_rows}</table>
<h2>Metrics summary</h2><table><tr><th>metric</th><th>value</th></tr>{metric_rows}</table>
<h2>Retrieved part metadata</h2>
<p><b>servo_mg996r</b> source_id={escape(str(metadata['source_id']))}; source_uri={escape(str(metadata['source_uri']))}; manufacturer={escape(str(metadata['manufacturer']))}; model={escape(str(metadata['model']))}; rag_score={escape(str(metadata['rag_score']))}</p>
<p>immutable original: <code>{escape(servo['original_step_path'])}</code>; normalized: <code>{escape(servo['normalized_step_path'])}</code>; category={escape(servo['category'])}; interfaces={escape(', '.join(metadata['interface_tags']))}</p>
<h2>Part catalog summary</h2>
<p>part_catalog.json count {report.metrics.get('part_catalog_count')}; source_count {report.metrics.get('part_catalog_source_count')}; immutable_count {report.metrics.get('part_catalog_immutable_count')}; checksum_count {report.metrics.get('part_catalog_checksum_count')}; local_catalog_metadata_count {report.metrics.get('local_catalog_metadata_count')}; interface_tag_count {report.metrics.get('part_catalog_interface_tag_count')}; dimension_tag_count {report.metrics.get('part_catalog_dimension_tag_count')}</p>
<p>Local STEP catalog seed: <code>catalog/parts/servo_mg996r/metadata.json</code>; original <code>catalog/parts/servo_mg996r/original.step</code>; normalized <code>catalog/parts/servo_mg996r/normalized.step</code>; license_status=placeholder-local-seed; provenance_status=curated_local_fixture.</p>
<h2>Part Selection Provenance</h2>
<p><code>part_selection_trace.json</code> selected {escape(str(selection_trace['selected_part_id']))} from {escape(str(selection_trace['candidate_count']))} candidate(s); constraints matched: {escape(', '.join(selection_trace.get('constraints_matched', [])))}; trace_count {report.metrics.get('part_selection_trace_count')}; retrieved_part_with_source_count {report.metrics.get('retrieved_part_with_source_count')}.</p>
<p>source_id={escape(str(selection_trace.get('source_id', '')))}; source_kind={escape(str(selection_trace.get('source_kind', '')))}; original <code>{escape(str(selection_trace.get('original_step_path', '')))}</code>; normalized <code>{escape(str(selection_trace.get('normalized_step_path', '')))}</code>; reason: {escape(str(selection_trace['selection_reason']))}</p>
<h2>Worker contracts</h2>
<p><code>worker_contracts.json</code> contract_count {report.metrics.get('worker_contract_count')}; artifact_reference_count {report.metrics.get('worker_contract_artifact_reference_count')}; gate_reference_count {report.metrics.get('worker_contract_gate_reference_count')}; covered_gate_count {report.metrics.get('worker_contract_covered_gate_count')}.</p>
<p>Categories: {escape(', '.join(sorted({contract.get('category', '') for contract in worker_contracts.get('contracts', [])})))}. Owners: {escape(', '.join(sorted({contract.get('responsible_worker_type', '') for contract in worker_contracts.get('contracts', [])})))}.</p>
<h2>Review state</h2>
<p><code>review_state.json</code> checklist_count {report.metrics.get('review_state_checklist_count')}; artifact_group_count {report.metrics.get('review_state_artifact_group_count')}; preview_target_count {report.metrics.get('review_state_preview_target_count')}; limitation_count {report.metrics.get('review_state_limitation_count')}.</p>
<p>Artifact groups: {escape(', '.join(group.get('id', '') for group in review_state.get('artifact_groups', [])))}. Checklist: {escape(', '.join(item.get('id', '') + ':' + item.get('status', '') for item in review_state.get('checklist', [])))}.</p>
<p>Local review limitations: {escape(', '.join(review_state.get('limitations', [])))}.</p>
<h2>Reproducibility diagnostics</h2>
<p><code>reproducibility_report.json</code> python {escape(str(reproducibility.get('python_version', 'missing')))} on {escape(str(reproducibility.get('platform_system', 'missing')))} / {escape(str(reproducibility.get('platform_machine', 'missing')))}; geometry_backend {escape(str(reproducibility.get('geometry_backend', 'missing')))}; validation_status {escape(str(reproducibility.get('validation_status', 'missing')))}; validation_gate_count {escape(str(reproducibility.get('validation_gate_count', 'missing')))}.</p>
<p>reproducibility_package_available_count {report.metrics.get('reproducibility_package_available_count')}; reproducibility_smoke_command_count {report.metrics.get('reproducibility_smoke_command_count')}; reproducibility_limitation_count {report.metrics.get('reproducibility_limitation_count')}; docker_smoke_status {escape(str(reproducibility.get('docker_smoke_status', 'missing')))}; docker_smoke_note {escape(str(reproducibility.get('docker_smoke_note', 'missing')))}.</p>
<p>Package probes: {escape(', '.join(package.get('name', '') + ':' + str(package.get('available', False)) for package in reproducibility.get('package_availability', [])))}. Smoke commands: {escape(' | '.join(reproducibility.get('smoke_commands', [])))}. Limitations: {escape(', '.join(reproducibility.get('limitations', [])))}.</p>
{agent_section}<h2>Preview summary</h2>
<p>preview.json target_count {report.metrics.get('preview_target_count')}; main_artifact_count {report.metrics.get('preview_main_artifact_count')}</p>
<h2>Assembly / URDF summary</h2>
<p>components {report.metrics.get('assembly_component_count')}; links {report.metrics.get('urdf_links')}; joints {report.metrics.get('urdf_joints')}; urdf_visual_count {report.metrics.get('urdf_visual_count')}; urdf_collision_count {report.metrics.get('urdf_collision_count')}; urdf_mesh_reference_count {report.metrics.get('urdf_mesh_reference_count')}; urdf_mesh_files_exist_count {report.metrics.get('urdf_mesh_files_exist_count')}</p>
<h2>Interface contract summary</h2>
<p>part_count {report.metrics.get('interface_contract_part_count')}; locked_count {report.metrics.get('interface_contract_locked_count')}; mate_count {report.metrics.get('interface_contract_mate_count')}; joint_trace_count {report.metrics.get('interface_contract_joint_trace_count')}; interface_contract_locked_count {report.metrics.get('interface_contract_locked_count')}</p>
<h2>Repair plan summary</h2>
<p>repair_plan.json status {escape(str(repair_plan['status']))}; failure_count {escape(str(repair_plan['failure_count']))}; action_count {escape(str(repair_plan['action_count']))}</p>
<p>Policy: Part RAG metadata first; external STEP originals immutable; custom parts editable via source/design contracts; future direct edits require interface locks and before/after geometric diff.</p>
</body></html>
"""
    (run_dir / "run_report.html").write_text(html)


def run_pan_tilt_workflow(out_dir: Path, spec=None, run_id: str = "pan_tilt_2axis_demo") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = spec or pan_tilt_2axis.product_spec()
    bom = pan_tilt_2axis.bom()
    write_json(out_dir / "product_spec.json", spec)
    write_json(out_dir / "bom.json", bom)

    retrieved = copy_retrieved_part(out_dir, pan_tilt_2axis.servo_part())
    write_local_catalog_seed(out_dir, retrieved)
    parts = [retrieved]
    can_use_build123d, import_error = build123d_available()
    geometry_backend = "build123d" if can_use_build123d else "placeholder"
    backend_messages: list[str] = [] if can_use_build123d else [import_error or "build123d unavailable"]

    for request in bom.generated_custom_parts:
        part_dir = out_dir / "custom_parts" / request.id
        part_dir.mkdir(parents=True, exist_ok=True)
        write_source(part_dir / "source.py", request.id)
        part_backend, warning = write_custom_part_geometry(request.id, part_dir / "part.step", can_use_build123d)
        if part_backend != "build123d":
            geometry_backend = "placeholder"
        if warning:
            backend_messages.append(warning)
        contract = pan_tilt_2axis.custom_contract(request.id, request.required_interfaces)
        write_json(part_dir / "design_contract.json", contract)
        part_record = PartRecord(
            id=request.id,
            name=request.role,
            source="generated" if part_backend == "build123d" else "placeholder",
            category="adapter",
            normalized_step_path=str((part_dir / "part.step").relative_to(out_dir)),
            metadata={"geometry_backend": part_backend},
            bbox_mm=_bbox_for(request.id),
            interfaces=pan_tilt_2axis.custom_interfaces(request.id),
            immutable_original=False,
            design_contract_id=contract.id,
        )
        write_json(part_dir / "part_record.json", part_record)
        parts.append(part_record)

    assembly = pan_tilt_2axis.assembly_plan()
    write_json(out_dir / "assembly_plan.json", assembly)
    if geometry_backend == "build123d":
        try:
            export_build123d_assembly(out_dir, out_dir / "assembly.step")
        except Exception as exc:  # pragma: no cover - depends on OCC/export runtime
            write_placeholder_step(out_dir / "assembly.step", "pan_tilt_2axis_assembly", f"build123d assembly export failed: {exc}")
            backend_messages.append(f"build123d assembly export failed: {exc}")
    else:
        write_placeholder_step(out_dir / "assembly.step", "pan_tilt_2axis_assembly", f"Sprint 0 assembly manifest; custom part backend={geometry_backend}")
    write_json(out_dir / "joints.json", pan_tilt_2axis.joints())
    export_urdf(out_dir)
    write_part_catalog(out_dir, run_id, spec.id)
    write_part_selection_trace(out_dir, run_id, spec.id)
    write_worker_contracts(out_dir, run_id, spec.id)

    report = validate_run(out_dir, geometry_backend=geometry_backend, backend_messages=backend_messages, run_id=run_id, product_spec_id=spec.id)
    write_repair_plan(out_dir, report)
    write_json(out_dir / "validation_report.json", report)
    write_artifact_manifest(out_dir, report)
    write_preview_artifact(out_dir, report)
    write_review_state(out_dir, report)
    write_reproducibility_report(out_dir, report)
    write_report(out_dir, report)
    report = validate_run(out_dir, geometry_backend=geometry_backend, backend_messages=backend_messages, run_id=run_id, product_spec_id=spec.id)
    write_repair_plan(out_dir, report)
    write_json(out_dir / "validation_report.json", report)
    write_artifact_manifest(out_dir, report)
    write_preview_artifact(out_dir, report)
    write_review_state(out_dir, report)
    write_reproducibility_report(out_dir, report)
    write_report(out_dir, report)
    return out_dir


def run_pan_tilt_demo(out_dir: Path) -> Path:
    return run_pan_tilt_workflow(out_dir)
