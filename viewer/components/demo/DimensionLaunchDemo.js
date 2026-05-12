import { useEffect, useMemo, useRef, useState } from "react";
import {
  Box,
  Check,
  ChevronDown,
  Circle,
  Download,
  ExternalLink,
  FileText,
  GitBranch,
  Globe,
  Loader2,
  MousePointer2,
  PanelRight,
  Plus,
  RefreshCw,
  Ruler,
  Send,
  ShieldCheck,
  Square,
  Target,
  X,
} from "lucide-react";
import CadViewer from "../CadViewer";
import brandLogoUrl from "../../app/brand-logo.svg";
import { GLB_COORDINATE_SPACE, loadRenderGlb } from "../../lib/renderAssetClient";
import { DEFAULT_LOOK_SETTINGS, LOOK_FLOOR_MODES } from "../../lib/lookSettings";
import { VIEWER_PICK_MODE } from "../../lib/viewer/constants";

const DEFAULT_PROMPT = "";

const DEFAULT_ATTACHMENTS = [];

const RUN_MODES = {
  MODEL: "model",
  VALIDATE: "validate",
};

const MODE_OPTIONS = [RUN_MODES.MODEL, RUN_MODES.VALIDATE];
const EMPTY_VIEWER_ITEMS = Object.freeze([]);

const VALIDATE_ASSET_INDEX = 4;
const VALIDATE_DRAWING_IMAGE = "/benchmarks/drawings/model_009.png";
const VALIDATE_LINKAGE_ASSET_ID = "model-009-linkage-assembly";
const VALIDATE_LINKAGE_DEFAULT_ANGLE = 54;
const VALIDATE_LINKAGE_MIN_ANGLE = 38;
const VALIDATE_LINKAGE_MAX_ANGLE = 68;

const VALIDATE_PROMPT = "Validate model_009_linkage_assembly.step against ASME Y14.5. Detect plate, slot, pin, and hole features, propose A/B/C datums, generate GD&T recommendations, and prepare the evaluator report.";

const VALIDATE_ATTACHMENTS = [];

const DIMENSION_DEMO_THEME = {
  "--dd-bg": "#fafafa",
  "--dd-panel": "#ffffff",
  "--dd-panel-muted": "#f5f5f5",
  "--dd-control": "#ffffff",
  "--dd-control-hover": "#f5f5f5",
  "--dd-border": "#e5e5e5",
  "--dd-border-strong": "#d4d4d4",
  "--dd-fg": "#0a0a0a",
  "--dd-fg-muted": "#404040",
  "--dd-fg-subtle": "#737373",
  "--dd-fg-faint": "#a3a3a3",
  "--dd-accent": "#0090ff",
  "--dd-accent-deep": "#0d74ce",
  "--dd-blueprint": "#0066cc",
  "--dd-success": "#16a34a",
  "--dd-danger": "#dc2626",
  "--dd-render-bg": "#f5f5f5",
  "--dd-radius-control": "6px",
  "--dd-radius-panel": "10px",
  "--dd-font-display": "\"Geist\", \"Inter\", ui-sans-serif, system-ui, -apple-system, \"Segoe UI\", sans-serif",
  "--dd-font-sans": "\"Inter\", \"Geist\", ui-sans-serif, system-ui, -apple-system, \"Segoe UI\", sans-serif",
  "--dd-font-mono": "\"Geist Mono\", \"JetBrains Mono\", ui-monospace, \"SF Mono\", Menlo, Consolas, monospace",
  fontFamily: "var(--dd-font-sans)",
};

const BOOPALAN_ASSET_START_INDEX = 5;

const BOOPALAN_MODEL_SPECS = Object.freeze([
  {
    number: "001",
    sourceName: "[001]MODEL-1.pdf",
    resultName: "boopalan_model_001.stp",
    dimensions: "102.0 x 182.0 x 98.0 mm envelope, 65 faces, 139 edges",
    cameraFitScale: 1.42,
  },
  {
    number: "002",
    sourceName: "[002]MODEL-2.pdf",
    resultName: "boopalan_model_002.stp",
    dimensions: "150.0 x 88.0 x 120.0 mm envelope, 64 faces, 180 edges",
    cameraFitScale: 1.62,
  },
  {
    number: "003",
    sourceName: "[003]MODEL-3.pdf",
    resultName: "boopalan_model_003.stp",
    dimensions: "80.0 x 100.0 x 154.0 mm envelope, 53 faces, 141 edges",
    cameraFitScale: 1.42,
  },
  {
    number: "004",
    sourceName: "[004]MODEL-4.pdf",
    resultName: "boopalan_model_004.stp",
    dimensions: "45.0 x 90.0 x 40.5 mm envelope, 156 faces, 354 edges",
  },
  {
    number: "005",
    sourceName: "[005]MODEL-5.pdf",
    resultName: "boopalan_model_005.stp",
    dimensions: "145.8 x 63.8 x 25.0 mm envelope, 41 faces, 107 edges",
  },
  {
    number: "006",
    sourceName: "[006]MODEL-6.pdf",
    resultName: "boopalan_model_006.stp",
    dimensions: "57.5 x 110.3 x 78.7 mm envelope, 44 faces, 122 edges",
    cameraFitScale: 1.34,
  },
  {
    number: "007",
    sourceName: "[007]MODEL-7.pdf",
    resultName: "boopalan_model_007.stp",
    dimensions: "223.7 x 94.0 x 38.0 mm envelope, 47 faces, 120 edges",
  },
  {
    number: "008",
    sourceName: "[008]MODEL-8.pdf",
    resultName: "boopalan_model_008.stp",
    dimensions: "49.8 x 49.8 x 72.0 mm envelope, 78 faces, 205 edges",
  },
  {
    number: "009",
    sourceName: "[009]MODEL-9.pdf",
    resultName: "boopalan_model_009.stp",
    dimensions: "235.5 x 127.4 x 20.0 mm envelope, 140 faces, 336 edges",
    cameraFitScale: 1.36,
  },
  {
    number: "010",
    sourceName: "[010]MODEL-10.pdf",
    resultName: "boopalan_model_010.stp",
    dimensions: "137.0 x 60.0 x 50.0 mm envelope, 46 faces, 145 edges",
  },
]);

const ASSETS = [
  {
    id: "model-006",
    label: "model_006_pipe_elbow.step",
    path: "/models/benchmarks/.model_006_pipe_elbow.step/model.glb",
    url: "app.dimension-cad.com/model/model_006_pipe_elbow.step",
  },
  {
    id: "model-006-revision-01",
    label: "model_006_pipe_elbow_revision_01.step",
    path: "/models/demo/.model_006_pipe_elbow_revision_01.step/model.glb",
    url: "app.dimension-cad.com/model/model_006_pipe_elbow_revision_01.step",
  },
  {
    id: "model-006-revision-02",
    label: "model_006_pipe_elbow_revision_02.step",
    path: "/models/demo/.model_006_pipe_elbow_revision_02.step/model.glb",
    url: "app.dimension-cad.com/model/model_006_pipe_elbow_revision_02.step",
  },
  {
    id: "model-006-revision-03",
    label: "model_006_pipe_elbow_revision_03.step",
    path: "/models/demo/.model_006_pipe_elbow_revision_03.step/model.glb",
    url: "app.dimension-cad.com/model/model_006_pipe_elbow_revision_03.step",
  },
  {
    id: "model-009-linkage-assembly",
    label: "model_009_linkage_assembly.step",
    path: "/models/demo/.model_009_linkage_assembly.step/model.glb",
    url: "app.dimension-cad.com/validate/model_009_linkage_assembly.step",
  },
  ...BOOPALAN_MODEL_SPECS.map((spec) => ({
    id: `boopalan-model-${spec.number}`,
    label: spec.resultName,
    path: `/models/demo/boopalan/.${spec.resultName}/model.glb`,
    url: `app.dimension-cad.com/model/${spec.resultName}`,
    floorOffset: spec.floorOffset ?? -56,
    cameraFitScale: spec.cameraFitScale ?? 1.24,
  })),
];

const RUN_STEPS = [
  {
    atMs: 220,
    assetIndex: 0,
    text: "I'll use the attached MODEL-006 drawing as the input and build a parametric CAD source under models/benchmarks.",
    meta: "Loaded benchmarks/drawings/model_006.pdf",
  },
  {
    atMs: 780,
    assetIndex: 0,
    text: "Extracted the main dimensions: front flange Ø57.5, bolt pattern Ø47.15 with 4x Ø5, pipe OD 20 / ID 15, and top flange 50 x 40.",
    meta: "Parsed drawing dimensions",
  },
  {
    atMs: 1350,
    assetIndex: 0,
    text: "Built the build123d source with hollow pipe runs, a swept elbow bend, service port, raised front face, and rounded top flange.",
    meta: "Generated model_006_pipe_elbow.step",
  },
  {
    atMs: 2050,
    assetIndex: 0,
    text: "CoMeT stored the drawing interpretation and linked the PDF input to the generated CAD target for future iterations.",
    meta: "Updated source, STEP, GLB, topology",
  },
  {
    atMs: 2850,
    assetIndex: 0,
    text: "Evaluator passed: valid shape, drawing-derived bounding box, swept bend surfaces, bolt holes, STEP, GLB, and topology ready.",
    meta: "Completed in 7m 12s",
    done: true,
  },
];

const MODEL_REVISION_RUNS = [
  {
    assetIndex: 0,
    runSteps: RUN_STEPS,
    elapsedRunning: "Working for 4m 38s",
    elapsedDone: "Completed in 7m 12s",
    readyMessage: "STEP, GLB, topology, and evaluator report ready",
  },
  {
    assetIndex: 1,
    startAssetIndex: 0,
    runSteps: [
      {
        atMs: 180,
        assetIndex: 0,
        text: "I’ll update the generated CAD source instead of rebuilding from scratch, preserving the pipe, bore, bend, and front flange references.",
        meta: "Loaded model_006_pipe_elbow.py context",
      },
      {
        atMs: 720,
        assetIndex: 0,
        text: "Expanded the top rectangular flange from 50 x 40 mm to 60 x 45 mm and moved the corner bolt pattern to 48 x 34 mm.",
        meta: "Edited top flange parameters",
      },
      {
        atMs: 1420,
        assetIndex: 1,
        text: "Regenerated the revision STEP, GLB, and topology with the larger top mounting interface.",
        meta: "Generated model_006_pipe_elbow_revision_01.step",
      },
      {
        atMs: 2140,
        assetIndex: 1,
        text: "Evaluator passed: bolt holes remain inside edge clearance, pipe bore stays aligned, and the top flange plane is valid.",
        meta: "Completed in 1m 16s",
        done: true,
      },
    ],
    elapsedRunning: "Applying revision 1",
    elapsedDone: "Revision 1 completed in 1m 16s",
    readyMessage: "Revision ready: top flange enlarged and bolt pattern updated",
  },
  {
    assetIndex: 2,
    startAssetIndex: 1,
    runSteps: [
      {
        atMs: 180,
        assetIndex: 1,
        text: "I’ll keep the revised 60 x 45 mm flange footprint and reroute the outlet instead of changing the inlet geometry.",
        meta: "Loaded revision 01",
      },
      {
        atMs: 780,
        assetIndex: 1,
        text: "Added a second 90 degree bend at the top of the riser, turning the outlet into a horizontal side exit with the same OD 20 mm / ID 15 mm pipe.",
        meta: "Inserted second swept bend",
      },
      {
        atMs: 1500,
        assetIndex: 2,
        text: "Moved the rectangular mounting flange onto the new horizontal outlet and regenerated STEP, GLB, and topology.",
        meta: "Generated model_006_pipe_elbow_revision_02.step",
      },
      {
        atMs: 2240,
        assetIndex: 2,
        text: "Evaluator passed: the two swept bends are tangent, the side outlet is a single solid, and the bolt pattern stays valid.",
        meta: "Completed in 1m 22s",
        done: true,
      },
    ],
    elapsedRunning: "Applying revision 2",
    elapsedDone: "Revision 2 completed in 1m 22s",
    readyMessage: "Revision ready: second 90 degree outlet bend added",
  },
  {
    assetIndex: 3,
    startAssetIndex: 2,
    runSteps: [
      {
        atMs: 180,
        assetIndex: 2,
        text: "I’ll reinforce the inlet side without changing the new side outlet, bore, or bolt count from the previous revisions.",
        meta: "Loaded revision 02",
      },
      {
        atMs: 820,
        assetIndex: 2,
        text: "Increased the front circular flange OD from 57.5 mm to 64 mm and thickness from 5 mm to 8 mm.",
        meta: "Edited front flange envelope",
      },
      {
        atMs: 1580,
        assetIndex: 3,
        text: "Regenerated the final STEP, GLB, topology, and evaluator report with the reinforced front flange.",
        meta: "Generated model_006_pipe_elbow_revision_03.step",
      },
      {
        atMs: 2320,
        assetIndex: 3,
        text: "Evaluator passed: bore clearance, bolt PCD, solid validity, and updated bounding box all check out.",
        meta: "Completed in 1m 31s",
        done: true,
      },
    ],
    elapsedRunning: "Applying final revision",
    elapsedDone: "Final revision completed in 1m 31s",
    readyMessage: "Final revision ready: inlet flange reinforced",
  },
];

const BATCH_DRAWING_FIXTURES = BOOPALAN_MODEL_SPECS.map((spec, index) => ({
  id: `boopalan-model-${spec.number}`,
  modelNumber: spec.number,
  sourceName: spec.sourceName,
  assetIndex: BOOPALAN_ASSET_START_INDEX + index,
  resultName: spec.resultName,
  description: `BOOPALAN model ${spec.number} imported from the supplied STEP target`,
  dimensions: spec.dimensions,
  artifacts: "STEP, GLB, topology, inspection summary",
}));

const BATCH_ITEM_PHASES = [
  { atMs: 260, status: "running", phase: "Parsing PDF", progress: 18, meta: "Drawing parsed" },
  { atMs: 1220, status: "running", phase: "Extracting dimensions", progress: 42, meta: "Dimensions extracted" },
  { atMs: 2420, status: "running", phase: "Generating CAD", progress: 72, meta: "CAD model generated" },
  { atMs: 3540, status: "running", phase: "Validating geometry", progress: 90, meta: "Evaluator running" },
  { atMs: 4560, status: "done", phase: "Ready", progress: 100, meta: "Artifacts ready", done: true },
];

const VALIDATE_RUN_STEPS = [
  {
    atMs: 220,
    assetIndex: VALIDATE_ASSET_INDEX,
    text: "Loaded the MODEL-009 STEP assembly and indexed plate, slot, pin, and hole features from the topology manifest.",
    meta: "Imported model_009_linkage_assembly.step",
  },
  {
    atMs: 820,
    assetIndex: VALIDATE_ASSET_INDEX,
    text: "Detected 42 candidate manufacturing features and grouped repeated pivot holes, long slots, spacers, plate faces, and datum-quality planes.",
    meta: "Feature graph ready",
  },
  {
    atMs: 1420,
    assetIndex: VALIDATE_ASSET_INDEX,
    text: "Proposed datum scheme A/B/C from the base plate top face, left pivot axis, and link center plane.",
    meta: "Datums proposed",
  },
  {
    atMs: 2240,
    assetIndex: VALIDATE_ASSET_INDEX,
    text: "Generated GD&T suggestions for slot position, pivot bore position, profile control, flatness, pin diameter limits, and drawing callout placement.",
    meta: "ASME Y14.5 rule pass",
  },
  {
    atMs: 3180,
    assetIndex: VALIDATE_ASSET_INDEX,
    text: "Validation package is ready with confirmed features, datums, annotated drawing, DXF export, and evaluator report.",
    meta: "Completed in 3m 46s",
    done: true,
  },
];

const MODE_CONFIG = {
  [RUN_MODES.MODEL]: {
    label: "Model",
    heading: "What should we model?",
    idleStatus: "agentic CAD modeling",
    activeStatus: "generating editable CAD",
    statusLabel: "model locally",
    prompt: DEFAULT_PROMPT,
    attachments: DEFAULT_ATTACHMENTS,
    acceptedFileTypes: "image/*,.pdf",
    placeholder: "Describe a part or attach a drawing...",
    runSteps: RUN_STEPS,
    elapsedRunning: "Working for 4m 38s",
    elapsedDone: "Completed in 7m 12s",
    readyMessage: "STEP, GLB, topology, and evaluator report ready",
    followUpPlaceholder: "Ask for follow-up changes",
  },
  [RUN_MODES.VALIDATE]: {
    label: "Validate",
    heading: "What should we validate?",
    idleStatus: "CAD validation",
    activeStatus: "validating CAD",
    statusLabel: "validate locally",
    prompt: VALIDATE_PROMPT,
    attachments: VALIDATE_ATTACHMENTS,
    acceptedFileTypes: ".step,.stp,.glb,.stl,.dxf,.pdf,image/*",
    assetIndex: VALIDATE_ASSET_INDEX,
    startAssetIndex: VALIDATE_ASSET_INDEX,
    runSteps: VALIDATE_RUN_STEPS,
    elapsedRunning: "Working for 2m 18s",
    elapsedDone: "Completed in 3m 46s",
    readyMessage: "Features, datums, GD&T suggestions, and report ready",
    followUpPlaceholder: "Ask for tolerance or report changes",
  },
};

const VALIDATION_STEPS = ["Import", "Features", "Datums", "Review", "Export"];

const VALIDATION_FEATURES = [
  { id: "pivot-bores", label: "4x pivot bore Ø10.0", kind: "hole", color: "#2563eb", status: "confirmed" },
  { id: "slotted-links", label: "2x long link slot", kind: "slot", color: "#16a34a", status: "confirmed" },
  { id: "base-face", label: "Base plate face", kind: "plane", color: "#ef4444", status: "datum" },
  { id: "triangular-cutout", label: "Triangular cutout", kind: "profile", color: "#a855f7", status: "review" },
  { id: "pin-stack", label: "4x spacer pin stack", kind: "cylinder", color: "#f59e0b", status: "review" },
];

const VALIDATION_DATUMS = [
  { id: "A", label: "base plate top face", color: "#ef4444" },
  { id: "B", label: "left pivot axis", color: "#2563eb" },
  { id: "C", label: "link center plane", color: "#16a34a" },
];

const VALIDATE_LINKAGE_PART_SOURCES = [
  { key: "base", path: "/models/demo/model_009_linkage_parts/.model_009_part_01_base_plate.step/model.glb" },
  { key: "upperLink", path: "/models/demo/model_009_linkage_parts/.model_009_part_02_link.step/model.glb" },
  { key: "shortLink", path: "/models/demo/model_009_linkage_parts/.model_009_part_03_short_link.step/model.glb" },
  { key: "lowerLink", path: "/models/demo/model_009_linkage_parts/.model_009_part_04_link.step/model.glb" },
  { key: "jointPin", path: "/models/demo/model_009_linkage_parts/.model_009_part_05_pin.step/model.glb" },
  { key: "basePin", path: "/models/demo/model_009_linkage_parts/.model_009_part_06_pin.step/model.glb" },
];

const LINKAGE_TOP_FIXED_PIVOT = Object.freeze({ x: -4, y: 81 });
const LINKAGE_LOWER_FIXED_PIVOT = Object.freeze({ x: 77, y: 0 });
const LINKAGE_SHORT_LENGTH = 30;
const LINKAGE_LONG_LENGTH = 130;

function degreesToRadians(degrees) {
  return (Number(degrees || 0) * Math.PI) / 180;
}

function distance2d(left, right) {
  return Math.hypot(right.x - left.x, right.y - left.y);
}

function midpoint2d(left, right) {
  return {
    x: (left.x + right.x) / 2,
    y: (left.y + right.y) / 2,
  };
}

function angleBetween2d(left, right) {
  return Math.atan2(right.y - left.y, right.x - left.x);
}

function solveCircleIntersection(leftCenter, leftRadius, rightCenter, rightRadius) {
  const dx = rightCenter.x - leftCenter.x;
  const dy = rightCenter.y - leftCenter.y;
  const distance = Math.hypot(dx, dy);
  if (distance < 1e-6) {
    return null;
  }
  const clampedDistance = Math.min(
    Math.max(distance, Math.abs(leftRadius - rightRadius) + 1e-3),
    leftRadius + rightRadius - 1e-3
  );
  const ux = dx / distance;
  const uy = dy / distance;
  const along = ((leftRadius * leftRadius) - (rightRadius * rightRadius) + (clampedDistance * clampedDistance)) / (2 * clampedDistance);
  const heightSquared = Math.max((leftRadius * leftRadius) - (along * along), 0);
  const height = Math.sqrt(heightSquared);
  const baseX = leftCenter.x + (ux * along);
  const baseY = leftCenter.y + (uy * along);
  const first = {
    x: baseX + (-uy * height),
    y: baseY + (ux * height),
  };
  const second = {
    x: baseX - (-uy * height),
    y: baseY - (ux * height),
  };
  return first.y >= second.y ? first : second;
}

function linkagePoseFromAngle(angleDeg) {
  const lowerAngle = degreesToRadians(angleDeg);
  const topPivot = LINKAGE_TOP_FIXED_PIVOT;
  const lowerPivot = LINKAGE_LOWER_FIXED_PIVOT;
  const rightJoint = {
    x: lowerPivot.x + (LINKAGE_LONG_LENGTH * Math.cos(lowerAngle)),
    y: lowerPivot.y + (LINKAGE_LONG_LENGTH * Math.sin(lowerAngle)),
  };
  const middleJoint = solveCircleIntersection(
    topPivot,
    LINKAGE_SHORT_LENGTH,
    rightJoint,
    LINKAGE_LONG_LENGTH
  ) || {
    x: topPivot.x + (LINKAGE_SHORT_LENGTH * Math.cos(lowerAngle)),
    y: topPivot.y + (LINKAGE_SHORT_LENGTH * Math.sin(lowerAngle)),
  };
  return {
    topPivot,
    lowerPivot,
    middleJoint,
    rightJoint,
    shortAngle: angleBetween2d(topPivot, middleJoint),
    upperAngle: angleBetween2d(middleJoint, rightJoint),
    lowerAngle,
  };
}

function makeTransform({ x = 0, y = 0, z = 0, angle = 0, scaleZ = 1 } = {}) {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  return [
    cos, -sin, 0, x,
    sin, cos, 0, y,
    0, 0, scaleZ, z,
    0, 0, 0, 1,
  ];
}

function transformPoint(matrix, x, y, z) {
  return [
    (matrix[0] * x) + (matrix[1] * y) + (matrix[2] * z) + matrix[3],
    (matrix[4] * x) + (matrix[5] * y) + (matrix[6] * z) + matrix[7],
    (matrix[8] * x) + (matrix[9] * y) + (matrix[10] * z) + matrix[11],
  ];
}

function transformNormal(matrix, x, y, z) {
  const nx = (matrix[0] * x) + (matrix[1] * y) + (matrix[2] * z);
  const ny = (matrix[4] * x) + (matrix[5] * y) + (matrix[6] * z);
  const nz = (matrix[8] * x) + (matrix[9] * y) + (matrix[10] * z);
  const length = Math.hypot(nx, ny, nz) || 1;
  return [nx / length, ny / length, nz / length];
}

function emptyBounds() {
  return {
    min: [Infinity, Infinity, Infinity],
    max: [-Infinity, -Infinity, -Infinity],
  };
}

function expandBounds(bounds, x, y, z) {
  bounds.min[0] = Math.min(bounds.min[0], x);
  bounds.min[1] = Math.min(bounds.min[1], y);
  bounds.min[2] = Math.min(bounds.min[2], z);
  bounds.max[0] = Math.max(bounds.max[0], x);
  bounds.max[1] = Math.max(bounds.max[1], y);
  bounds.max[2] = Math.max(bounds.max[2], z);
}

function finalizeBounds(bounds) {
  if (!bounds.min.every(Number.isFinite) || !bounds.max.every(Number.isFinite)) {
    return { min: [0, 0, 0], max: [0, 0, 0] };
  }
  return bounds;
}

function appendTransformedMesh(accumulator, sourceMesh, occurrence) {
  if (!sourceMesh?.vertices?.length || !sourceMesh?.indices?.length) {
    return;
  }
  const vertexOffset = Math.floor(accumulator.vertices.length / 3);
  const triangleOffset = Math.floor(accumulator.indices.length / 3);
  const partBounds = emptyBounds();
  for (let index = 0; index + 2 < sourceMesh.vertices.length; index += 3) {
    const [x, y, z] = transformPoint(
      occurrence.transform,
      Number(sourceMesh.vertices[index] || 0),
      Number(sourceMesh.vertices[index + 1] || 0),
      Number(sourceMesh.vertices[index + 2] || 0)
    );
    accumulator.vertices.push(x, y, z);
    expandBounds(partBounds, x, y, z);
    expandBounds(accumulator.bounds, x, y, z);
    if (sourceMesh.normals?.length === sourceMesh.vertices.length) {
      const [nx, ny, nz] = transformNormal(
        occurrence.transform,
        Number(sourceMesh.normals[index] || 0),
        Number(sourceMesh.normals[index + 1] || 0),
        Number(sourceMesh.normals[index + 2] || 0)
      );
      accumulator.normals.push(nx, ny, nz);
    } else {
      accumulator.normals.push(0, 0, 1);
    }
  }
  for (let index = 0; index < sourceMesh.indices.length; index += 1) {
    accumulator.indices.push(vertexOffset + Number(sourceMesh.indices[index] || 0));
  }
  const vertexCount = Math.floor(sourceMesh.vertices.length / 3);
  accumulator.parts.push({
    id: occurrence.id,
    occurrenceId: occurrence.id,
    name: occurrence.label,
    label: occurrence.label,
    nodeType: "part",
    color: "",
    bounds: finalizeBounds(partBounds),
    vertexOffset,
    vertexCount,
    triangleOffset,
    triangleCount: Math.floor(sourceMesh.indices.length / 3),
    edgeIndexOffset: 0,
    edgeIndexCount: 0,
  });
}

function buildValidationLinkageMeshData(sourceMeshes, angleDeg) {
  const pose = linkagePoseFromAngle(angleDeg);
  const shortMidpoint = midpoint2d(pose.topPivot, pose.middleJoint);
  const upperMidpoint = midpoint2d(pose.middleJoint, pose.rightJoint);
  const lowerMidpoint = midpoint2d(pose.lowerPivot, pose.rightJoint);
  const occurrences = [
    {
      id: "part-01-base-plate",
      label: "PART-1 base plate",
      sourceKey: "base",
      transform: makeTransform(),
    },
    {
      id: "part-06-top-fixed-pin",
      label: "PART-6 top fixed pin",
      sourceKey: "basePin",
      transform: makeTransform({ x: pose.topPivot.x, y: pose.topPivot.y, z: 10 }),
    },
    {
      id: "part-06-lower-fixed-pin",
      label: "PART-6 lower fixed pin",
      sourceKey: "basePin",
      transform: makeTransform({ x: pose.lowerPivot.x, y: pose.lowerPivot.y, z: 10 }),
    },
    {
      id: "part-03-short-coupler",
      label: "PART-3 short coupler",
      sourceKey: "shortLink",
      transform: makeTransform({ x: shortMidpoint.x, y: shortMidpoint.y, z: 17.5, angle: pose.shortAngle }),
    },
    {
      id: "part-02-upper-link",
      label: "PART-2 upper link",
      sourceKey: "upperLink",
      transform: makeTransform({ x: upperMidpoint.x, y: upperMidpoint.y, z: 22.5, angle: pose.upperAngle }),
    },
    {
      id: "part-04-lower-link",
      label: "PART-4 lower link",
      sourceKey: "lowerLink",
      transform: makeTransform({ x: lowerMidpoint.x, y: lowerMidpoint.y, z: 12.5, angle: pose.lowerAngle }),
    },
    {
      id: "part-05-middle-joint-pin",
      label: "PART-5 middle joint pin",
      sourceKey: "jointPin",
      transform: makeTransform({ x: pose.middleJoint.x, y: pose.middleJoint.y, z: 12.5, scaleZ: 1.5 }),
    },
    {
      id: "part-05-right-joint-pin",
      label: "PART-5 right joint pin",
      sourceKey: "jointPin",
      transform: makeTransform({ x: pose.rightJoint.x, y: pose.rightJoint.y, z: 12.5, scaleZ: 1.5 }),
    },
  ];
  const accumulator = {
    vertices: [],
    indices: [],
    normals: [],
    parts: [],
    bounds: emptyBounds(),
  };
  for (const occurrence of occurrences) {
    appendTransformedMesh(accumulator, sourceMeshes[occurrence.sourceKey], occurrence);
  }
  const vertices = new Float32Array(accumulator.vertices);
  return {
    vertices,
    indices: new Uint32Array(accumulator.indices),
    normals: new Float32Array(accumulator.normals),
    colors: new Float32Array(0),
    edge_indices: new Uint32Array(0),
    bounds: finalizeBounds(accumulator.bounds),
    parts: accumulator.parts,
    has_source_colors: false,
    sourceColor: "",
  };
}

function modeConfig(mode) {
  return MODE_CONFIG[mode] || MODE_CONFIG[RUN_MODES.MODEL];
}

function runConfigForMode(mode, modelRevisionIndex = 0) {
  const baseConfig = modeConfig(mode);
  if (mode !== RUN_MODES.MODEL) {
    return baseConfig;
  }
  const revisionConfig = MODEL_REVISION_RUNS[Math.min(modelRevisionIndex, MODEL_REVISION_RUNS.length - 1)] || MODEL_REVISION_RUNS[0];
  return {
    ...baseConfig,
    ...revisionConfig,
  };
}

function defaultAttachmentsForMode(mode) {
  return modeConfig(mode).attachments.map((attachment) => ({ ...attachment }));
}

function isPdfAttachment(attachment) {
  return String(attachment?.kind || "").toUpperCase() === "PDF" || /\.pdf$/i.test(attachment?.name || "");
}

function modelNumberFromAttachmentName(name) {
  const rawName = String(name || "");
  const bracketMatch = rawName.match(/\[(\d{1,3})\]/);
  const modelMatch = rawName.match(/model[-_\s]?(\d{1,3})/i);
  const fallbackMatch = rawName.match(/(?:^|[^\d])(\d{1,3})(?:[^\d]|$)/);
  const numeric = Number(bracketMatch?.[1] || modelMatch?.[1] || fallbackMatch?.[1] || 0);
  if (!Number.isInteger(numeric) || numeric < 1 || numeric > BOOPALAN_MODEL_SPECS.length) {
    return "";
  }
  return String(numeric).padStart(3, "0");
}

function fixtureForAttachment(attachment, index) {
  const modelNumber = modelNumberFromAttachmentName(attachment?.name);
  if (modelNumber) {
    return BATCH_DRAWING_FIXTURES.find((fixture) => fixture.modelNumber === modelNumber) || BATCH_DRAWING_FIXTURES[0];
  }
  return BATCH_DRAWING_FIXTURES[index % BATCH_DRAWING_FIXTURES.length];
}

function createBatchItems(attachments) {
  const pdfAttachments = attachments.filter(isPdfAttachment);
  return pdfAttachments.map((attachment, index) => {
    const fixture = fixtureForAttachment(attachment, index);
    return {
      ...fixture,
      id: `${fixture.id}-${index}`,
      inputName: attachment.name || fixture.sourceName,
      attachmentId: attachment.id,
      status: "queued",
      phase: "Queued",
      progress: 0,
    };
  });
}

function batchPromptSummary(prompt, itemCount) {
  if (prompt) {
    return prompt;
  }
  return `Convert ${itemCount} PDF drawings into editable CAD models.`;
}

function batchLogForPhase(item, phase) {
  if (phase.phase === "Parsing PDF") {
    return `Queued ${item.inputName} and split the sheet into drawing views, title block metadata, and dimension regions.`;
  }
  if (phase.phase === "Extracting dimensions") {
    return `${item.inputName}: ${item.dimensions}.`;
  }
  if (phase.phase === "Generating CAD") {
    return `Generated ${item.resultName}: ${item.description}.`;
  }
  if (phase.phase === "Validating geometry") {
    return `Checking solid validity, drawing-derived envelope, and export readiness for ${item.resultName}.`;
  }
  return `${item.resultName} is ready with ${item.artifacts}.`;
}

function useDemoMesh(asset, enabled = true) {
  const [meshData, setMeshData] = useState(null);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!enabled) {
      setMeshData(null);
      setStatus("idle");
      setError("");
      return undefined;
    }
    let cancelled = false;
    setStatus("loading");
    setError("");
    loadRenderGlb(asset.path)
      .then((loadedMeshData) => {
        if (!cancelled) {
          setMeshData(loadedMeshData);
          setStatus("ready");
        }
      })
      .catch((loadError) => {
        if (!cancelled) {
          setStatus("error");
          setError(loadError?.message || "Failed to load CAD asset.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [asset.path, enabled]);

  return { meshData, status, error };
}

function useValidationLinkageMesh(enabled, angleDeg) {
  const [sourceMeshes, setSourceMeshes] = useState(null);
  const [status, setStatus] = useState(enabled ? "loading" : "idle");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!enabled) {
      setSourceMeshes(null);
      setStatus("idle");
      setError("");
      return undefined;
    }
    let cancelled = false;
    setStatus("loading");
    setError("");
    Promise.all(
      VALIDATE_LINKAGE_PART_SOURCES.map((source) => (
        loadRenderGlb(source.path, { coordinateSpace: GLB_COORDINATE_SPACE.CAD }).then((meshData) => [source.key, meshData])
      ))
    )
      .then((entries) => {
        if (!cancelled) {
          setSourceMeshes(Object.fromEntries(entries));
          setStatus("ready");
        }
      })
      .catch((loadError) => {
        if (!cancelled) {
          setStatus("error");
          setError(loadError?.message || "Failed to load linkage parts.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [enabled]);

  const meshData = useMemo(() => {
    if (!enabled || !sourceMeshes || status !== "ready") {
      return null;
    }
    return buildValidationLinkageMeshData(sourceMeshes, angleDeg);
  }, [angleDeg, enabled, sourceMeshes, status]);

  return { meshData, status, error };
}

function useCadRun() {
  const [mode, setMode] = useState(RUN_MODES.MODEL);
  const [prompt, setPrompt] = useState(() => modeConfig(RUN_MODES.MODEL).prompt);
  const [followUpPrompt, setFollowUpPrompt] = useState("");
  const [submittedPrompt, setSubmittedPrompt] = useState("");
  const [attachments, setAttachments] = useState(() => defaultAttachmentsForMode(RUN_MODES.MODEL));
  const [logs, setLogs] = useState([]);
  const [assetIndex, setAssetIndex] = useState(0);
  const [modelRevisionIndex, setModelRevisionIndex] = useState(0);
  const [runKind, setRunKind] = useState("single");
  const [batchItems, setBatchItems] = useState([]);
  const [batchActiveIndex, setBatchActiveIndex] = useState(0);
  const [status, setStatus] = useState("idle");
  const timersRef = useRef([]);

  useEffect(() => () => {
    timersRef.current.forEach((timer) => window.clearTimeout(timer));
  }, []);

  function clearTimers() {
    timersRef.current.forEach((timer) => window.clearTimeout(timer));
    timersRef.current = [];
  }

  function updateBatchItem(index, patch) {
    setBatchItems((current) => current.map((item, itemIndex) => (
      itemIndex === index ? { ...item, ...patch } : item
    )));
  }

  function selectBatchItem(index) {
    const nextItem = batchItems[index];
    if (!nextItem) {
      return;
    }
    setBatchActiveIndex(index);
    setAssetIndex(nextItem.assetIndex);
  }

  function startBatchRun(nextPrompt, items) {
    const submitted = batchPromptSummary(nextPrompt, items.length);
    clearTimers();
    setPrompt(nextPrompt);
    setFollowUpPrompt("");
    setSubmittedPrompt(submitted);
    setLogs([]);
    setRunKind("batch");
    setBatchItems(items);
    setBatchActiveIndex(0);
    setModelRevisionIndex(0);
    setAssetIndex(items[0]?.assetIndex ?? 0);
    setStatus("running");

    timersRef.current = items.flatMap((item, itemIndex) => {
      const baseDelay = itemIndex * 1250;
      return BATCH_ITEM_PHASES.map((phase) => window.setTimeout(() => {
        setBatchActiveIndex(itemIndex);
        setAssetIndex(item.assetIndex);
        updateBatchItem(itemIndex, {
          status: phase.status,
          phase: phase.phase,
          progress: phase.progress,
        });
        setLogs((current) => [...current, {
          text: batchLogForPhase(item, phase),
          meta: `${phase.meta} · ${item.inputName}`,
          assetIndex: item.assetIndex,
          done: phase.done,
        }]);
        if (phase.done && itemIndex === items.length - 1) {
          setStatus("done");
        }
      }, baseDelay + phase.atMs));
    });
  }

  function startRun(nextPrompt = prompt) {
    const normalizedPrompt = nextPrompt.trim();
    if (!normalizedPrompt && !attachments.length) {
      return;
    }
    const batchCandidates = createBatchItems(attachments);
    if (mode === RUN_MODES.MODEL && status !== "done" && batchCandidates.length > 1) {
      startBatchRun(normalizedPrompt, batchCandidates);
      return;
    }
    const nextRevisionIndex = mode === RUN_MODES.MODEL && status === "done"
      ? Math.min(modelRevisionIndex + 1, MODEL_REVISION_RUNS.length - 1)
      : modelRevisionIndex;
    const activeConfig = runConfigForMode(mode, nextRevisionIndex);
    clearTimers();
    setPrompt(normalizedPrompt);
    setFollowUpPrompt("");
    setSubmittedPrompt(batchPromptSummary(normalizedPrompt, 1));
    setLogs([]);
    setRunKind("single");
    setBatchItems([]);
    setBatchActiveIndex(0);
    setModelRevisionIndex(nextRevisionIndex);
    setAssetIndex(activeConfig.startAssetIndex ?? activeConfig.assetIndex ?? 0);
    setStatus("running");

    timersRef.current = activeConfig.runSteps.map((step) => window.setTimeout(() => {
      setAssetIndex(step.assetIndex);
      setLogs((current) => [...current, step]);
      if (step.done) {
        setStatus("done");
      }
    }, step.atMs));
  }

  function stopRun() {
    clearTimers();
    setStatus((current) => current === "done" ? "done" : "paused");
  }

  function switchMode(nextMode) {
    if (!MODE_CONFIG[nextMode] || nextMode === mode || status === "running") {
      return;
    }
    const nextConfig = modeConfig(nextMode);
    clearTimers();
    setMode(nextMode);
    setPrompt(nextConfig.prompt);
    setFollowUpPrompt("");
    setSubmittedPrompt("");
    setAttachments(defaultAttachmentsForMode(nextMode));
    setLogs([]);
    setRunKind("single");
    setBatchItems([]);
    setBatchActiveIndex(0);
    setAssetIndex(nextConfig.startAssetIndex ?? nextConfig.assetIndex ?? 0);
    setModelRevisionIndex(0);
    setStatus("idle");
  }

  function reset() {
    const activeConfig = modeConfig(mode);
    clearTimers();
    setSubmittedPrompt("");
    setLogs([]);
    setRunKind("single");
    setBatchItems([]);
    setBatchActiveIndex(0);
    setAssetIndex(activeConfig.startAssetIndex ?? activeConfig.assetIndex ?? 0);
    setModelRevisionIndex(0);
    setStatus("idle");
  }

  return {
    mode,
    setMode: switchMode,
    prompt,
    setPrompt,
    attachments,
    setAttachments,
    followUpPrompt,
    setFollowUpPrompt,
    submittedPrompt,
    logs,
    assetIndex,
    modelRevisionIndex,
    runConfig: runConfigForMode(mode, modelRevisionIndex),
    runKind,
    isBatch: runKind === "batch",
    batchItems,
    batchActiveIndex,
    activeBatchItem: batchItems[batchActiveIndex] || null,
    selectBatchItem,
    status,
    startRun,
    stopRun,
    reset,
  };
}

function TopBar({ status, mode, onModeChange }) {
  const activeConfig = modeConfig(mode);
  return (
    <header className="grid h-12 shrink-0 grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center border-b border-[var(--dd-border)] bg-[var(--dd-panel)] px-5">
      <div className="flex min-w-0 items-center gap-3 justify-self-start">
        <img
          src={brandLogoUrl}
          alt="The Dimension Company"
          className="h-6 w-auto shrink-0 sm:h-7"
          draggable={false}
        />
        <div className="hidden text-xs text-[var(--dd-fg-subtle)] sm:block" style={{ fontFamily: "var(--dd-font-mono)" }}>
          {status === "idle" ? activeConfig.idleStatus : activeConfig.activeStatus}
        </div>
      </div>
      <div className="justify-self-center">
        <ModeSwitcher mode={mode} onModeChange={onModeChange} disabled={status === "running"} />
      </div>
      <div className="flex items-center gap-1.5 justify-self-end">
        <span
          className="hidden h-7 items-center gap-1.5 rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-[var(--dd-panel-muted)] px-2.5 text-xs text-[var(--dd-fg-subtle)] md:inline-flex"
          style={{ fontFamily: "var(--dd-font-mono)" }}
        >
          <GitBranch className="h-3.5 w-3.5" />
          local
        </span>
        <span
          className="h-7 rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-[var(--dd-panel-muted)] px-2.5 text-xs font-medium leading-7 text-[var(--dd-fg-subtle)]"
          style={{ fontFamily: "var(--dd-font-mono)" }}
        >
          CoMeT memory
        </span>
      </div>
    </header>
  );
}

function fileKindFromName(file) {
  const extension = String(file?.name || "").split(".").pop()?.toLowerCase() || "";
  if (extension === "step" || extension === "stp") {
    return "STEP";
  }
  if (extension === "glb") {
    return "GLB";
  }
  if (extension === "stl") {
    return "STL";
  }
  if (extension === "dxf") {
    return "DXF";
  }
  if (extension === "pdf") {
    return "PDF";
  }
  if (extension === "svg") {
    return "SVG";
  }
  return file?.type?.split("/")?.[1]?.toUpperCase() || "FILE";
}

function fileCanAttach(file) {
  return file?.type?.startsWith("image/") || /\.(step|stp|glb|stl|dxf|pdf|svg)$/i.test(file?.name || "");
}

function fileToAttachment(file) {
  if (!file?.type?.startsWith("image/")) {
    return Promise.resolve({
      id: `${file.name}-${file.size}-${file.lastModified}`,
      name: file.name,
      kind: fileKindFromName(file),
    });
  }

  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      resolve({
        id: `${file.name}-${file.size}-${file.lastModified}`,
        name: file.name,
        kind: fileKindFromName(file),
        previewUrl: String(reader.result || ""),
      });
    };
    reader.onerror = () => reject(reader.error || new Error(`Failed to read ${file.name}`));
    reader.readAsDataURL(file);
  });
}

function AttachmentIcon({ kind }) {
  const normalizedKind = String(kind || "").toUpperCase();
  if (normalizedKind === "STEP" || normalizedKind === "STP" || normalizedKind === "GLB" || normalizedKind === "STL") {
    return <Box className="h-6 w-6" aria-hidden="true" />;
  }
  return <FileText className="h-6 w-6" aria-hidden="true" />;
}

function AttachmentPreview({ attachment, onRemove }) {
  const hasPreview = !!attachment.previewUrl;
  return (
    <div className="group relative h-[76px] w-[112px] overflow-hidden rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-[var(--dd-panel-muted)]">
      {hasPreview ? (
        <img
          src={attachment.previewUrl}
          alt={attachment.name}
          className="h-full w-full object-cover"
          draggable={false}
        />
      ) : (
        <div className="flex h-full w-full flex-col items-center justify-center gap-1 bg-[var(--dd-panel-muted)] text-[var(--dd-fg-subtle)]">
          <AttachmentIcon kind={attachment.kind} />
          <span className="text-[10px] font-semibold" style={{ fontFamily: "var(--dd-font-mono)" }}>
            {attachment.kind}
          </span>
        </div>
      )}
      <div className="absolute inset-x-0 bottom-0 border-t border-black/5 bg-white/92 px-2 py-1">
        <div className="truncate text-[10px] font-medium text-[var(--dd-fg)]" style={{ fontFamily: "var(--dd-font-mono)" }}>
          {attachment.name}
        </div>
      </div>
      <div className="absolute left-1.5 top-1.5 rounded-[4px] bg-white/92 px-1.5 py-0.5 text-[9px] font-semibold text-[var(--dd-fg-subtle)] shadow-[0_6px_14px_-12px_rgba(0,0,0,0.2)]">
        {attachment.kind}
      </div>
      {onRemove ? (
        <button
          type="button"
          title={`Remove ${attachment.name}`}
          className="absolute right-1.5 top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-white text-[var(--dd-fg-muted)] opacity-0 shadow-[0_8px_18px_-12px_rgba(0,0,0,0.25)] transition hover:bg-[var(--dd-fg)] hover:text-white focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgba(0,144,255,0.45)] group-hover:opacity-100"
          onClick={(event) => {
            event.preventDefault();
            event.stopPropagation();
            onRemove();
          }}
        >
          <X className="h-3 w-3" />
        </button>
      ) : null}
    </div>
  );
}

function ModeSwitcher({ mode, onModeChange, disabled = false }) {
  return (
    <div className="inline-flex rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-[var(--dd-panel-muted)] p-0.5" role="tablist" aria-label="CAD agent mode">
      {MODE_OPTIONS.map((option) => {
        const active = option === mode;
        const config = modeConfig(option);
        return (
          <button
            key={option}
            type="button"
            role="tab"
            aria-selected={active}
            disabled={disabled}
            onClick={() => onModeChange?.(option)}
            className={`h-7 rounded-[5px] px-3 text-xs font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgba(0,144,255,0.45)] disabled:cursor-not-allowed disabled:opacity-60 ${active ? "bg-white text-[var(--dd-fg)] shadow-[0_6px_14px_-13px_rgba(0,0,0,0.28)]" : "text-[var(--dd-fg-subtle)] hover:text-[var(--dd-fg)]"}`}
          >
            {config.label}
          </button>
        );
      })}
    </div>
  );
}

function Composer({
  prompt,
  setPrompt,
  attachments = [],
  setAttachments,
  status,
  onSubmit,
  onStop,
  placeholder = "",
  compact = false,
  acceptedFileTypes = "image/*",
}) {
  const disabled = status === "running";
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);
  const supportsAttachments = !compact && typeof setAttachments === "function";
  const maxTextareaHeight = compact ? 168 : 260;

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) {
      return;
    }
    textarea.style.height = "auto";
    const nextHeight = Math.min(textarea.scrollHeight, maxTextareaHeight);
    textarea.style.height = `${nextHeight}px`;
    textarea.style.overflowY = textarea.scrollHeight > maxTextareaHeight ? "auto" : "hidden";
  }, [prompt, compact, maxTextareaHeight]);

  async function addFiles(fileList) {
    if (!supportsAttachments || disabled) {
      return;
    }
    const files = Array.from(fileList || []).filter(fileCanAttach);
    if (!files.length) {
      return;
    }
    const nextAttachments = await Promise.all(files.map(fileToAttachment));
    setAttachments((current) => [...current, ...nextAttachments]);
  }

  return (
    <div
      className={`relative rounded-[var(--dd-radius-panel)] border bg-[var(--dd-control)] shadow-[0_12px_24px_-20px_rgba(0,0,0,0.16)] transition ${isDragging ? "border-[rgba(0,144,255,0.55)] ring-2 ring-[rgba(0,144,255,0.14)]" : "border-[var(--dd-border)]"}`}
      onDragEnter={(event) => {
        if (!supportsAttachments || disabled) {
          return;
        }
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragOver={(event) => {
        if (!supportsAttachments || disabled) {
          return;
        }
        event.preventDefault();
        event.dataTransfer.dropEffect = "copy";
      }}
      onDragLeave={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) {
          setIsDragging(false);
        }
      }}
      onDrop={(event) => {
        if (!supportsAttachments || disabled) {
          return;
        }
        event.preventDefault();
        setIsDragging(false);
        void addFiles(event.dataTransfer.files);
      }}
    >
      {supportsAttachments ? (
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedFileTypes}
          multiple={true}
          className="hidden"
          onChange={(event) => {
            void addFiles(event.target.files);
            event.target.value = "";
          }}
        />
      ) : null}
      {!compact && attachments.length ? (
        <div className="flex gap-2 overflow-x-auto px-3 pt-3">
          {attachments.map((attachment) => (
            <AttachmentPreview
              key={attachment.id}
              attachment={attachment}
              onRemove={() => setAttachments((current) => current.filter((item) => item.id !== attachment.id))}
            />
          ))}
        </div>
      ) : null}
      <textarea
        ref={textareaRef}
        value={prompt}
        disabled={disabled}
        onChange={(event) => setPrompt(event.target.value)}
        onKeyDown={(event) => {
          if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
            event.preventDefault();
            onSubmit();
          }
        }}
        className={`${compact ? "min-h-[3.4rem]" : "min-h-[5.8rem]"} block w-full resize-none bg-transparent px-4 py-3 text-[13px] leading-6 text-[var(--dd-fg)] outline-none placeholder:text-[var(--dd-fg-faint)] disabled:opacity-80`}
        placeholder={placeholder}
      />
      <div className="flex items-center justify-between border-t border-[var(--dd-border)] px-3 py-2">
        <div className="flex items-center gap-2 text-xs text-[var(--dd-fg-subtle)]">
          <button
            className="flex h-7 w-7 items-center justify-center rounded-[var(--dd-radius-control)] text-[var(--dd-fg-subtle)] transition hover:bg-[var(--dd-panel-muted)] hover:text-[var(--dd-fg)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgba(0,144,255,0.45)]"
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={!supportsAttachments || disabled}
          >
            <Plus className="h-4 w-4" />
          </button>
          <button className="inline-flex h-7 items-center gap-1 rounded-[var(--dd-radius-control)] px-1.5 transition hover:bg-[var(--dd-panel-muted)] hover:text-[var(--dd-fg)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgba(0,144,255,0.45)]" type="button">
            <Circle className="h-3.5 w-3.5" />
            Local execution
            <ChevronDown className="h-3.5 w-3.5" />
          </button>
        </div>
        <div className="flex items-center gap-3 text-xs font-medium text-[var(--dd-fg-subtle)]">
          <span>GPT 5.5</span>
          <span>Extra High</span>
          <button
            className="flex h-8 w-8 items-center justify-center rounded-[var(--dd-radius-control)] bg-[var(--dd-fg)] text-white transition hover:bg-[var(--dd-accent-deep)] disabled:cursor-not-allowed disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgba(0,144,255,0.45)]"
            type="button"
            onClick={status === "running" ? onStop : onSubmit}
            disabled={!prompt.trim() && !attachments.length && status !== "running"}
            title={status === "running" ? "Stop run" : "Run CAD agent"}
          >
            {status === "running" ? <Square className="h-3.5 w-3.5 fill-current" /> : <Send className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </div>
  );
}

function IdlePane({ run }) {
  const activeConfig = modeConfig(run.mode);
  if (run.mode === RUN_MODES.VALIDATE) {
    return <ValidateSetupPane run={run} />;
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col items-center justify-center px-10 pb-12">
      <h1
        className="mb-6 max-w-[34rem] text-center text-[clamp(1.75rem,1.9vw,2.25rem)] font-semibold leading-tight tracking-normal text-[var(--dd-fg)]"
        style={{ fontFamily: "var(--dd-font-display)" }}
      >
        {activeConfig.heading}
      </h1>
      <div className="w-full max-w-[42rem]">
        <Composer
          prompt={run.prompt}
          setPrompt={run.setPrompt}
          attachments={run.attachments}
          setAttachments={run.setAttachments}
          status={run.status}
          onSubmit={() => run.startRun()}
          onStop={run.stopRun}
          acceptedFileTypes={activeConfig.acceptedFileTypes}
          placeholder={activeConfig.placeholder}
        />
      </div>
    </div>
  );
}

function ValidateSetupPane({ run }) {
  const activeConfig = modeConfig(RUN_MODES.VALIDATE);
  const fileInputRef = useRef(null);
  const disabled = run.status === "running";

  async function addFiles(fileList) {
    if (disabled) {
      return;
    }
    const files = Array.from(fileList || []).filter(fileCanAttach);
    if (!files.length) {
      return;
    }
    const nextAttachments = await Promise.all(files.map(fileToAttachment));
    run.setAttachments((current) => [...current, ...nextAttachments]);
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col items-center justify-center bg-[var(--dd-bg)] px-10 pb-12">
      <h1
        className="mb-6 max-w-[34rem] text-center text-[clamp(1.75rem,1.9vw,2.25rem)] font-semibold leading-tight tracking-normal text-[var(--dd-fg)]"
        style={{ fontFamily: "var(--dd-font-display)" }}
      >
        {activeConfig.heading}
      </h1>
      <div className="w-full max-w-[42rem] rounded-[var(--dd-radius-panel)] border border-[var(--dd-border)] bg-[var(--dd-control)] shadow-[0_12px_24px_-20px_rgba(0,0,0,0.16)]">
        <div className="px-3 pt-3">
          <input
            ref={fileInputRef}
            type="file"
            accept={activeConfig.acceptedFileTypes}
            multiple={true}
            className="hidden"
            onChange={(event) => {
              void addFiles(event.target.files);
              event.target.value = "";
            }}
          />
          <div
            className="rounded-[var(--dd-radius-control)] border border-dashed border-[var(--dd-border-strong)] bg-[var(--dd-panel-muted)] px-3 py-3"
            onDragOver={(event) => {
              if (disabled) {
                return;
              }
              event.preventDefault();
              event.dataTransfer.dropEffect = "copy";
            }}
            onDrop={(event) => {
              if (disabled) {
                return;
              }
              event.preventDefault();
              void addFiles(event.dataTransfer.files);
            }}
          >
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <div className="text-[13px] font-semibold text-[var(--dd-fg)]">CAD package</div>
                <div className="mt-1 text-xs text-[var(--dd-fg-subtle)]">STEP, STP, GLB, DXF, PDF</div>
              </div>
              <button
                type="button"
                className="h-8 shrink-0 rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-white px-3 text-xs font-medium text-[var(--dd-fg-muted)] transition hover:bg-[var(--dd-control-hover)] hover:text-[var(--dd-fg)] disabled:cursor-not-allowed disabled:opacity-60"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled}
              >
                Add files
              </button>
            </div>
            {run.attachments.length ? (
              <div className="mt-3 flex gap-2 overflow-x-auto">
                {run.attachments.map((attachment) => (
                  <AttachmentPreview
                    key={attachment.id}
                    attachment={attachment}
                    onRemove={() => run.setAttachments((current) => current.filter((item) => item.id !== attachment.id))}
                  />
                ))}
              </div>
            ) : null}
          </div>
        </div>
        <div className="grid gap-2 px-3 py-3 sm:grid-cols-3">
          <div className="rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-white px-3 py-2">
            <div className="text-[10px] uppercase tracking-[0.08em] text-[var(--dd-fg-faint)]" style={{ fontFamily: "var(--dd-font-mono)" }}>Standard</div>
            <div className="mt-1 text-xs font-semibold text-[var(--dd-fg)]">ASME Y14.5</div>
          </div>
          <div className="rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-white px-3 py-2">
            <div className="text-[10px] uppercase tracking-[0.08em] text-[var(--dd-fg-faint)]" style={{ fontFamily: "var(--dd-font-mono)" }}>Process</div>
            <div className="mt-1 text-xs font-semibold text-[var(--dd-fg)]">CNC Milling</div>
          </div>
          <div className="rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-white px-3 py-2">
            <div className="text-[10px] uppercase tracking-[0.08em] text-[var(--dd-fg-faint)]" style={{ fontFamily: "var(--dd-font-mono)" }}>Output</div>
            <div className="mt-1 text-xs font-semibold text-[var(--dd-fg)]">Report + DXF</div>
          </div>
        </div>
        <div className="flex items-center justify-between border-t border-[var(--dd-border)] px-3 py-2">
          <div className="flex items-center gap-2 text-xs text-[var(--dd-fg-subtle)]">
            <Circle className="h-3.5 w-3.5" />
            Validate locally
          </div>
          <button
            type="button"
            className="flex h-8 items-center gap-2 rounded-[var(--dd-radius-control)] bg-[var(--dd-fg)] px-3 text-xs font-semibold text-white transition hover:bg-[var(--dd-accent-deep)] disabled:cursor-not-allowed disabled:opacity-60"
            onClick={() => run.startRun(activeConfig.prompt)}
            disabled={disabled}
            title="Start validation"
          >
            <ShieldCheck className="h-4 w-4" />
            Start validation
          </button>
        </div>
      </div>
    </div>
  );
}

function RunPane({ run }) {
  const activeConfig = run.runConfig || modeConfig(run.mode);
  const elapsedLabel = run.status === "done" ? activeConfig.elapsedDone : run.status === "paused" ? "Paused" : activeConfig.elapsedRunning;
  const logScrollerRef = useRef(null);

  useEffect(() => {
    const scroller = logScrollerRef.current;
    if (scroller) {
      scroller.scrollTop = scroller.scrollHeight;
    }
  }, [run.logs.length, run.status]);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="border-b border-[var(--dd-border)] px-6 py-4">
        <div className="ml-auto max-w-[36rem] rounded-[var(--dd-radius-control)] border border-[rgba(0,144,255,0.24)] bg-[rgba(0,144,255,0.08)] px-3 py-2 text-[13px] font-medium leading-6 text-[var(--dd-fg)]">
          {run.submittedPrompt}
        </div>
      </div>
      <div ref={logScrollerRef} className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
        <div className="mb-4 flex items-center gap-2 text-[13px] font-medium text-[var(--dd-fg-subtle)]">
          {run.status === "running" ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          {elapsedLabel}
        </div>
        <div className="space-y-5 border-t border-[var(--dd-border)] pt-4">
          {run.logs.map((log, index) => (
            <div key={`${log.text}-${index}`}>
              <p className="max-w-[40rem] text-[13px] leading-6 text-[var(--dd-fg-muted)]">{log.text}</p>
              <div className="mt-3 text-[11px] uppercase tracking-[0.08em] text-[var(--dd-fg-faint)]" style={{ fontFamily: "var(--dd-font-mono)" }}>{log.meta}</div>
            </div>
          ))}
          {run.status === "done" ? (
            <div className="inline-flex items-center gap-2 rounded-[var(--dd-radius-control)] border border-[rgba(22,163,74,0.24)] bg-[rgba(22,163,74,0.08)] px-3 py-2 text-[13px] font-medium text-[var(--dd-success)]">
              <Check className="h-4 w-4" />
              {activeConfig.readyMessage}
            </div>
          ) : null}
        </div>
      </div>
      <div className="px-6 pb-4">
        <Composer
          prompt={run.followUpPrompt}
          setPrompt={run.setFollowUpPrompt}
          status={run.status}
          onSubmit={() => run.startRun(run.followUpPrompt)}
          onStop={run.stopRun}
          placeholder={activeConfig.followUpPlaceholder}
          compact={true}
        />
      </div>
    </div>
  );
}

function BatchRunPane({ run }) {
  const logScrollerRef = useRef(null);
  const completedCount = run.batchItems.filter((item) => item.status === "done").length;
  const activeItem = run.activeBatchItem || run.batchItems[0];
  const denseQueue = run.batchItems.length >= 8;
  const elapsedLabel = run.status === "done"
    ? `Batch completed · ${completedCount}/${run.batchItems.length} drawings`
    : `Batch running · ${completedCount}/${run.batchItems.length} drawings ready`;

  useEffect(() => {
    const scroller = logScrollerRef.current;
    if (scroller) {
      scroller.scrollTop = scroller.scrollHeight;
    }
  }, [run.logs.length, run.status]);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="border-b border-[var(--dd-border)] px-6 py-4">
        <div className="ml-auto max-w-[36rem] rounded-[var(--dd-radius-control)] border border-[rgba(0,144,255,0.24)] bg-[rgba(0,144,255,0.08)] px-3 py-2 text-[13px] font-medium leading-6 text-[var(--dd-fg)]">
          {run.submittedPrompt}
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-[13px] font-medium text-[var(--dd-fg-subtle)]">
            {run.status === "running" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4 text-[var(--dd-success)]" />}
            {elapsedLabel}
          </div>
          <div className="rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-white px-2.5 py-1 text-[11px] text-[var(--dd-fg-subtle)]" style={{ fontFamily: "var(--dd-font-mono)" }}>
            {run.batchItems.length} PDF queue
          </div>
        </div>

        <div className={`grid gap-2 ${denseQueue ? "xl:grid-cols-2" : ""}`}>
          {run.batchItems.map((item, index) => (
            <button
              key={item.id}
              type="button"
              onClick={() => run.selectBatchItem(index)}
              className={`grid min-w-0 ${denseQueue ? "grid-cols-[auto_minmax(0,1fr)] gap-2 px-2.5 py-2" : "grid-cols-[auto_minmax(0,1fr)_auto] gap-3 px-3 py-3"} rounded-[var(--dd-radius-panel)] border text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgba(0,144,255,0.45)] ${
                index === run.batchActiveIndex
                  ? "border-[rgba(0,144,255,0.42)] bg-[rgba(0,144,255,0.06)]"
                  : "border-[var(--dd-border)] bg-white hover:border-[var(--dd-border-strong)]"
              }`}
            >
              <div className={`flex ${denseQueue ? "h-8 w-8" : "h-9 w-9"} items-center justify-center rounded-[var(--dd-radius-control)] border ${
                item.status === "done"
                  ? "border-[rgba(22,163,74,0.28)] bg-[rgba(22,163,74,0.08)] text-[var(--dd-success)]"
                  : "border-[var(--dd-border)] bg-[var(--dd-panel-muted)] text-[var(--dd-fg-subtle)]"
              }`}>
                {item.status === "done" ? <Check className="h-4 w-4" /> : <FileText className="h-4 w-4" />}
              </div>
              <div className="min-w-0">
                <div className="flex min-w-0 items-center gap-2">
                  <span className="truncate text-[13px] font-semibold text-[var(--dd-fg)]">{item.inputName}</span>
                  <span className="shrink-0 rounded-[4px] bg-[var(--dd-panel-muted)] px-1.5 py-0.5 text-[9px] font-semibold text-[var(--dd-fg-subtle)]" style={{ fontFamily: "var(--dd-font-mono)" }}>
                    PDF
                  </span>
                </div>
                <div className="mt-1 truncate text-[11px] text-[var(--dd-fg-subtle)]">{item.resultName}</div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-[var(--dd-panel-muted)]">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${item.status === "done" ? "bg-[var(--dd-success)]" : "bg-[var(--dd-accent)]"}`}
                    style={{ width: `${item.progress}%` }}
                  />
                </div>
                {denseQueue ? (
                  <div className="mt-1 flex items-center justify-between gap-2 text-[10px]" style={{ fontFamily: "var(--dd-font-mono)" }}>
                    <span className={`truncate font-semibold ${item.status === "done" ? "text-[var(--dd-success)]" : item.status === "queued" ? "text-[var(--dd-fg-faint)]" : "text-[var(--dd-accent-deep)]"}`}>
                      {item.phase}
                    </span>
                    <span className="shrink-0 text-[var(--dd-fg-faint)]">{item.progress}%</span>
                  </div>
                ) : null}
              </div>
              {denseQueue ? null : (
              <div className="w-[7.5rem] text-right">
                <div className={`truncate text-[11px] font-semibold ${item.status === "done" ? "text-[var(--dd-success)]" : item.status === "queued" ? "text-[var(--dd-fg-faint)]" : "text-[var(--dd-accent-deep)]"}`}>
                  {item.phase}
                </div>
                <div className="mt-1 text-[10px] text-[var(--dd-fg-faint)]" style={{ fontFamily: "var(--dd-font-mono)" }}>
                  {item.progress}%
                </div>
              </div>
              )}
            </button>
          ))}
        </div>

        {activeItem ? (
          <div className="mt-4 rounded-[var(--dd-radius-panel)] border border-[var(--dd-border)] bg-white px-4 py-3">
            <div className="mb-2 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <div className="truncate text-[13px] font-semibold text-[var(--dd-fg)]">{activeItem.description}</div>
                <div className="mt-1 truncate text-[11px] text-[var(--dd-fg-subtle)]">{activeItem.dimensions}</div>
              </div>
              <div className="shrink-0 rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-[var(--dd-panel-muted)] px-2 py-1 text-[10px] text-[var(--dd-fg-subtle)]" style={{ fontFamily: "var(--dd-font-mono)" }}>
                {activeItem.status === "done" ? "ready" : "active"}
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {activeItem.artifacts.split(", ").slice(0, 3).map((artifact) => (
                <div key={artifact} className={`rounded-[var(--dd-radius-control)] border px-2 py-1.5 text-[10px] ${
                  activeItem.progress >= 72
                    ? "border-[rgba(22,163,74,0.22)] bg-[rgba(22,163,74,0.06)] text-[var(--dd-success)]"
                    : "border-[var(--dd-border)] bg-[var(--dd-panel-muted)] text-[var(--dd-fg-subtle)]"
                }`}>
                  {artifact}
                </div>
              ))}
            </div>
          </div>
        ) : null}

        <div ref={logScrollerRef} className={`mt-4 ${denseQueue ? "max-h-24" : "max-h-[13rem]"} overflow-y-auto border-t border-[var(--dd-border)] pt-4`}>
          <div className="space-y-4">
            {run.logs.map((log, index) => (
              <div key={`${log.meta}-${index}`}>
                <p className="text-[13px] leading-6 text-[var(--dd-fg-muted)]">{log.text}</p>
                <div className="mt-2 text-[10px] uppercase tracking-[0.08em] text-[var(--dd-fg-faint)]" style={{ fontFamily: "var(--dd-font-mono)" }}>{log.meta}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
      {run.status === "done" ? (
        <div className="border-t border-[var(--dd-border)] px-6 py-4">
          <div className="inline-flex items-center gap-2 rounded-[var(--dd-radius-control)] border border-[rgba(22,163,74,0.24)] bg-[rgba(22,163,74,0.08)] px-3 py-2 text-[13px] font-medium text-[var(--dd-success)]">
            <Check className="h-4 w-4" />
            {completedCount} CAD models exported with linked drawing inputs
          </div>
        </div>
      ) : null}
    </div>
  );
}

function StatusBar({ mode }) {
  const activeConfig = modeConfig(mode);
  return (
    <div className="flex h-8 shrink-0 items-center gap-5 border-t border-[var(--dd-border)] bg-[var(--dd-panel)] px-5 text-[11px] text-[var(--dd-fg-faint)]" style={{ fontFamily: "var(--dd-font-mono)" }}>
      <span className="inline-flex items-center gap-1.5"><Globe className="h-3.5 w-3.5" /> {activeConfig.label.toLowerCase()}</span>
      <span className="inline-flex items-center gap-1.5"><Circle className="h-3 w-3" /> {activeConfig.statusLabel}</span>
      <span className="inline-flex items-center gap-1.5"><GitBranch className="h-3.5 w-3.5" /> main</span>
    </div>
  );
}

function useDemoLookSettings({ validate = false } = {}) {
  return useMemo(() => ({
    ...DEFAULT_LOOK_SETTINGS,
    materials: {
      ...DEFAULT_LOOK_SETTINGS.materials,
      defaultColor: validate ? "#aeb7c2" : "#d9dee3",
      tintStrength: validate ? 0.24 : 0.78,
      saturation: validate ? 0.42 : 0.22,
      contrast: validate ? 1.06 : 1.02,
      brightness: validate ? 0.94 : 1.04,
      roughness: validate ? 0.56 : 0.42,
      metalness: validate ? 0.02 : 0.28,
      clearcoat: validate ? 0.08 : 0.2,
      clearcoatRoughness: validate ? 0.62 : 0.48,
      opacity: 1,
      envMapIntensity: validate ? 0.42 : 0.9,
    },
    edges: {
      ...DEFAULT_LOOK_SETTINGS.edges,
      enabled: false,
    },
    background: {
      ...DEFAULT_LOOK_SETTINGS.background,
      type: "radial",
      radialInner: "#ffffff",
      radialOuter: validate ? "#f4f4f4" : "#e8ecef",
      solidColor: "#f5f5f5",
    },
    floor: {
      ...DEFAULT_LOOK_SETTINGS.floor,
      mode: LOOK_FLOOR_MODES.STAGE,
      color: "#e5e5e5",
      reflectivity: validate ? 0.04 : 0.08,
      shadowOpacity: validate ? 0.22 : 0.24,
      horizonBlend: 0.08,
    },
    lighting: {
      ...DEFAULT_LOOK_SETTINGS.lighting,
      toneMappingExposure: validate ? 1 : 1.08,
      ambient: {
        ...DEFAULT_LOOK_SETTINGS.lighting.ambient,
        enabled: true,
        intensity: validate ? 0.55 : 1.35,
      },
      directional: {
        ...DEFAULT_LOOK_SETTINGS.lighting.directional,
        enabled: true,
        intensity: validate ? 1.2 : 4.2,
        color: "#ffffff",
        position: { x: -80, y: 120, z: 110 },
      },
      hemisphere: {
        ...DEFAULT_LOOK_SETTINGS.lighting.hemisphere,
        enabled: true,
        intensity: validate ? 0.95 : 2.1,
        skyColor: "#ffffff",
        groundColor: "#d4d4d4",
      },
    },
  }), [validate]);
}

function BrowserPane({ asset, showModel }) {
  return (
    <div className="flex min-h-0 flex-col border-l border-[var(--dd-border)] bg-[var(--dd-panel)]">
      <div className="flex h-10 shrink-0 items-center gap-2 border-b border-[var(--dd-border)] px-4 text-xs text-[var(--dd-fg-subtle)]">
        <span className="rounded-[var(--dd-radius-control)] bg-[var(--dd-panel-muted)] px-2 py-1">Summary</span>
        <span className="rounded-[var(--dd-radius-control)] bg-[var(--dd-panel-muted)] px-2 py-1">Review</span>
        <span className="rounded-[var(--dd-radius-control)] border border-[rgba(0,144,255,0.24)] bg-[rgba(0,144,255,0.08)] px-2 py-1 text-[var(--dd-fg)]">
          <Globe className="mr-1 inline h-3.5 w-3.5" />
          Viewport
        </span>
        <Plus className="h-4 w-4" />
      </div>
      <div className="flex h-8 shrink-0 items-center justify-between border-b border-[var(--dd-border)] px-4 text-xs text-[var(--dd-fg-faint)]">
        <div className="flex items-center gap-3">
          <RefreshCw className="h-4 w-4" />
        </div>
        <div className="max-w-[74%] truncate text-[var(--dd-fg-subtle)]" style={{ fontFamily: "var(--dd-font-mono)" }}>
          {asset.url}
        </div>
        <div className="flex items-center gap-3">
          <ExternalLink className="h-4 w-4" />
          <PanelRight className="h-4 w-4" />
        </div>
      </div>
      <RenderPane asset={asset} showModel={showModel} />
    </div>
  );
}

function RenderPane({ asset, showModel = false }) {
  const viewerRef = useRef(null);
  const perspectiveRef = useRef(null);
  const [viewerAlert, setViewerAlert] = useState(null);
  const { meshData, status, error } = useDemoMesh(asset);
  const shouldShowModel = showModel && status === "ready";
  const viewerLoading = status !== "error" && !shouldShowModel;
  const lookSettings = useDemoLookSettings();

  return (
    <div className="relative min-h-0 flex-1 overflow-hidden bg-[var(--dd-render-bg)]">
      <CadViewer
        ref={viewerRef}
        meshData={shouldShowModel ? meshData : null}
        modelKey={asset.id}
        perspectiveRef={perspectiveRef}
        showEdges={false}
        recomputeNormals={false}
        lookSettings={lookSettings}
        floorModeOverride={LOOK_FLOOR_MODES.STAGE}
        floorOffset={asset.floorOffset ?? 0}
        cameraFitScale={asset.cameraFitScale ?? 1}
        previewMode={true}
        showViewPlane={false}
        isLoading={viewerLoading}
        pickMode={VIEWER_PICK_MODE.NONE}
        pickableParts={EMPTY_VIEWER_ITEMS}
        hiddenPartIds={EMPTY_VIEWER_ITEMS}
        selectedPartIds={EMPTY_VIEWER_ITEMS}
        selectedReferenceIds={EMPTY_VIEWER_ITEMS}
        pickableFaces={EMPTY_VIEWER_ITEMS}
        pickableEdges={EMPTY_VIEWER_ITEMS}
        pickableVertices={EMPTY_VIEWER_ITEMS}
        drawingStrokes={EMPTY_VIEWER_ITEMS}
        onViewerAlertChange={setViewerAlert}
      />
      {viewerLoading ? (
        <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center">
          <div
            className="flex h-12 w-12 animate-spin items-center justify-center rounded-full border border-[var(--dd-border)] bg-white/88 text-[var(--dd-fg-subtle)] shadow-[0_14px_30px_-22px_rgba(0,0,0,0.24)] backdrop-blur"
            role="status"
            aria-label="Loading CAD model"
          >
            <Loader2 className="h-7 w-7" aria-hidden="true" />
          </div>
        </div>
      ) : null}
      <div className="pointer-events-none absolute bottom-4 left-4 rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-white/88 px-3 py-2 text-xs text-[var(--dd-fg-subtle)] shadow-[0_8px_20px_-18px_rgba(0,0,0,0.18)] backdrop-blur" style={{ fontFamily: "var(--dd-font-mono)" }}>
        {asset.label}
      </div>
      {status === "error" || viewerAlert ? (
        <div className="absolute inset-x-5 bottom-5 rounded-[var(--dd-radius-control)] border border-[rgba(220,38,38,0.42)] bg-white p-3 text-sm text-[var(--dd-danger)] shadow-[0_12px_24px_-18px_rgba(0,0,0,0.18)]">
          {error || viewerAlert?.message || "CAD viewer error"}
        </div>
      ) : null}
    </div>
  );
}

function ValidateBrowserPane({ asset, showWorkspace, fullWidth = false }) {
  const [linkageAngle, setLinkageAngle] = useState(VALIDATE_LINKAGE_DEFAULT_ANGLE);
  const [modelReady, setModelReady] = useState(false);

  useEffect(() => {
    if (!showWorkspace) {
      setModelReady(false);
    }
  }, [asset.id, showWorkspace]);

  const railReady = showWorkspace && modelReady;
  return (
    <div className={`flex min-h-0 flex-1 flex-col bg-[var(--dd-panel)] ${fullWidth ? "" : "border-l border-[var(--dd-border)]"}`}>
      <div className="flex h-10 shrink-0 items-center justify-between border-b border-[var(--dd-border)] px-4 text-xs text-[var(--dd-fg-subtle)]">
        <div className="inline-flex rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-[var(--dd-panel-muted)] p-0.5">
          <span className="h-6 rounded-[5px] px-2.5 leading-6">3D</span>
          <span className="h-6 rounded-[5px] bg-[var(--dd-fg)] px-2.5 font-medium leading-6 text-white">Split</span>
          <span className="h-6 rounded-[5px] px-2.5 leading-6">2D</span>
        </div>
        <div className="flex items-center gap-3 text-[var(--dd-fg-faint)]">
          <RefreshCw className="h-4 w-4" />
          <ExternalLink className="h-4 w-4" />
          <PanelRight className="h-4 w-4" />
        </div>
      </div>
      <div className="flex h-8 shrink-0 items-center justify-between border-b border-[var(--dd-border)] px-4 text-xs text-[var(--dd-fg-faint)]">
        <div className="inline-flex items-center gap-1.5 text-[var(--dd-fg-subtle)]">
          <ShieldCheck className="h-3.5 w-3.5" />
          GD&T validation
        </div>
        <div className="max-w-[64%] truncate text-[var(--dd-fg-subtle)]" style={{ fontFamily: "var(--dd-font-mono)" }}>
          {asset.url}
        </div>
      </div>
      <div className="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)_13.5rem] bg-white xl:grid-cols-[minmax(0,1fr)_15rem]">
        <div className="grid min-h-0 grid-rows-2 xl:grid-cols-2 xl:grid-rows-1">
          <ValidationModelPanel asset={asset} ready={showWorkspace} linkageAngle={linkageAngle} onReadyChange={setModelReady} />
          <ValidationDrawingPanel ready={showWorkspace} />
        </div>
        <ValidationRail ready={railReady} linkageAngle={linkageAngle} onLinkageAngleChange={setLinkageAngle} />
      </div>
    </div>
  );
}

function ValidationModelPanel({ asset, ready, linkageAngle, onReadyChange }) {
  const viewerRef = useRef(null);
  const perspectiveRef = useRef(null);
  const [viewerAlert, setViewerAlert] = useState(null);
  const isArticulatedLinkage = asset.id === VALIDATE_LINKAGE_ASSET_ID;
  const fallbackMesh = useDemoMesh(asset, !isArticulatedLinkage);
  const linkageMesh = useValidationLinkageMesh(isArticulatedLinkage, linkageAngle);
  const { meshData, status, error } = isArticulatedLinkage ? linkageMesh : fallbackMesh;
  const shouldShowModel = ready && status === "ready";
  const viewerLoading = status !== "error" && !shouldShowModel;
  const lookSettings = useDemoLookSettings({ validate: true });

  useEffect(() => {
    onReadyChange?.(shouldShowModel);
  }, [onReadyChange, shouldShowModel]);

  return (
    <section className="relative min-h-0 overflow-hidden border-b border-[var(--dd-border)] bg-white xl:border-b-0 xl:border-r">
      <div className="absolute left-3 top-3 z-10 text-[10px] uppercase tracking-[0.08em] text-[var(--dd-fg-faint)]" style={{ fontFamily: "var(--dd-font-mono)" }}>
        3D viewer
      </div>
      <CadViewer
        ref={viewerRef}
        meshData={shouldShowModel ? meshData : null}
        modelKey={`${asset.id}-validate`}
        perspectiveRef={perspectiveRef}
        showEdges={false}
        recomputeNormals={false}
        lookSettings={lookSettings}
        floorModeOverride={LOOK_FLOOR_MODES.STAGE}
        previewMode={true}
        showViewPlane={false}
        isLoading={viewerLoading}
        pickMode={VIEWER_PICK_MODE.NONE}
        pickableParts={EMPTY_VIEWER_ITEMS}
        hiddenPartIds={EMPTY_VIEWER_ITEMS}
        selectedPartIds={EMPTY_VIEWER_ITEMS}
        selectedReferenceIds={EMPTY_VIEWER_ITEMS}
        pickableFaces={EMPTY_VIEWER_ITEMS}
        pickableEdges={EMPTY_VIEWER_ITEMS}
        pickableVertices={EMPTY_VIEWER_ITEMS}
        drawingStrokes={EMPTY_VIEWER_ITEMS}
        onViewerAlertChange={setViewerAlert}
      />
      {viewerLoading ? (
        <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center">
          <div
            className="flex h-11 w-11 animate-spin items-center justify-center rounded-full border border-[var(--dd-border)] bg-white/90 text-[var(--dd-fg-subtle)] shadow-[0_14px_30px_-22px_rgba(0,0,0,0.24)] backdrop-blur"
            role="status"
            aria-label="Loading validation model"
          >
            <Loader2 className="h-6 w-6" aria-hidden="true" />
          </div>
        </div>
      ) : null}
      {status === "error" || viewerAlert ? (
        <div className="absolute inset-x-4 bottom-4 rounded-[var(--dd-radius-control)] border border-[rgba(220,38,38,0.42)] bg-white p-3 text-xs text-[var(--dd-danger)] shadow-[0_12px_24px_-18px_rgba(0,0,0,0.18)]">
          {error || viewerAlert?.message || "CAD viewer error"}
        </div>
      ) : null}
    </section>
  );
}

function ValidationDrawingPanel({ ready }) {
  return (
    <section className="relative min-h-0 overflow-hidden bg-white">
      <div className="absolute left-3 top-3 z-10 text-[10px] uppercase tracking-[0.08em] text-[var(--dd-fg-faint)]" style={{ fontFamily: "var(--dd-font-mono)" }}>
        2D drawing
      </div>
      {ready ? (
        <div className="absolute inset-0 flex items-center justify-center p-6">
          <img
            src={VALIDATE_DRAWING_IMAGE}
            alt="Model 009 drawing"
            className="max-h-full max-w-full object-contain"
            draggable={false}
          />
        </div>
      ) : null}
      {!ready ? (
        <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center">
          <div className="flex items-center gap-2 rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-white/90 px-3 py-2 text-xs text-[var(--dd-fg-subtle)] shadow-[0_14px_30px_-24px_rgba(0,0,0,0.28)]">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Preparing drawing
          </div>
        </div>
      ) : null}
    </section>
  );
}

function ValidationRail({ ready, linkageAngle, onLinkageAngleChange }) {
  const handleLinkageAngleInput = (event) => {
    onLinkageAngleChange(Number(event.currentTarget.value));
  };
  if (!ready) {
    return (
      <aside className="min-h-0 border-l border-[var(--dd-border)] bg-[var(--dd-panel)]" aria-label="Validation panel" />
    );
  }
  const activeStepIndex = 4;
  return (
    <aside className="flex min-h-0 flex-col border-l border-[var(--dd-border)] bg-[var(--dd-panel)]">
      <div className="border-b border-[var(--dd-border)] px-3 py-3">
        <div className="flex items-center gap-2 text-[13px] font-semibold text-[var(--dd-fg)]">
          <ShieldCheck className="h-4 w-4" />
          Validate
        </div>
        <div className="mt-2 grid grid-cols-2 gap-1.5 text-[10px] text-[var(--dd-fg-subtle)]" style={{ fontFamily: "var(--dd-font-mono)" }}>
          <span className="rounded-[4px] bg-[var(--dd-panel-muted)] px-1.5 py-1">ASME Y14.5</span>
          <span className="rounded-[4px] bg-[var(--dd-panel-muted)] px-1.5 py-1">CNC Milling</span>
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
        <div className="mb-3">
          <div className="mb-2 flex items-center justify-between text-[11px] font-semibold text-[var(--dd-fg-muted)]">
            <span className="inline-flex items-center gap-1.5"><GitBranch className="h-3.5 w-3.5" /> Linkage</span>
            <span className="text-[var(--dd-fg-faint)]" style={{ fontFamily: "var(--dd-font-mono)" }}>{Math.round(linkageAngle)}°</span>
          </div>
          <input
            type="range"
            min={VALIDATE_LINKAGE_MIN_ANGLE}
            max={VALIDATE_LINKAGE_MAX_ANGLE}
            step="1"
            value={linkageAngle}
            disabled={!ready}
            onInput={handleLinkageAngleInput}
            onChange={handleLinkageAngleInput}
            className="h-6 w-full accent-[var(--dd-fg)] disabled:cursor-not-allowed disabled:opacity-45"
            aria-label="Drive linkage angle"
          />
        </div>

        <div className="mb-3">
          <div className="mb-2 flex items-center justify-between text-[11px] font-semibold text-[var(--dd-fg-muted)]">
            <span className="inline-flex items-center gap-1.5"><MousePointer2 className="h-3.5 w-3.5" /> Features</span>
            <span className="text-[var(--dd-fg-faint)]">{ready ? "42" : "..."}</span>
          </div>
          <div className="space-y-1.5">
            {VALIDATION_FEATURES.map((feature) => (
              <div key={feature.id} className={`grid grid-cols-[1fr_auto] gap-2 rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-white px-2 py-1.5 transition ${ready ? "opacity-100" : "opacity-45"}`}>
                <div className="min-w-0">
                  <div className="flex min-w-0 items-center gap-1.5">
                    <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: feature.color }} />
                    <span className="truncate text-[11px] font-semibold text-[var(--dd-fg)]">{feature.label}</span>
                  </div>
                  <div className="mt-0.5 text-[9px] uppercase tracking-[0.06em] text-[var(--dd-fg-faint)]" style={{ fontFamily: "var(--dd-font-mono)" }}>
                    {feature.kind}
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button type="button" className="flex h-6 w-6 items-center justify-center rounded-[4px] border border-[rgba(22,163,74,0.35)] bg-[rgba(22,163,74,0.08)] text-[var(--dd-success)]" disabled={!ready} title="Confirm feature">
                    <Check className="h-3.5 w-3.5" />
                  </button>
                  <button type="button" className="flex h-6 w-6 items-center justify-center rounded-[4px] border border-[rgba(220,38,38,0.28)] bg-[rgba(220,38,38,0.06)] text-[var(--dd-danger)]" disabled={!ready} title="Reject feature">
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mb-3">
          <div className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold text-[var(--dd-fg-muted)]">
            <Target className="h-3.5 w-3.5" />
            Datums
          </div>
          <div className="space-y-1.5">
            {VALIDATION_DATUMS.map((datum) => (
              <div key={datum.id} className={`flex items-center gap-2 rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-white px-2 py-1.5 transition ${ready ? "opacity-100" : "opacity-45"}`}>
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-[4px] text-[11px] font-semibold text-white" style={{ backgroundColor: datum.color }}>
                  {datum.id}
                </span>
                <span className="min-w-0 truncate text-[11px] text-[var(--dd-fg-muted)]">{datum.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold text-[var(--dd-fg-muted)]">
            <Ruler className="h-3.5 w-3.5" />
            Review
          </div>
          <div className={`rounded-[var(--dd-radius-control)] border border-[rgba(0,102,204,0.18)] bg-[rgba(0,102,204,0.05)] px-2 py-2 text-[11px] leading-5 text-[var(--dd-fg-muted)] transition ${ready ? "opacity-100" : "opacity-45"}`}>
            24 GD&T callouts, 3 datums, 1 evaluator report
          </div>
        </div>
      </div>
      <div className="border-t border-[var(--dd-border)] px-3 py-3">
        <button
          type="button"
          className="mb-3 flex h-8 w-full items-center justify-center gap-2 rounded-[var(--dd-radius-control)] bg-[var(--dd-fg)] text-xs font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-55"
          disabled={!ready}
        >
          <Download className="h-3.5 w-3.5" />
          Export DXF
        </button>
        <div className="grid grid-cols-5 gap-1">
          {VALIDATION_STEPS.map((step, index) => {
            const active = index <= activeStepIndex;
            return (
              <div key={step} className="min-w-0 text-center">
                <div className={`mx-auto mb-1 flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-semibold ${active ? "bg-[var(--dd-fg)] text-white" : "bg-[var(--dd-panel-muted)] text-[var(--dd-fg-faint)]"}`}>
                  {index + 1}
                </div>
                <div className="truncate text-[8px] text-[var(--dd-fg-faint)]">{step}</div>
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
}

export default function DimensionLaunchDemo() {
  const run = useCadRun();
  const asset = ASSETS[run.assetIndex] || ASSETS[0];

  useEffect(() => {
    document.title = "Dimension AI text-to-CAD";
    document.documentElement.classList.remove("dark");
    document.documentElement.dataset.theme = "light";
    return () => {
      delete document.documentElement.dataset.theme;
    };
  }, []);

  return (
    <div className="flex h-screen min-h-[720px] overflow-hidden bg-[var(--dd-bg)] text-[var(--dd-fg)]" style={DIMENSION_DEMO_THEME}>
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar status={run.status} mode={run.mode} onModeChange={run.setMode} />
        {run.status === "idle" ? (
          <main className="flex min-h-0 flex-1 bg-[var(--dd-bg)]">
            <IdlePane run={run} />
          </main>
        ) : run.mode === RUN_MODES.VALIDATE ? (
          <div className="flex min-h-0 flex-1 flex-col">
            <ValidateBrowserPane asset={asset} showWorkspace={run.status === "done"} fullWidth={true} />
            <StatusBar mode={run.mode} />
          </div>
        ) : run.isBatch ? (
          <div className="grid min-h-0 flex-1 grid-cols-[46%_54%]">
            <section className="flex min-h-0 flex-col bg-[var(--dd-bg)]">
              <BatchRunPane run={run} />
              <StatusBar mode={run.mode} />
            </section>
            <BrowserPane asset={asset} showModel={(run.activeBatchItem?.progress ?? 0) >= 72 || run.status === "done"} />
          </div>
        ) : (
          <div className="grid min-h-0 flex-1 grid-cols-[45%_55%]">
            <section className="flex min-h-0 flex-col bg-[var(--dd-bg)]">
              <RunPane run={run} />
              <StatusBar mode={run.mode} />
            </section>
            <BrowserPane asset={asset} showModel={run.status === "done"} />
          </div>
        )}
      </div>
    </div>
  );
}
