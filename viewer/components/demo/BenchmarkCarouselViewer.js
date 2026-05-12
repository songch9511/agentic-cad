"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ExternalLink, Globe, Loader2, PanelRight, Plus, RefreshCw } from "lucide-react";
import CadViewer from "../CadViewer";
import { DEFAULT_LOOK_SETTINGS, LOOK_FLOOR_MODES } from "../../lib/lookSettings";
import { loadRenderGlb } from "../../lib/renderAssetClient";
import { VIEWER_PICK_MODE } from "../../lib/viewer/constants";

const EMPTY_VIEWER_ITEMS = Object.freeze([]);
const AUTO_ADVANCE_MS = 5200;
const ERROR_ADVANCE_MS = 2200;
const FIRST_MODEL_LABELS = new Map([
  ["model_006_pipe_elbow.step", 0],
]);

const DIMENSION_VIEWER_THEME = {
  "--dd-bg": "#fafafa",
  "--dd-panel": "#ffffff",
  "--dd-panel-muted": "#f5f5f5",
  "--dd-control": "#ffffff",
  "--dd-border": "#e5e5e5",
  "--dd-fg": "#0a0a0a",
  "--dd-fg-muted": "#404040",
  "--dd-fg-subtle": "#737373",
  "--dd-fg-faint": "#a3a3a3",
  "--dd-accent": "#0090ff",
  "--dd-render-bg": "#f5f5f5",
  "--dd-radius-control": "6px",
  "--dd-font-sans": "\"Inter\", \"Geist\", ui-sans-serif, system-ui, -apple-system, \"Segoe UI\", sans-serif",
  "--dd-font-mono": "\"Geist Mono\", \"JetBrains Mono\", ui-monospace, \"SF Mono\", Menlo, Consolas, monospace",
  fontFamily: "var(--dd-font-sans)",
};

function normalizePath(value) {
  return String(value || "").replace(/\\/g, "/").replace(/^\/+/, "").replace(/\/+$/, "");
}

function isTopLevelBenchmarkEntry(entry) {
  const file = normalizePath(entry?.file);
  if (!file) {
    return false;
  }
  const parts = file.split("/").filter(Boolean);
  if (parts[0] === "benchmarks") {
    return parts.length === 2;
  }
  return parts.length === 1;
}

function compareAssetLabels(a, b) {
  const aPriority = FIRST_MODEL_LABELS.get(String(a.label || "")) ?? 100;
  const bPriority = FIRST_MODEL_LABELS.get(String(b.label || "")) ?? 100;
  if (aPriority !== bPriority) {
    return aPriority - bPriority;
  }
  return String(a.label || "").localeCompare(String(b.label || ""), undefined, {
    numeric: true,
    sensitivity: "base",
  });
}

function buildBenchmarkAssets(manifestEntries) {
  return (Array.isArray(manifestEntries) ? manifestEntries : [])
    .filter((entry) => {
      const format = String(entry?.source?.format || "").toLowerCase();
      return (format === "step" || format === "stp") && entry?.assets?.glb?.url && isTopLevelBenchmarkEntry(entry);
    })
    .map((entry) => ({
      id: normalizePath(entry.cadPath || entry.file || entry.name),
      label: String(entry.name || entry.file || "benchmark.step"),
      path: entry.assets.glb.url,
      url: `app.dimension-cad.com/model/${String(entry.name || entry.file || "benchmark.step")}`,
    }))
    .sort(compareAssetLabels);
}

function useCarouselMesh(asset) {
  const [meshData, setMeshData] = useState(null);
  const [status, setStatus] = useState(asset ? "loading" : "idle");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!asset?.path) {
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
          setMeshData(null);
          setStatus("error");
          setError(loadError?.message || "Failed to load CAD asset.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [asset?.path]);

  return { meshData, status, error };
}

function useDemoLookSettings() {
  return useMemo(() => ({
    ...DEFAULT_LOOK_SETTINGS,
    background: {
      ...DEFAULT_LOOK_SETTINGS.background,
      type: "linear",
      color: "#f5f5f5",
      color2: "#ffffff",
      gradientDirection: 180,
    },
    materials: {
      ...DEFAULT_LOOK_SETTINGS.materials,
      sourceColors: false,
      surfaceColor: "#f8fafc",
      metalness: 0.02,
      roughness: 0.7,
      opacity: 1,
    },
    edges: {
      ...DEFAULT_LOOK_SETTINGS.edges,
      enabled: false,
    },
    shadows: {
      ...DEFAULT_LOOK_SETTINGS.shadows,
      enabled: true,
      opacity: 0.18,
      blur: 1.35,
    },
    lighting: {
      ...DEFAULT_LOOK_SETTINGS.lighting,
      ambient: {
        ...DEFAULT_LOOK_SETTINGS.lighting.ambient,
        enabled: true,
        intensity: 1.35,
      },
      directional: {
        ...DEFAULT_LOOK_SETTINGS.lighting.directional,
        enabled: true,
        intensity: 4.2,
        color: "#ffffff",
        position: { x: -80, y: 120, z: 110 },
      },
      hemisphere: {
        ...DEFAULT_LOOK_SETTINGS.lighting.hemisphere,
        enabled: true,
        intensity: 2.1,
        skyColor: "#ffffff",
        groundColor: "#d4d4d4",
      },
    },
  }), []);
}

function ViewerChrome({ asset, children }) {
  return (
    <div className="flex h-screen min-h-[520px] flex-col overflow-hidden bg-[var(--dd-panel)] text-[var(--dd-fg)]" style={DIMENSION_VIEWER_THEME}>
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
          {asset?.url || "app.dimension-cad.com/model/benchmarks"}
        </div>
        <div className="flex items-center gap-3">
          <ExternalLink className="h-4 w-4" />
          <PanelRight className="h-4 w-4" />
        </div>
      </div>
      {children}
    </div>
  );
}

function EmptyBenchmarks() {
  return (
    <div className="flex min-h-0 flex-1 items-center justify-center bg-[var(--dd-render-bg)] px-6 text-center text-sm text-[var(--dd-fg-subtle)]">
      No benchmark STEP models with generated GLB viewer assets were found.
    </div>
  );
}

function BenchmarkRenderPane({ asset, assetIndex, assetCount, onStatusChange }) {
  const viewerRef = useRef(null);
  const perspectiveRef = useRef(null);
  const [viewerAlert, setViewerAlert] = useState(null);
  const { meshData, status, error } = useCarouselMesh(asset);
  const lookSettings = useDemoLookSettings();
  const shouldShowModel = status === "ready";
  const viewerLoading = status !== "error" && !shouldShowModel;

  useEffect(() => {
    onStatusChange?.(status);
  }, [onStatusChange, status]);

  useEffect(() => {
    if (!asset?.path || assetCount <= 1) {
      return;
    }
    const nextPath = asset?.nextPath;
    if (nextPath) {
      loadRenderGlb(nextPath).catch(() => {});
    }
  }, [asset?.path, asset?.nextPath, assetCount]);

  return (
    <div className="relative min-h-0 flex-1 overflow-hidden bg-[var(--dd-render-bg)]">
      <CadViewer
        ref={viewerRef}
        meshData={shouldShowModel ? meshData : null}
        modelKey={asset?.id || "benchmark-carousel"}
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
            className="flex h-12 w-12 animate-spin items-center justify-center rounded-full border border-[var(--dd-border)] bg-white/88 text-[var(--dd-fg-subtle)] shadow-[0_14px_30px_-22px_rgba(0,0,0,0.24)] backdrop-blur"
            role="status"
            aria-label="Loading CAD model"
          >
            <Loader2 className="h-7 w-7" aria-hidden="true" />
          </div>
        </div>
      ) : null}
      <div className="pointer-events-none absolute bottom-4 left-4 rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-white/88 px-3 py-2 text-xs text-[var(--dd-fg-subtle)] shadow-[0_8px_20px_-18px_rgba(0,0,0,0.18)] backdrop-blur" style={{ fontFamily: "var(--dd-font-mono)" }}>
        {asset?.label || "benchmark.step"}
      </div>
      {assetCount > 1 ? (
        <div className="pointer-events-none absolute bottom-4 right-4 rounded-[var(--dd-radius-control)] border border-[var(--dd-border)] bg-white/88 px-3 py-2 text-xs text-[var(--dd-fg-subtle)] shadow-[0_8px_20px_-18px_rgba(0,0,0,0.18)] backdrop-blur" style={{ fontFamily: "var(--dd-font-mono)" }}>
          {assetIndex + 1} / {assetCount}
        </div>
      ) : null}
      {status === "error" || viewerAlert ? (
        <div className="absolute inset-x-5 bottom-5 rounded-[var(--dd-radius-control)] border border-[rgba(220,38,38,0.42)] bg-white p-3 text-sm text-red-600 shadow-[0_12px_24px_-18px_rgba(0,0,0,0.18)]">
          {error || viewerAlert?.message || "CAD viewer error"}
        </div>
      ) : null}
    </div>
  );
}

export default function BenchmarkCarouselViewer({ manifestEntries }) {
  const assets = useMemo(() => buildBenchmarkAssets(manifestEntries), [manifestEntries]);
  const [assetIndex, setAssetIndex] = useState(0);
  const [activeStatus, setActiveStatus] = useState("idle");
  const activeAsset = assets[assetIndex] || null;
  const nextAsset = assets.length > 1 ? assets[(assetIndex + 1) % assets.length] : null;
  const asset = activeAsset ? { ...activeAsset, nextPath: nextAsset?.path || "" } : null;

  useEffect(() => {
    setAssetIndex((current) => Math.min(current, Math.max(assets.length - 1, 0)));
  }, [assets.length]);

  useEffect(() => {
    setActiveStatus(asset ? "loading" : "idle");
  }, [asset?.id]);

  useEffect(() => {
    if (assets.length <= 1 || (activeStatus !== "ready" && activeStatus !== "error")) {
      return undefined;
    }
    const timer = window.setTimeout(() => {
      setAssetIndex((current) => (current + 1) % assets.length);
    }, activeStatus === "ready" ? AUTO_ADVANCE_MS : ERROR_ADVANCE_MS);
    return () => window.clearTimeout(timer);
  }, [activeStatus, assets.length, asset?.id]);

  useEffect(() => {
    document.title = "Dimension benchmark CAD viewer";
    document.documentElement.classList.remove("dark");
    document.documentElement.dataset.theme = "light";
    return () => {
      delete document.documentElement.dataset.theme;
    };
  }, []);

  return (
    <ViewerChrome asset={asset}>
      {asset ? (
        <BenchmarkRenderPane
          asset={asset}
          assetIndex={assetIndex}
          assetCount={assets.length}
          onStatusChange={setActiveStatus}
        />
      ) : (
        <EmptyBenchmarks />
      )}
    </ViewerChrome>
  );
}
