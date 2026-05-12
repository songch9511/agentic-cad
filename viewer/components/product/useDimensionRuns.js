import { useCallback, useMemo, useState } from "react";

export const DIMENSION_RUN_MODES = Object.freeze({
  TEXT_TO_CAD: "text_to_cad",
  DRAWING_TO_CAD: "drawing_to_cad",
  VALIDATE: "validate",
  BATCH: "batch",
});

export const DIMENSION_RUN_STATUSES = Object.freeze({
  IDLE: "idle",
  QUEUED: "queued",
  RUNNING: "running",
  SUCCEEDED: "succeeded",
  FAILED: "failed",
});

const STEP_EXTENSIONS = new Set(["step", "stp"]);

function extensionForName(name = "") {
  const parts = String(name || "").toLowerCase().split(".");
  return parts.length > 1 ? parts.pop() : "";
}

export function isStepFile(file) {
  return STEP_EXTENSIONS.has(extensionForName(file?.name));
}

function createRunId(prefix = "run") {
  const timestamp = Date.now().toString(36);
  const suffix = Math.random().toString(36).slice(2, 8);
  return `${prefix}-${timestamp}-${suffix}`;
}

function fileMetadata(file) {
  return {
    id: createRunId("file"),
    name: file.name,
    size: file.size,
    type: file.type || "model/step",
    extension: extensionForName(file.name),
    lastModified: file.lastModified || null,
  };
}

function formatBytes(value) {
  const bytes = Number(value || 0);
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return "0 B";
  }
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function artifactFromManifestAsset(kind, asset, fallbackLabel) {
  if (!asset?.url) {
    return null;
  }
  return {
    kind,
    label: fallbackLabel,
    url: asset.url,
    path: asset.path || asset.url,
    hash: asset.hash || "",
    source: "local_manifest",
  };
}

function stepArtifactFromEntry(entry) {
  const sourcePath = entry?.step?.path || entry?.source?.path || entry?.file || entry?.name || "";
  if (!sourcePath) {
    return null;
  }
  return {
    kind: "step",
    label: entry?.name || sourcePath.split("/").pop() || "STEP source",
    path: sourcePath,
    hash: entry?.step?.hash || "",
    source: "local_manifest",
  };
}

function sampleEntryHasGlb(entry) {
  return Boolean(entry?.assets?.glb?.url);
}

function compareSampleEntries(left, right) {
  return String(left?.name || left?.file || "").localeCompare(String(right?.name || right?.file || ""), undefined, {
    numeric: true,
    sensitivity: "base",
  });
}

export function useDimensionRuns({ manifestEntries = [] } = {}) {
  const [runs, setRuns] = useState([]);
  const [activeRunId, setActiveRunId] = useState("");

  const sampleEntries = useMemo(
    () => (Array.isArray(manifestEntries) ? manifestEntries : [])
      .filter(sampleEntryHasGlb)
      .sort(compareSampleEntries),
    [manifestEntries],
  );

  const activeRun = useMemo(
    () => activeRunId ? runs.find((run) => run.id === activeRunId) || null : null,
    [activeRunId, runs],
  );

  const createRunFromUpload = useCallback(({ file, prompt = "", mode = DIMENSION_RUN_MODES.TEXT_TO_CAD } = {}) => {
    if (!file) {
      throw new Error("Choose a STEP or STP file to start a Dimension run.");
    }
    if (!isStepFile(file)) {
      throw new Error("Dimension currently accepts STEP or STP files for this local workflow.");
    }

    const now = new Date().toISOString();
    const metadata = fileMetadata(file);
    const run = {
      id: createRunId(),
      mode,
      status: DIMENSION_RUN_STATUSES.QUEUED,
      prompt: String(prompt || "").trim(),
      uploadedFiles: [metadata],
      steps: [
        {
          id: "source-uploaded",
          label: "STEP file received",
          status: DIMENSION_RUN_STATUSES.SUCCEEDED,
          detail: `${metadata.name} · ${formatBytes(metadata.size)}`,
        },
        {
          id: "cad-artifact-awaiting-conversion",
          label: "CAD artifact generation",
          status: DIMENSION_RUN_STATUSES.QUEUED,
          detail: "Conversion is not connected yet. A GLB viewer artifact is required before the model can be shown.",
        },
      ],
      artifacts: {
        step: {
          kind: "step",
          label: metadata.name,
          fileName: metadata.name,
          size: metadata.size,
          source: "upload",
          note: "Awaiting CAD artifact",
        },
        glb: null,
        topology: null,
        source: {
          kind: "source",
          label: metadata.name,
          fileName: metadata.name,
          size: metadata.size,
          source: "upload",
        },
        report: null,
      },
      selectedArtifact: "step",
      createdAt: now,
      updatedAt: now,
    };

    setRuns((currentRuns) => [run, ...currentRuns]);
    setActiveRunId(run.id);
    return run;
  }, []);

  const createRunFromCatalogEntry = useCallback((entry) => {
    const glb = artifactFromManifestAsset("glb", entry?.assets?.glb, `${entry?.name || "Local CAD model"} GLB`);
    if (!glb) {
      throw new Error("This local CAD entry does not include a GLB viewer artifact.");
    }

    const topology = artifactFromManifestAsset("topology", entry?.assets?.topology, `${entry?.name || "Local CAD model"} topology`);
    const step = stepArtifactFromEntry(entry);
    const now = new Date().toISOString();
    const run = {
      id: createRunId("local"),
      mode: DIMENSION_RUN_MODES.TEXT_TO_CAD,
      status: DIMENSION_RUN_STATUSES.SUCCEEDED,
      prompt: "",
      uploadedFiles: [],
      steps: [
        {
          id: "local-source-found",
          label: "Local STEP source found",
          status: DIMENSION_RUN_STATUSES.SUCCEEDED,
          detail: step?.path || entry?.file || entry?.name || "Local CAD source",
        },
        {
          id: "local-glb-ready",
          label: "GLB viewer artifact ready",
          status: DIMENSION_RUN_STATUSES.SUCCEEDED,
          detail: glb.path || glb.url,
        },
      ],
      artifacts: {
        step,
        glb,
        topology,
        source: entry?.source ? {
          kind: "source",
          label: entry.name || entry.file || "Local source",
          path: entry.source.path || entry.file || "",
          format: entry.source.format || entry.kind || "step",
          source: "local_manifest",
        } : step,
        report: null,
      },
      selectedArtifact: "glb",
      createdAt: now,
      updatedAt: now,
    };

    setRuns((currentRuns) => [run, ...currentRuns]);
    setActiveRunId(run.id);
    return run;
  }, []);

  const selectArtifact = useCallback((runId, artifactKey) => {
    setRuns((currentRuns) => currentRuns.map((run) => {
      if (run.id !== runId || !(artifactKey in run.artifacts)) {
        return run;
      }
      return {
        ...run,
        selectedArtifact: artifactKey,
        updatedAt: new Date().toISOString(),
      };
    }));
  }, []);

  const clearActiveRun = useCallback(() => {
    setActiveRunId("");
  }, []);

  return {
    runs,
    activeRun,
    activeRunId,
    sampleEntries,
    createRunFromUpload,
    createRunFromCatalogEntry,
    selectArtifact,
    setActiveRunId,
    clearActiveRun,
  };
}
