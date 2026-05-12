import { useMemo } from "react";
import { Box, ChevronRight, PanelLeft, Plus } from "lucide-react";
import ArtifactPanel from "./ArtifactPanel";
import DimensionComposer from "./DimensionComposer";
import DimensionViewerPane from "./DimensionViewerPane";
import RunTimeline from "./RunTimeline";
import { useDimensionRuns } from "./useDimensionRuns";

const PRODUCT_THEME = {
  fontFamily: "\"Inter\", \"Geist\", ui-sans-serif, system-ui, -apple-system, \"Segoe UI\", sans-serif",
};

function modeLabel(mode = "") {
  return String(mode || "")
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function selectedArtifactForRun(run) {
  if (!run) {
    return { key: "", artifact: null, glbUrl: "", modelLabel: "" };
  }

  const selectedKey = run.selectedArtifact || "glb";
  const selectedArtifact = run.artifacts?.[selectedKey] || null;
  return {
    key: selectedKey,
    artifact: selectedArtifact,
    glbUrl: selectedArtifact?.kind === "glb" ? selectedArtifact.url || "" : "",
    modelLabel: selectedArtifact?.label || run.uploadedFiles?.[0]?.name || run.id,
  };
}

export default function DimensionProductApp({ manifestEntries = [] }) {
  const {
    runs,
    activeRun,
    activeRunId,
    sampleEntries,
    createRunFromUpload,
    createRunFromCatalogEntry,
    selectArtifact,
    setActiveRunId,
    clearActiveRun,
  } = useDimensionRuns({ manifestEntries });

  const selected = useMemo(() => selectedArtifactForRun(activeRun), [activeRun]);
  const hasActiveRun = Boolean(activeRun);

  function handleSelectArtifact(artifactKey) {
    if (!activeRun) {
      return;
    }
    selectArtifact(activeRun.id, artifactKey);
  }

  return (
    <div className="flex h-screen min-h-[620px] flex-col overflow-hidden bg-neutral-50 text-neutral-950" style={PRODUCT_THEME}>
      <header className="flex h-12 shrink-0 items-center justify-between border-b border-neutral-200 bg-white px-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md border border-neutral-200 bg-neutral-950 text-white">
            <Box className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-semibold leading-none tracking-tight">Dimension</p>
            <p className="mt-0.5 text-[10px] uppercase tracking-[0.18em] text-neutral-400">CAD Workbench</p>
          </div>
        </div>
        <nav className="hidden items-center gap-1 text-xs text-neutral-500 sm:flex">
          <a className="rounded-md px-2 py-1 hover:bg-neutral-100 hover:text-neutral-900" href="/workbench">Workbench</a>
          <a className="rounded-md px-2 py-1 hover:bg-neutral-100 hover:text-neutral-900" href="/dimension-demo">Demo</a>
        </nav>
      </header>

      {!hasActiveRun ? (
        <main className="flex min-h-0 flex-1 flex-col items-center justify-center px-5 py-10">
          <div className="mb-8 max-w-2xl text-center">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-neutral-400">Product frontend foundation</p>
            <h1 className="mt-3 text-2xl font-semibold tracking-tight text-neutral-950 sm:text-3xl">
              Start with a real CAD input.
            </h1>
            <p className="mt-3 text-sm leading-6 text-neutral-500">
              Upload a STEP/STP file to create a local Dimension run. Backend conversion is not connected yet, so viewer output appears only when a real GLB artifact exists.
            </p>
          </div>
          <DimensionComposer
            onCreateRun={createRunFromUpload}
            sampleEntries={sampleEntries}
            onCreateSampleRun={createRunFromCatalogEntry}
          />
        </main>
      ) : (
        <main className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[390px_minmax(0,1fr)]">
          <aside className="flex min-h-0 flex-col gap-4 overflow-y-auto border-r border-neutral-200 bg-neutral-50 p-4">
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs font-medium uppercase tracking-[0.16em] text-neutral-400">Current run</p>
                <h1 className="mt-1 truncate text-lg font-semibold text-neutral-950">
                  {activeRun.uploadedFiles?.[0]?.name || activeRun.id}
                </h1>
              </div>
              <button
                type="button"
                className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-neutral-200 bg-white text-neutral-600 hover:border-neutral-300 hover:text-neutral-950"
                aria-label="Start a new run"
                onClick={clearActiveRun}
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>

            <div className="rounded-xl border border-neutral-200 bg-white p-4">
              <p className="text-xs font-medium uppercase tracking-[0.16em] text-neutral-400">Run state</p>
              <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="text-xs text-neutral-400">Mode</dt>
                  <dd className="mt-1 font-medium text-neutral-900">{modeLabel(activeRun.mode)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-neutral-400">Status</dt>
                  <dd className="mt-1 font-medium capitalize text-neutral-900">{activeRun.status}</dd>
                </div>
              </dl>
              {activeRun.prompt ? (
                <p className="mt-3 rounded-lg bg-neutral-50 px-3 py-2 text-sm leading-6 text-neutral-600">{activeRun.prompt}</p>
              ) : null}
            </div>

            <RunTimeline run={activeRun} />
            <ArtifactPanel
              run={activeRun}
              selectedArtifactKey={activeRun.selectedArtifact}
              onSelectArtifact={handleSelectArtifact}
            />

            <DimensionComposer
              compact={true}
              onCreateRun={createRunFromUpload}
              sampleEntries={sampleEntries}
              onCreateSampleRun={createRunFromCatalogEntry}
            />

            {runs.length > 1 ? (
              <section className="rounded-xl border border-neutral-200 bg-white p-4">
                <p className="text-xs font-medium uppercase tracking-[0.16em] text-neutral-400">Runs</p>
                <div className="mt-3 space-y-2">
                  {runs.map((run) => (
                    <button
                      key={run.id}
                      type="button"
                      className={run.id === activeRunId
                        ? "flex w-full items-center justify-between gap-2 rounded-lg border border-neutral-900 bg-neutral-900 px-3 py-2 text-left text-white"
                        : "flex w-full items-center justify-between gap-2 rounded-lg border border-neutral-200 bg-white px-3 py-2 text-left text-neutral-700 hover:border-neutral-300 hover:bg-neutral-50"}
                      onClick={() => setActiveRunId(run.id)}
                    >
                      <span className="min-w-0 truncate text-sm font-medium">{run.uploadedFiles?.[0]?.name || run.id}</span>
                      <ChevronRight className="h-4 w-4 shrink-0" />
                    </button>
                  ))}
                </div>
              </section>
            ) : null}
          </aside>

          <div className="min-h-0 bg-white">
            <DimensionViewerPane
              selectedArtifact={selected.artifact}
              glbUrl={selected.glbUrl}
              modelLabel={selected.modelLabel}
              loading={false}
              error=""
            />
          </div>
        </main>
      )}

      <div className="pointer-events-none fixed bottom-3 left-3 hidden items-center gap-2 rounded-full border border-neutral-200 bg-white/90 px-3 py-1.5 text-xs text-neutral-500 shadow-[0_14px_35px_-28px_rgba(0,0,0,0.45)] backdrop-blur lg:flex">
        <PanelLeft className="h-3.5 w-3.5" />
        Local run state · conversion pending
      </div>
    </div>
  );
}
