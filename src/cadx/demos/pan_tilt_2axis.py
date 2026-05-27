from __future__ import annotations

from cadx.schemas import (
    AssemblyComponent,
    AssemblyPlan,
    BOM,
    BOMItem,
    BBox,
    CustomPartRequest,
    DesignContract,
    Frame,
    Interface,
    InterfaceGeometry,
    JointLimits,
    JointOrigin,
    JointSpec,
    MateConstraint,
    PartRecord,
    ProductSpec,
    FunctionalRequirement,
    MotionRequirement,
    Transform,
)


COMPONENT_PLACEMENTS_MM = {
    "base_bracket": (0.0, 0.0, 0.0),
    "servo_pan": (0.0, 0.0, 22.0),
    "tilt_yoke": (0.0, -25.0, 52.0),
    "servo_tilt": (0.0, 20.0, 58.0),
    "camera_plate": (0.0, 0.0, 104.0),
}

JOINT_FRAME_COMPONENTS = {
    "pan_yaw": ("base_bracket", "tilt_yoke"),
    "tilt_pitch": ("tilt_yoke", "camera_plate"),
}


def product_spec() -> ProductSpec:
    return ProductSpec(
        id="pan_tilt_2axis_demo",
        name="2-axis pan-tilt camera mount",
        description="Two-servo pan-tilt mechanism assembled from retrieved STEP-like parts and generated adapters.",
        product_type="electromechanical_assembly",
        functional_requirements=[
            FunctionalRequirement(
                id="pan_axis",
                description="Rotate payload around vertical yaw axis",
                function_type="rotary_motion",
                required_motion=MotionRequirement(dof=1, axes=["yaw"], range_deg={"yaw": 180}),
            ),
            FunctionalRequirement(
                id="tilt_axis",
                description="Rotate payload around horizontal pitch axis",
                function_type="rotary_motion",
                required_motion=MotionRequirement(dof=1, axes=["pitch"], range_deg={"pitch": 120}),
            ),
        ],
        assumptions=[
            "Sprint 0 uses deterministic placeholder STEP text if build123d is unavailable.",
            "External STEP originals are immutable; generated adapters are editable placeholders.",
        ],
    )


def bom() -> BOM:
    return BOM(
        id="bom_pan_tilt_2axis",
        product_spec_id="pan_tilt_2axis_demo",
        items=[
            BOMItem(id="servo_pan", role="yaw actuator", part_query="standard hobby servo with output spline", selected_part_id="servo_mg996r", required_interfaces=["servo_output_spline", "servo_mount_tabs"], status="selected"),
            BOMItem(id="servo_tilt", role="pitch actuator", part_query="standard hobby servo with output spline", selected_part_id="servo_mg996r", required_interfaces=["servo_output_spline", "servo_mount_tabs"], status="selected"),
        ],
        generated_custom_parts=[
            CustomPartRequest(id="base_bracket", role="mount pan servo to base", description="Adapter bracket from base plate to pan servo mount tabs", required_interfaces=["base_mount_holes", "servo_mount_tabs"], design_contract_id="contract_base_bracket"),
            CustomPartRequest(id="tilt_yoke", role="connect pan output to tilt stage", description="Yoke bracket carrying tilt servo and camera plate", required_interfaces=["servo_output_spline", "camera_mount_pattern"], design_contract_id="contract_tilt_yoke"),
            CustomPartRequest(id="camera_plate", role="payload mount", description="Simple camera/payload mounting plate", required_interfaces=["camera_mount_pattern"], design_contract_id="contract_camera_plate"),
        ],
        notes=["Part RAG is deterministic metadata matching in Sprint 0."],
    )


def servo_part() -> PartRecord:
    return PartRecord(
        id="servo_mg996r",
        name="MG996R hobby servo placeholder",
        source="placeholder",
        category="actuator",
        original_step_path="original.step",
        normalized_step_path="normalized.step",
        metadata={
            "source_id": "placeholder:mg996r:v1",
            "source_uri": "cadx://placeholder/vendor/mg996r.step",
            "manufacturer": "TowerPro-compatible placeholder",
            "model": "MG996R",
            "rag_score": 1.0,
            "rag_query": "standard hobby servo with output spline",
            "interface_tags": ["servo_output_spline", "servo_mount_tabs"],
            "dimension_tags": ["40x20x40mm_body", "48x10mm_mount_tabs", "6mm_output_spline"],
            "contract_references": ["bom:servo_pan", "bom:servo_tilt", "assembly:servo_pan", "assembly:servo_tilt"],
            "immutable_policy": "original STEP copied only; never edited or referenced directly by derived URDF meshes",
        },
        bbox_mm=BBox(x=40, y=20, z=40),
        interfaces=[
            Interface(id="servo_output_spline", name="Servo output spline proxy", type="servo_spline", frame=Frame(origin_mm=(0, 0, 22)), geometry=InterfaceGeometry(kind="spline", parameters={"diameter_mm": 6})),
            Interface(id="servo_mount_tabs", name="Servo mounting tabs", type="mounting_hole_pattern", frame=Frame(origin_mm=(0, 0, 0)), geometry=InterfaceGeometry(kind="hole_pattern", parameters={"holes": 4, "diameter_mm": 3, "spacing_mm": [48, 10]})),
        ],
        immutable_original=True,
    )


CUSTOM_PART_INTERFACES = {
    "base_bracket": [
        Interface(id="base_mount_holes", name="Base mounting holes", type="mounting_hole_pattern", frame=Frame(origin_mm=(0, 0, 0)), geometry=InterfaceGeometry(kind="hole_pattern", parameters={"holes": 4, "diameter_mm": 4, "spacing_mm": [70, 50]})),
        Interface(id="servo_mount_tabs", name="Pan servo tab mounting pattern", type="mounting_hole_pattern", frame=Frame(origin_mm=(0, 0, 18)), geometry=InterfaceGeometry(kind="hole_pattern", parameters={"holes": 4, "diameter_mm": 3, "spacing_mm": [48, 10]})),
    ],
    "tilt_yoke": [
        Interface(id="servo_output_spline", name="Pan servo spline receiver", type="servo_spline", frame=Frame(origin_mm=(0, -25, 45)), geometry=InterfaceGeometry(kind="spline", parameters={"diameter_mm": 6})),
        Interface(id="camera_mount_pattern", name="Tilt camera plate hinge pattern", type="mounting_hole_pattern", frame=Frame(origin_mm=(0, 25, 33)), geometry=InterfaceGeometry(kind="hole_pattern", parameters={"holes": 4, "diameter_mm": 3, "spacing_mm": [40, 30]})),
    ],
    "camera_plate": [
        Interface(id="camera_mount_pattern", name="Payload mounting pattern", type="mounting_hole_pattern", frame=Frame(origin_mm=(0, 0, 3)), geometry=InterfaceGeometry(kind="hole_pattern", parameters={"holes": 4, "diameter_mm": 3, "spacing_mm": [40, 30]})),
    ],
}


def custom_interfaces(part_id: str) -> list[Interface]:
    return CUSTOM_PART_INTERFACES[part_id]


def custom_contract(part_id: str, locked: list[str]) -> DesignContract:
    invariants = []
    for interface in custom_interfaces(part_id):
        if interface.id in locked:
            invariants.append({"type": "interface_pose", "target": interface.id, "value": {"origin_mm": interface.frame.origin_mm, "x_axis": interface.frame.x_axis, "y_axis": interface.frame.y_axis, "z_axis": interface.frame.z_axis}, "tolerance_mm": 0.05})
            invariants.append({"type": "hole_pattern" if interface.geometry.kind == "hole_pattern" else "axis_alignment", "target": interface.id, "value": interface.geometry.parameters, "tolerance_mm": 0.05})
    return DesignContract(
        id=f"contract_{part_id}",
        target_part_id=part_id,
        contract_type="adapter_part",
        locked_interfaces=locked,
        geometric_invariants=invariants,
        allowed_operations=["generate_adapter", "translate", "rotate"],
        forbidden_operations=["edit_external_original_step", "break_locked_interfaces"],
    )


def joints() -> list[JointSpec]:
    return [
        JointSpec(id="joint_pan_yaw", name="pan_yaw", type="revolute", parent="base_link", child="pan_link", origin=JointOrigin(xyz_mm=(0, 0, 45)), axis=(0, 0, 1), limits=JointLimits(lower_deg=-90, upper_deg=90, effort=1.0, velocity=2.0)),
        JointSpec(id="joint_tilt_pitch", name="tilt_pitch", type="revolute", parent="pan_link", child="tilt_link", origin=JointOrigin(xyz_mm=(0, 0, 85)), axis=(0, 1, 0), limits=JointLimits(lower_deg=-60, upper_deg=60, effort=1.0, velocity=2.0)),
    ]


def assembly_plan() -> AssemblyPlan:
    js = joints()
    return AssemblyPlan(
        id="assembly_pan_tilt_2axis",
        product_spec_id="pan_tilt_2axis_demo",
        bom_id="bom_pan_tilt_2axis",
        components=[
            AssemblyComponent(id="base_bracket", part_record_id="base_bracket", role="base adapter", instance_name="base_link", initial_transform=Transform(translation_mm=COMPONENT_PLACEMENTS_MM["base_bracket"]), fixed=True),
            AssemblyComponent(id="servo_pan", part_record_id="servo_mg996r", role="pan servo", instance_name="pan_servo", initial_transform=Transform(translation_mm=COMPONENT_PLACEMENTS_MM["servo_pan"])),
            AssemblyComponent(id="tilt_yoke", part_record_id="tilt_yoke", role="tilt adapter", instance_name="pan_link", initial_transform=Transform(translation_mm=COMPONENT_PLACEMENTS_MM["tilt_yoke"])),
            AssemblyComponent(id="servo_tilt", part_record_id="servo_mg996r", role="tilt servo", instance_name="tilt_servo", initial_transform=Transform(translation_mm=COMPONENT_PLACEMENTS_MM["servo_tilt"])),
            AssemblyComponent(id="camera_plate", part_record_id="camera_plate", role="payload mount", instance_name="tilt_link", initial_transform=Transform(translation_mm=COMPONENT_PLACEMENTS_MM["camera_plate"])),
        ],
        mates=[
            MateConstraint(id="mate_base_to_pan_servo", parent_component="base_bracket", parent_interface="servo_mount_tabs", child_component="servo_pan", child_interface="servo_mount_tabs", type="fixed"),
            MateConstraint(id="mate_pan_to_yoke", parent_component="servo_pan", parent_interface="servo_output_spline", child_component="tilt_yoke", child_interface="servo_output_spline", type="revolute"),
            MateConstraint(id="mate_yoke_to_camera", parent_component="tilt_yoke", parent_interface="camera_mount_pattern", child_component="camera_plate", child_interface="camera_mount_pattern", type="revolute"),
        ],
        joints=js,
        generated_parts=["base_bracket", "tilt_yoke", "camera_plate"],
    )
