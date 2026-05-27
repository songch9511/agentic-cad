from pathlib import Path
import json
import xml.etree.ElementTree as ET

from cadx.demos import pan_tilt_2axis
from cadx.pipeline import orchestrator
from cadx.pipeline.orchestrator import run_pan_tilt_demo
from cadx.pipeline.runner import load_product_spec, run_from_spec
from cadx.pipeline.workflows import list_workflows, select_workflow, supported_workflow_ids


def test_pan_tilt_pipeline_outputs(tmp_path: Path):
    run_dir = run_pan_tilt_demo(tmp_path / "run")
    for name in ["product_spec.json", "bom.json", "part_catalog.json", "part_selection_trace.json", "worker_contracts.json", "review_state.json", "reproducibility_report.json", "assembly_plan.json", "assembly.step", "robot.urdf", "joints.json", "validation_report.json", "repair_plan.json", "preview.json", "run_report.html", "artifact_manifest.json"]:
        assert (run_dir / name).exists(), name
    servo_record_path = run_dir / "retrieved_parts" / "servo_mg996r" / "part_record.json"
    assert (run_dir / "retrieved_parts" / "servo_mg996r" / "original.step").exists()
    assert (run_dir / "retrieved_parts" / "servo_mg996r" / "normalized.step").exists()
    servo_record = json.loads(servo_record_path.read_text())
    assert servo_record["metadata"]["source_id"] == "placeholder:mg996r:v1"
    assert servo_record["metadata"]["source_uri"] == "cadx://placeholder/vendor/mg996r.step"
    assert servo_record["metadata"]["manufacturer"] == "TowerPro-compatible placeholder"
    assert servo_record["metadata"]["model"] == "MG996R"
    assert set(servo_record["metadata"]["interface_tags"]) == {"servo_output_spline", "servo_mount_tabs"}
    assert set(servo_record["metadata"]["contract_references"]) == {"bom:servo_pan", "bom:servo_tilt", "assembly:servo_pan", "assembly:servo_tilt"}
    assert servo_record["original_step_path"] == "retrieved_parts/servo_mg996r/original.step"
    assert servo_record["normalized_step_path"] == "retrieved_parts/servo_mg996r/normalized.step"
    assert servo_record["immutable_original"] is True
    assert (run_dir / "catalog" / "parts" / "servo_mg996r" / "metadata.json").exists()
    assert (run_dir / "catalog" / "parts" / "servo_mg996r" / "original.step").exists()
    assert (run_dir / "catalog" / "parts" / "servo_mg996r" / "normalized.step").exists()
    local_catalog_metadata = json.loads((run_dir / "catalog" / "parts" / "servo_mg996r" / "metadata.json").read_text())
    assert local_catalog_metadata["part_id"] == "servo_mg996r"
    assert local_catalog_metadata["license_status"] == "placeholder-local-seed"
    assert local_catalog_metadata["provenance_status"] == "curated_local_fixture"
    assert local_catalog_metadata["immutable_original"] is True
    assert local_catalog_metadata["checksum_sha256"]
    assert local_catalog_metadata["source_kind"] == "local_seed"
    assert "matches_pan_tilt_interfaces" in local_catalog_metadata["selection_suitability"]
    part_catalog = json.loads((run_dir / "part_catalog.json").read_text())
    assert part_catalog["run_id"] == "pan_tilt_2axis_demo"
    assert part_catalog["product_spec_id"] == "pan_tilt_2axis_demo"
    assert len(part_catalog["sources"]) == 1
    assert part_catalog["sources"][0]["source_type"] == "local_seed"
    assert len(part_catalog["parts"]) == 1
    catalog_servo = part_catalog["parts"][0]
    assert catalog_servo["id"] == "servo_mg996r"
    assert catalog_servo["part_id"] == "servo_mg996r"
    assert catalog_servo["source_id"] == servo_record["metadata"]["source_id"]
    assert catalog_servo["source_uri"] == servo_record["metadata"]["source_uri"]
    assert catalog_servo["source_kind"] == "local_seed"
    assert catalog_servo["manufacturer"] == servo_record["metadata"]["manufacturer"]
    assert catalog_servo["model"] == servo_record["metadata"]["model"]
    assert catalog_servo["license_status"] == "placeholder-local-seed"
    assert catalog_servo["provenance_status"] == "curated_local_fixture"
    assert catalog_servo["checksum_sha256"] == local_catalog_metadata["checksum_sha256"]
    assert "local_deterministic_seed" in catalog_servo["selection_suitability"]
    assert set(catalog_servo["interfaces"]) == {interface["id"] for interface in servo_record["interfaces"]}
    assert set(catalog_servo["interface_tags"]) == set(servo_record["metadata"]["interface_tags"])
    assert set(catalog_servo["dimension_tags"]) == set(servo_record["metadata"]["dimension_tags"])
    assert catalog_servo["original_step_path"] == "catalog/parts/servo_mg996r/original.step"
    assert catalog_servo["normalized_step_path"] == "catalog/parts/servo_mg996r/normalized.step"
    assert catalog_servo["metadata_path"] == "catalog/parts/servo_mg996r/metadata.json"
    assert catalog_servo["part_record_path"] == "retrieved_parts/servo_mg996r/part_record.json"
    assert catalog_servo["immutable_original"] is True
    expected_custom_interfaces = {
        "base_bracket": {"base_mount_holes", "servo_mount_tabs"},
        "tilt_yoke": {"servo_output_spline", "camera_mount_pattern"},
        "camera_plate": {"camera_mount_pattern"},
    }
    for part_id in ["base_bracket", "tilt_yoke", "camera_plate"]:
        assert (run_dir / "custom_parts" / part_id / "source.py").exists()
        assert (run_dir / "custom_parts" / part_id / "part.step").exists()
        record = json.loads((run_dir / "custom_parts" / part_id / "part_record.json").read_text())
        assert record["metadata"]["geometry_backend"] in {"build123d", "placeholder"}
        assert {interface["id"] for interface in record["interfaces"]} == expected_custom_interfaces[part_id]
        contract = json.loads((run_dir / "custom_parts" / part_id / "design_contract.json").read_text())
        assert set(contract["locked_interfaces"]) == expected_custom_interfaces[part_id]
        invariant_targets = {invariant["target"] for invariant in contract["geometric_invariants"]}
        assert expected_custom_interfaces[part_id].issubset(invariant_targets)
        for interface in record["interfaces"]:
            assert len(interface["frame"]["origin_mm"]) == 3
            assert interface["geometry"]["parameters"]
    report = json.loads((run_dir / "validation_report.json").read_text())
    backend = report["metrics"]["geometry_backend"]
    assert backend in {"build123d", "placeholder"}
    if backend == "build123d":
        assert report["status"] == "pass"
        assert not report["warnings"]
        assembly_gate = next(g for g in report["gates"] if g["id"] == "assembly_step")
        assert assembly_gate["status"] == "pass"
        assert (run_dir / "assembly.step").stat().st_size > 10_000
    else:
        assert report["status"] == "warning"
        assert report["warnings"]
    root = ET.parse(run_dir / "robot.urdf").getroot()
    links = {link.attrib["name"]: link for link in root.findall("link")}
    assert set(links) == {"base_link", "pan_link", "tilt_link"}
    for link_name, link in links.items():
        for tag in ["visual", "collision"]:
            mesh = link.find(f"{tag}/geometry/mesh")
            assert mesh is not None, f"{link_name} missing {tag} mesh"
            mesh_ref = mesh.attrib["filename"]
            assert mesh_ref.startswith("urdf_meshes/")
            assert "original.step" not in mesh_ref
            assert (run_dir / mesh_ref).exists()
    urdf_joints = {joint.attrib["name"]: joint for joint in root.findall("joint")}
    assert set(urdf_joints) == {"pan_yaw", "tilt_pitch"}
    assert urdf_joints["pan_yaw"].find("parent").attrib["link"] == "base_link"
    assert urdf_joints["pan_yaw"].find("child").attrib["link"] == "pan_link"
    assert urdf_joints["pan_yaw"].find("axis").attrib["xyz"] == "0.0 0.0 1.0"
    assert urdf_joints["tilt_pitch"].find("parent").attrib["link"] == "pan_link"
    assert urdf_joints["tilt_pitch"].find("child").attrib["link"] == "tilt_link"
    assert urdf_joints["tilt_pitch"].find("axis").attrib["xyz"] == "0.0 1.0 0.0"
    assembly_plan = json.loads((run_dir / "assembly_plan.json").read_text())
    placements = {component["id"]: component["initial_transform"]["translation_mm"] for component in assembly_plan["components"]}
    assert placements == {
        "base_bracket": [0.0, 0.0, 0.0],
        "servo_pan": [0.0, 0.0, 22.0],
        "tilt_yoke": [0.0, -25.0, 52.0],
        "servo_tilt": [0.0, 20.0, 58.0],
        "camera_plate": [0.0, 0.0, 104.0],
    }
    assert urdf_joints["pan_yaw"].find("origin").attrib["xyz"] == "0 0 0.045"
    assert urdf_joints["tilt_pitch"].find("origin").attrib["xyz"] == "0 0 0.085"
    urdf_gate = next(g for g in report["gates"] if g["id"] == "urdf_joint_contract")
    assert urdf_gate["status"] == "pass"
    frame_gate = next(g for g in report["gates"] if g["id"] == "assembly_urdf_frame_consistency")
    assert frame_gate["status"] == "pass"
    assert report["metrics"]["urdf_links"] == 3
    assert report["metrics"]["urdf_joints"] == 2
    assert report["metrics"]["joint_contract_count"] == 2
    assert report["metrics"]["assembly_component_count"] == 5
    assert report["metrics"]["frame_contract_count"] == 2
    assert report["metrics"]["urdf_origin_count"] == 2
    mesh_gate = next(g for g in report["gates"] if g["id"] == "urdf_mesh_linkage")
    assert mesh_gate["status"] == "pass"
    assert report["metrics"]["urdf_visual_count"] == 3
    assert report["metrics"]["urdf_collision_count"] == 3
    assert report["metrics"]["urdf_mesh_reference_count"] == 6
    assert report["metrics"]["urdf_mesh_files_exist_count"] == 6
    metadata_gate = next(g for g in report["gates"] if g["id"] == "retrieved_part_metadata")
    assert metadata_gate["status"] == "pass"
    assert report["metrics"]["retrieved_part_metadata_count"] == 1
    assert report["metrics"]["retrieved_part_interface_count"] == 2
    assert report["metrics"]["retrieved_part_trace_count"] == 4
    catalog_gate = next(g for g in report["gates"] if g["id"] == "part_catalog")
    assert catalog_gate["status"] == "pass"
    assert report["metrics"]["part_catalog_count"] == 1
    assert report["metrics"]["part_catalog_source_count"] == 1
    assert report["metrics"]["part_catalog_immutable_count"] == 1
    assert report["metrics"]["part_catalog_checksum_count"] == 1
    assert report["metrics"]["local_catalog_metadata_count"] == 1
    assert report["metrics"]["part_catalog_interface_tag_count"] == 2
    assert report["metrics"]["part_catalog_dimension_tag_count"] == 3
    selection_trace = json.loads((run_dir / "part_selection_trace.json").read_text())
    assert selection_trace["selected_part_id"] == "servo_mg996r"
    assert selection_trace["source_id"] == catalog_servo["source_id"]
    assert selection_trace["source_kind"] == "local_seed"
    assert selection_trace["candidate_count"] == 1
    assert selection_trace["candidate_part_ids"] == ["servo_mg996r"]
    assert selection_trace["original_step_path"] == catalog_servo["original_step_path"]
    assert selection_trace["normalized_step_path"] == catalog_servo["normalized_step_path"]
    assert selection_trace["immutable_original"] is True
    assert set(selection_trace["constraints_matched"]) == {"servo_mount_tabs", "servo_output_spline"}
    selection_gate = next(g for g in report["gates"] if g["id"] == "part_selection_provenance")
    assert selection_gate["status"] == "pass"
    assert report["metrics"]["part_selection_trace_count"] == 1
    assert report["metrics"]["catalog_source_count"] == 1
    assert report["metrics"]["catalog_part_count"] == 1
    assert report["metrics"]["retrieved_part_with_source_count"] == 1
    worker_contracts = json.loads((run_dir / "worker_contracts.json").read_text())
    contract_categories = {contract["category"] for contract in worker_contracts["contracts"]}
    assert {"intake", "part_sourcing", "cad_generation", "assembly_urdf", "validation_repair", "report_review"}.issubset(contract_categories)
    assert all("no_cloud" in contract["non_goals"] for contract in worker_contracts["contracts"])
    assert all("no_new_cad_kernel" in contract["non_goals"] for contract in worker_contracts["contracts"])
    covered_contract_gates = {gate for contract in worker_contracts["contracts"] for gate in contract["validation_gates"]}
    assert "part_selection_provenance" in covered_contract_gates
    assert "run_artifact_manifest" in covered_contract_gates
    worker_gate = next(g for g in report["gates"] if g["id"] == "worker_contracts")
    assert worker_gate["status"] == "pass"
    assert report["metrics"]["worker_contract_count"] == 6
    assert report["metrics"]["worker_contract_covered_gate_count"] >= 13
    assert report["metrics"]["worker_contract_gate_reference_count"] >= 13
    interface_gate = next(g for g in report["gates"] if g["id"] == "interface_contract_lock")
    assert interface_gate["status"] == "pass"
    assert report["metrics"]["interface_contract_part_count"] == 4
    assert report["metrics"]["interface_contract_locked_count"] == 5
    assert report["metrics"]["interface_contract_mate_count"] == 3
    assert report["metrics"]["interface_contract_joint_trace_count"] == 2
    manifest = json.loads((run_dir / "artifact_manifest.json").read_text())
    assert manifest["generated_at"] == "2026-05-25T00:00:00+09:00"
    assert manifest["core_artifacts"]["part_catalog"] == "part_catalog.json"
    assert manifest["core_artifacts"]["part_selection_trace"] == "part_selection_trace.json"
    assert manifest["core_artifacts"]["worker_contracts"] == "worker_contracts.json"
    assert manifest["core_artifacts"]["review_state"] == "review_state.json"
    assert manifest["core_artifacts"]["reproducibility_report"] == "reproducibility_report.json"
    assert manifest["core_artifacts"]["validation_report"] == "validation_report.json"
    assert manifest["core_artifacts"]["repair_plan"] == "repair_plan.json"
    assert manifest["core_artifacts"]["preview"] == "preview.json"
    assert manifest["core_artifacts"]["run_report"] == "run_report.html"
    assert manifest["core_artifacts"]["artifact_manifest"] == "artifact_manifest.json"
    manifest_refs = []
    manifest_refs.extend(manifest["core_artifacts"].values())
    for entries in manifest["custom_parts"].values():
        manifest_refs.extend(entries)
    for entries in manifest["retrieved_parts"].values():
        manifest_refs.extend(entries)
    for entries in manifest["catalog_parts"].values():
        manifest_refs.extend(entries)
    manifest_refs.extend(manifest["urdf_meshes"])
    assert "retrieved_parts/servo_mg996r/original.step" in manifest_refs
    assert "retrieved_parts/servo_mg996r/normalized.step" in manifest_refs
    assert "catalog/parts/servo_mg996r/metadata.json" in manifest_refs
    assert "catalog/parts/servo_mg996r/original.step" in manifest_refs
    assert "catalog/parts/servo_mg996r/normalized.step" in manifest_refs
    assert "part_selection_trace.json" in manifest_refs
    assert "worker_contracts.json" in manifest_refs
    assert "review_state.json" in manifest_refs
    assert "reproducibility_report.json" in manifest_refs
    assert "urdf_meshes/base_link.step" in manifest_refs
    assert all(not Path(ref).is_absolute() and ".." not in Path(ref).parts for ref in manifest_refs)
    assert all((run_dir / ref).exists() for ref in manifest_refs)
    preview = json.loads((run_dir / "preview.json").read_text())
    assert preview["run_id"] == "pan_tilt_2axis_demo"
    assert preview["validation_status"] == report["status"]
    assert preview["main_artifacts"]["assembly_step"] == "assembly.step"
    assert preview["main_artifacts"]["robot_urdf"] == "robot.urdf"
    assert {target["id"] for target in preview["preview_targets"]} == {"assembly_step", "robot_urdf"}
    assert all((run_dir / target["artifact_path"]).exists() for target in preview["preview_targets"])
    preview_gate = next(g for g in report["gates"] if g["id"] == "preview_artifact")
    assert preview_gate["status"] == "pass"
    assert report["metrics"]["preview_target_count"] == 2
    assert report["metrics"]["preview_main_artifact_count"] == 5
    review_state = json.loads((run_dir / "review_state.json").read_text())
    assert review_state["review_status"] == report["status"]
    assert review_state["validation_gate_count"] >= 14
    assert {group["id"] for group in review_state["artifact_groups"]} == {"spec", "catalog_provenance", "cad_assembly", "validation_repair", "review"}
    assert {item["id"] for item in review_state["checklist"]} == {"validation", "preview", "repair", "part_provenance", "worker_contracts"}
    assert "no_arbitrary_file_streaming" in review_state["limitations"]
    review_gate = next(g for g in report["gates"] if g["id"] == "review_state")
    assert review_gate["status"] == "pass"
    assert report["metrics"]["review_state_checklist_count"] == 5
    assert report["metrics"]["review_state_artifact_group_count"] == 5
    assert report["metrics"]["review_state_preview_target_count"] == 2
    assert report["metrics"]["review_state_limitation_count"] == 8
    reproducibility = json.loads((run_dir / "reproducibility_report.json").read_text())
    assert reproducibility["python_version_major"] == 3
    assert reproducibility["python_version_minor"] == 12
    assert reproducibility["geometry_backend"] == backend
    assert reproducibility["validation_status"] == report["status"]
    assert reproducibility["validation_gate_count"] >= 15
    assert reproducibility["docker_smoke_status"] == "manual_optional"
    assert {package["name"] for package in reproducibility["package_availability"]} == {"build123d", "fastapi", "uvicorn", "httpx"}
    assert "local_diagnostics_only" in reproducibility["limitations"]
    reproducibility_gate = next(g for g in report["gates"] if g["id"] == "reproducibility_report")
    assert reproducibility_gate["status"] == "pass"
    assert report["metrics"]["reproducibility_python_major"] == 3
    assert report["metrics"]["reproducibility_package_available_count"] >= 1
    assert report["metrics"]["reproducibility_smoke_command_count"] == 5
    assert report["metrics"]["reproducibility_limitation_count"] >= 6
    manifest_gate = next(g for g in report["gates"] if g["id"] == "run_artifact_manifest")
    assert manifest_gate["status"] == "pass"
    assert report["metrics"]["manifest_artifact_count"] == report["metrics"]["manifest_reference_count"]
    assert report["metrics"]["run_report_section_count"] == 13
    assert report["metrics"]["manifest_gate_coverage_count"] >= 10
    html = (run_dir / "run_report.html").read_text()
    for token in ["Generated artifacts", "Validation gates", "Metrics summary", "Retrieved part metadata", "Part catalog summary", "Part Selection Provenance", "Worker contracts", "Review state", "Reproducibility diagnostics", "Preview summary", "Assembly / URDF summary", "Interface contract summary", "Repair plan summary", "servo_mg996r", "placeholder:mg996r:v1", "catalog/parts/servo_mg996r/metadata.json", "placeholder-local-seed", "part_catalog.json", "part_selection_trace.json", "worker_contracts.json", "part_selection_trace_count", "worker_contract_count", "review_state.json", "review_state_checklist_count", "reproducibility_report.json", "reproducibility_package_available_count", "part_catalog_count", "part_catalog_checksum_count", "preview.json", "preview_target_count", "urdf_mesh_reference_count", "interface_contract_locked_count", "repair_plan.json"]:
        assert token in html
    repair_plan = json.loads((run_dir / "repair_plan.json").read_text())
    assert repair_plan["run_id"] == "pan_tilt_2axis_demo"
    assert repair_plan["product_spec_id"] == "pan_tilt_2axis_demo"
    assert repair_plan["status"] == "pass"
    assert repair_plan["failure_count"] == 0
    assert repair_plan["action_count"] == 0
    assert repair_plan["actions"] == []
    broken_manifest = json.loads((run_dir / "artifact_manifest.json").read_text())
    broken_manifest["core_artifacts"]["assembly_step"] = "missing/assembly.step"
    (run_dir / "artifact_manifest.json").write_text(json.dumps(broken_manifest))
    broken_gate, _ = orchestrator.validate_run_artifact_manifest(run_dir, report["metrics"], {gate["id"] for gate in report["gates"]})
    assert broken_gate.status == "fail"


def test_run_from_spec_uses_run_id_and_preserves_artifacts(tmp_path: Path):
    spec_path = tmp_path / "product_spec.json"
    spec_path.write_text(pan_tilt_2axis.product_spec().model_dump_json(indent=2))
    run_dir = run_from_spec(spec_path, run_id="v02_test_run", runs_root=tmp_path / "runs")
    assert run_dir == tmp_path / "runs" / "v02_test_run"
    assert load_product_spec(spec_path).id == "pan_tilt_2axis_demo"
    report = json.loads((run_dir / "validation_report.json").read_text())
    manifest = json.loads((run_dir / "artifact_manifest.json").read_text())
    assert report["run_id"] == "v02_test_run"
    assert report["product_spec_id"] == "pan_tilt_2axis_demo"
    assert manifest["run_id"] == "v02_test_run"
    assert manifest["product_spec_id"] == "pan_tilt_2axis_demo"
    assert report["artifacts"]["assembly_step"] == "assembly.step"
    assert (run_dir / "run_report.html").exists()


def test_workflow_registry_lists_and_selects_pan_tilt_demo():
    workflows = list_workflows()
    assert [workflow.workflow_id for workflow in workflows] == ["pan_tilt_2axis_demo"]
    assert supported_workflow_ids() == ("pan_tilt_2axis_demo",)
    fallback_spec = pan_tilt_2axis.product_spec()
    assert select_workflow(fallback_spec).workflow_id == "pan_tilt_2axis_demo"
    explicit_spec = fallback_spec.model_copy(update={"workflow_id": "pan_tilt_2axis_demo"})
    assert select_workflow(explicit_spec).template_id == "pan_tilt_2axis_demo"
    template_spec = fallback_spec.model_copy(update={"template_id": "pan_tilt_2axis_demo"})
    assert select_workflow(template_spec).workflow_id == "pan_tilt_2axis_demo"


def test_run_from_spec_accepts_explicit_workflow_id(tmp_path: Path):
    spec = pan_tilt_2axis.product_spec().model_copy(update={"workflow_id": "pan_tilt_2axis_demo"})
    spec_path = tmp_path / "explicit_spec.json"
    spec_path.write_text(spec.model_dump_json(indent=2))
    run_dir = run_from_spec(spec_path, run_id="v02_explicit_test", runs_root=tmp_path / "runs")
    report = json.loads((run_dir / "validation_report.json").read_text())
    assert report["run_id"] == "v02_explicit_test"
    assert report["status"] in {"pass", "warning"}


def test_run_from_spec_rejects_unknown_template(tmp_path: Path):
    spec = pan_tilt_2axis.product_spec().model_copy(update={"id": "unknown_demo"})
    spec_path = tmp_path / "unknown_spec.json"
    spec_path.write_text(spec.model_dump_json(indent=2))
    try:
        run_from_spec(spec_path, run_id="bad", runs_root=tmp_path / "runs")
    except ValueError as exc:
        message = str(exc)
        assert "No CADX workflow supports product_spec_id='unknown_demo'" in message
        assert "supported workflow IDs: pan_tilt_2axis_demo" in message
    else:
        raise AssertionError("unknown product spec template should fail")


def test_run_from_spec_rejects_unknown_explicit_workflow(tmp_path: Path):
    spec = pan_tilt_2axis.product_spec().model_copy(update={"workflow_id": "missing_workflow"})
    spec_path = tmp_path / "bad_workflow_spec.json"
    spec_path.write_text(spec.model_dump_json(indent=2))
    try:
        run_from_spec(spec_path, run_id="bad_workflow", runs_root=tmp_path / "runs")
    except ValueError as exc:
        message = str(exc)
        assert "Unknown CADX workflow/template 'missing_workflow'" in message
        assert "supported workflow IDs: pan_tilt_2axis_demo" in message
    else:
        raise AssertionError("unknown explicit workflow should fail")


def test_fallback_path_is_explicit(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(orchestrator, "build123d_available", lambda: (False, "forced unavailable"))
    run_dir = run_pan_tilt_demo(tmp_path / "fallback")
    report = json.loads((run_dir / "validation_report.json").read_text())
    assert report["status"] == "warning"
    assert report["metrics"]["geometry_backend"] == "placeholder"
    assert "forced unavailable" in "\n".join(report["warnings"])
    step_text = (run_dir / "custom_parts" / "base_bracket" / "part.step").read_text()
    assert "PLACEHOLDER" in step_text
    assembly_gate = next(g for g in report["gates"] if g["id"] == "assembly_step")
    assert assembly_gate["status"] == "warning"


def test_failure_classifier_maps_known_gate_families():
    report = orchestrator.ValidationReport(
        id="validation_broken",
        run_id="broken_run",
        product_spec_id="pan_tilt_2axis_demo",
        status="fail",
        gates=[
            orchestrator.ValidationGateResult(id="retrieved_part_metadata", name="metadata", status="fail", message="missing servo metadata"),
            orchestrator.ValidationGateResult(id="urdf_mesh_linkage", name="mesh", status="warning", message="mesh proxy degraded"),
            orchestrator.ValidationGateResult(id="preview_artifact", name="preview", status="fail", message="preview missing"),
            orchestrator.ValidationGateResult(id="unexpected_gate", name="unexpected", status="fail", message="internal validator failed"),
        ],
        metrics={},
    )
    plan = orchestrator.classify_validation_failures(report)
    assert plan.status == "blocked"
    assert plan.failure_count == 4
    classes = {action.source_gate_id: action.failure_class for action in plan.actions}
    assert classes["retrieved_part_metadata"] == "part_retrieval_metadata_failure"
    assert classes["urdf_mesh_linkage"] == "urdf_mesh_linkage_failure"
    assert classes["preview_artifact"] == "preview_artifact_failure"
    assert classes["unexpected_gate"] == "validation_internal_error"
    assert {action.status for action in plan.actions} == {"planned"}


def test_part_catalog_validation_rejects_unsafe_and_duplicate_seed_metadata(tmp_path: Path):
    run_dir = run_pan_tilt_demo(tmp_path / "catalog_integrity")
    catalog_path = run_dir / "part_catalog.json"
    catalog = json.loads(catalog_path.read_text())
    duplicate = dict(catalog["parts"][0])
    duplicate["original_step_path"] = "../escape.step"
    duplicate["checksum_sha256"] = "bad"
    catalog["parts"].append(duplicate)
    catalog_path.write_text(json.dumps(catalog))

    gate, metrics = orchestrator.validate_part_catalog(run_dir)
    assert gate.status == "fail"
    assert "duplicate catalog part id" in gate.message
    assert "invalid reference" in gate.message
    assert metrics["part_catalog_count"] == 2
