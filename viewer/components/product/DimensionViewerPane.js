import { useEffect, useMemo, useRef, useState } from "react";
import CadViewer from "../CadViewer";
import { DEFAULT_LOOK_SETTINGS, LOOK_FLOOR_MODES } from "../../lib/lookSettings";
import { loadRenderGlb } from "../../lib/renderAssetClient";
import { VIEWER_PICK_MODE } from "../../lib/viewer/constants";

const EMPTY_VIEWER_ITEMS = Object.freeze([]);

function useProductLookSettings() {
  return useMemo(() => ({
    ...DEFAULT_LOOK_SETTINGS,
    background: {
      ...DEFAULT_LOOK_SETTINGS.background,
      type: "solid",
      color: "#f6f6f6",
      color2: "#ffffff",
    },
    materials: {
      ...DEFAULT_LOOK_SETTINGS.materials,
      sourceColors: false,
      surfaceColor: "#f8fafc",
      metalness: 0.02,
      roughness: 0.74,
      opacity: 1,
    },
    edges: {
      ...DEFAULT_LOOK_SETTINGS.edges,
      enabled: false,
    },
    shadows: {
      ...DEFAULT_LOOK_SETTINGS.shadows,
      enabled: true,
      opacity: 0.14,
      blur: 1.25,
    },
  }), []);
}

export default function DimensionViewerPane({
  selectedArtifact = null,
  glbUrl = "",
  modelLabel = "CAD model",
  loading = false,
  error = "",
}) {
  const viewerRef = useRef(null);
  const perspectiveRef = useRef(null);
  const [viewerAlert, setViewerAlert] = useState(null);
  const [meshData, setMeshData] = useState(null);
  const [loadStatus, setLoadStatus] = useState(glbUrl ? "loading" : "idle");
  const [loadError, setLoadError] = useState("");
  const lookSettings = useProductLookSettings();

  useEffect(() => {
    if (!glbUrl) {
      setMeshData(null);
      setLoadStatus("idle");
      setLoadError("");
      return undefined;
    }

    let cancelled = false;
    setLoadStatus("loading");
    setLoadError("");
    loadRenderGlb(glbUrl)
      .then((loadedMeshData) => {
        if (!cancelled) {
          setMeshData(loadedMeshData);
          setLoadStatus("ready");
        }
      })
      .catch((loadFailure) => {
        if (!cancelled) {
          setMeshData(null);
          setLoadStatus("error");
          setLoadError(loadFailure?.message || "Failed to load GLB artifact.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [glbUrl]);

  const effectiveError = error || loadError || viewerAlert?.message || "";
  const effectiveLoading = loading || loadStatus === "loading";
  const canShowViewer = Boolean(glbUrl);
  const canRenderMesh = loadStatus === "ready" && meshData;

  if (!canShowViewer) {
    return (
      <section className="flex h-full min-h-[420px] flex-col overflow-hidden rounded-none border-l border-neutral-200 bg-neutral-50">
        <div className="flex h-12 shrink-0 items-center justify-between border-b border-neutral-200 bg-white px-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-neutral-400">Viewer</p>
            <h2 className="text-sm font-semibold text-neutral-900">Awaiting CAD artifact</h2>
          </div>
        </div>
        <div className="flex min-h-0 flex-1 items-center justify-center px-8 text-center">
          <div className="max-w-sm">
            <p className="text-base font-medium text-neutral-900">No GLB artifact selected</p>
            <p className="mt-2 text-sm leading-6 text-neutral-500">
              Uploads are tracked as product runs, but STEP/STP conversion is not connected yet. The viewer appears only after a run has a GLB artifact.
            </p>
            {selectedArtifact?.label ? (
              <p className="mt-4 rounded-md border border-neutral-200 bg-white px-3 py-2 text-xs text-neutral-500">
                Selected artifact: {selectedArtifact.label}
              </p>
            ) : null}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="relative flex h-full min-h-[420px] flex-col overflow-hidden border-l border-neutral-200 bg-neutral-50">
      <div className="flex h-12 shrink-0 items-center justify-between border-b border-neutral-200 bg-white px-4">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-neutral-400">Viewer</p>
          <h2 className="truncate text-sm font-semibold text-neutral-900">{modelLabel}</h2>
        </div>
        <div className="rounded-md border border-neutral-200 bg-neutral-50 px-2 py-1 text-xs text-neutral-500">
          GLB
        </div>
      </div>
      <div className="relative min-h-0 flex-1 overflow-hidden bg-neutral-100">
        <CadViewer
          ref={viewerRef}
          meshData={canRenderMesh ? meshData : null}
          modelKey={glbUrl || modelLabel}
          perspectiveRef={perspectiveRef}
          showEdges={false}
          recomputeNormals={false}
          lookSettings={lookSettings}
          floorModeOverride={LOOK_FLOOR_MODES.STAGE}
          previewMode={true}
          showViewPlane={true}
          compactViewPlane={true}
          isLoading={effectiveLoading}
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
        {effectiveLoading ? (
          <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center bg-white/30 text-sm text-neutral-500 backdrop-blur-[1px]">
            Loading CAD viewer artifact…
          </div>
        ) : null}
        {effectiveError ? (
          <div className="absolute left-4 right-4 top-4 z-20 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {effectiveError}
          </div>
        ) : null}
      </div>
    </section>
  );
}
