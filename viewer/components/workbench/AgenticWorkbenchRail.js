"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BadgeCheck,
  Bot,
  Boxes,
  CheckCircle2,
  CircleDashed,
  ClipboardCheck,
  DraftingCompass,
  FileCode2,
  Gauge,
  GitBranch,
  LoaderCircle,
  Play,
  Ruler,
  Send,
  TerminalSquare,
  TriangleAlert
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { RENDER_FORMAT } from "../../lib/workbench/constants";

const WORKFLOW_OPTIONS = [
  {
    id: "text-to-cad",
    label: "Text to CAD",
    Icon: Bot
  },
  {
    id: "drawing-to-cad",
    label: "Drawing",
    Icon: DraftingCompass
  },
  {
    id: "gdnt",
    label: "GD&T",
    Icon: Ruler
  },
  {
    id: "assembly",
    label: "Assembly",
    Icon: Boxes
  }
];

const STATUS_TONE_CLASSES = {
  pass: "border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
  running: "border-sky-500/25 bg-sky-500/10 text-sky-700 dark:text-sky-200",
  warn: "border-amber-500/30 bg-amber-500/10 text-amber-800 dark:text-amber-200",
  idle: "border-border/80 bg-muted/40 text-muted-foreground"
};

function sourcePathForEntry(entry) {
  return String(entry?.source?.path || entry?.step?.path || entry?.id || "").trim();
}

function renderFormatLabel(renderFormat, entry) {
  if (entry?.kind === "assembly") {
    return "Assembly";
  }
  if (entry?.kind === "urdf" || renderFormat === RENDER_FORMAT.URDF) {
    return "URDF";
  }
  if (renderFormat === RENDER_FORMAT.DXF) {
    return "DXF";
  }
  if (renderFormat === RENDER_FORMAT.STL) {
    return "STL";
  }
  return "STEP";
}

function countEntryAssetPaths(value) {
  if (!value || typeof value !== "object") {
    return 0;
  }
  if (Array.isArray(value)) {
    return value.reduce((total, item) => total + countEntryAssetPaths(item), 0);
  }
  return Object.entries(value).reduce((total, [key, item]) => {
    if (key === "path" && typeof item === "string" && item.trim()) {
      return total + 1;
    }
    return total + countEntryAssetPaths(item);
  }, 0);
}

function StatusIcon({ state }) {
  if (state === "pass") {
    return <CheckCircle2 className="size-3.5" aria-hidden="true" />;
  }
  if (state === "running") {
    return <LoaderCircle className="size-3.5 animate-spin" aria-hidden="true" />;
  }
  if (state === "warn") {
    return <TriangleAlert className="size-3.5" aria-hidden="true" />;
  }
  return <CircleDashed className="size-3.5" aria-hidden="true" />;
}

function StatusPill({ state, children }) {
  return (
    <span
      className={cn(
        "inline-flex h-6 min-w-0 items-center gap-1 rounded-md border px-2 text-[10px] font-semibold",
        STATUS_TONE_CLASSES[state] || STATUS_TONE_CLASSES.idle
      )}
    >
      <StatusIcon state={state} />
      <span className="truncate">{children}</span>
    </span>
  );
}

function WorkflowButton({ option, active, suggested, onClick }) {
  const Icon = option.Icon;

  return (
    <button
      type="button"
      aria-pressed={active}
      title={option.label}
      onClick={onClick}
      className={cn(
        "flex h-10 min-w-0 items-center gap-2 rounded-md border px-2.5 text-left text-[11px] font-semibold transition-colors",
        active
          ? "border-primary/45 bg-primary/12 text-foreground shadow-sm"
          : "border-border/70 bg-background/45 text-muted-foreground hover:border-primary/35 hover:text-foreground"
      )}
    >
      <Icon className="size-4 shrink-0" strokeWidth={2} aria-hidden="true" />
      <span className="min-w-0 flex-1 truncate">{option.label}</span>
      {suggested ? (
        <span className="size-1.5 shrink-0 rounded-full bg-primary" aria-hidden="true" />
      ) : null}
    </button>
  );
}

function LoopRow({ Icon, title, detail, state }) {
  return (
    <div className="flex min-w-0 items-start gap-2 rounded-md border border-border/60 bg-background/35 px-2.5 py-2">
      <div
        className={cn(
          "mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-md border",
          STATUS_TONE_CLASSES[state] || STATUS_TONE_CLASSES.idle
        )}
      >
        <Icon className="size-3.5" strokeWidth={2} aria-hidden="true" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex min-w-0 items-center justify-between gap-2">
          <p className="truncate text-[11px] font-semibold text-foreground">{title}</p>
          <StatusIcon state={state} />
        </div>
        <p className="mt-0.5 line-clamp-2 text-[10px] leading-4 text-muted-foreground">{detail}</p>
      </div>
    </div>
  );
}

export default function AgenticWorkbenchRail({
  compact = false,
  selectedEntry,
  selectedEntryLabel,
  renderFormat,
  selectedMeshData,
  selectedDxfData,
  selectedUrdfData,
  catalogEntries = [],
  viewerLoading,
  viewerAlert,
  stepUpdateInProgress,
  selectionCount = 0,
  selectedReferenceCount = 0,
  isAssemblyView
}) {
  const suggestedWorkflowId = useMemo(() => {
    if (isAssemblyView || selectedEntry?.kind === "assembly" || selectedEntry?.kind === "urdf") {
      return "assembly";
    }
    if (renderFormat === RENDER_FORMAT.DXF) {
      return "drawing-to-cad";
    }
    return "text-to-cad";
  }, [isAssemblyView, renderFormat, selectedEntry?.kind]);
  const [activeWorkflowId, setActiveWorkflowId] = useState(suggestedWorkflowId);
  const [draft, setDraft] = useState("Create a manufacturable variant and run geometry checks.");
  const [lastPrompt, setLastPrompt] = useState("");
  const [commandCopied, setCommandCopied] = useState(false);

  useEffect(() => {
    setActiveWorkflowId(suggestedWorkflowId);
  }, [suggestedWorkflowId]);

  const activeWorkflow = WORKFLOW_OPTIONS.find((option) => option.id === activeWorkflowId) || WORKFLOW_OPTIONS[0];
  const entryPath = sourcePathForEntry(selectedEntry);
  const hasGeometry = Boolean(selectedMeshData || selectedDxfData || selectedUrdfData);
  const meshPartCount = Array.isArray(selectedMeshData?.parts) ? selectedMeshData.parts.length : 0;
  const assetCount = selectedEntry ? countEntryAssetPaths(selectedEntry) : 0;
  const benchmarkCommand = "python3 benchmarks/run_benchmark.py benchmarks/tasks/smoke.json --json-out benchmark-results/smoke.json";
  const selectedFormatLabel = renderFormatLabel(renderFormat, selectedEntry);
  const artifactLabel = selectedEntryLabel || "No artifact selected";
  const readyState = viewerLoading
    ? "running"
    : viewerAlert
      ? "warn"
      : selectedEntry
        ? "pass"
        : "idle";
  const geometryState = viewerLoading
    ? "running"
    : viewerAlert
      ? "warn"
      : hasGeometry
        ? "pass"
        : selectedEntry
          ? "warn"
          : "idle";
  const benchmarkState = catalogEntries.length > 0 ? "pass" : "idle";
  const verificationState = stepUpdateInProgress
    ? "running"
    : viewerAlert
      ? "warn"
      : hasGeometry
        ? "pass"
        : "idle";
  const loopRows = [
    {
      title: "Intent",
      detail: selectedEntry ? `${artifactLabel} is the active CAD target.` : "Waiting for a CAD artifact.",
      state: selectedEntry ? "pass" : "idle",
      Icon: FileCode2
    },
    {
      title: "Build",
      detail: viewerLoading
        ? "Loading render assets."
        : hasGeometry
          ? `${selectedFormatLabel} render assets are available.`
          : "Render asset is not ready.",
      state: geometryState,
      Icon: GitBranch
    },
    {
      title: "Evaluator",
      detail: viewerAlert
        ? viewerAlert.summary || viewerAlert.title || "Viewer raised a validation warning."
        : `${selectionCount + selectedReferenceCount} selectable references tracked.`,
      state: viewerAlert ? "warn" : hasGeometry ? "pass" : "idle",
      Icon: ClipboardCheck
    },
    {
      title: "Benchmark",
      detail: "Smoke suite is wired to build123d evaluator tasks.",
      state: benchmarkState,
      Icon: Gauge
    },
    {
      title: "Verified",
      detail: stepUpdateInProgress
        ? "References are updating from the latest STEP."
        : verificationState === "pass"
          ? "Ready for an agent iteration."
          : "Needs a selected, renderable artifact.",
      state: verificationState,
      Icon: BadgeCheck
    }
  ];

  const handleSubmitPrompt = (event) => {
    event.preventDefault();
    const nextPrompt = draft.trim();
    if (!nextPrompt) {
      return;
    }
    setLastPrompt(nextPrompt);
    setDraft("");
  };

  const copyBenchmarkCommand = async () => {
    if (typeof navigator === "undefined" || !navigator.clipboard?.writeText) {
      return;
    }
    await navigator.clipboard.writeText(benchmarkCommand);
    setCommandCopied(true);
  };

  return (
    <aside
      className={cn(
        "cad-glass-popover pointer-events-auto flex h-full min-h-0 flex-col overflow-hidden rounded-lg border border-sidebar-border/80 bg-popover/82 text-popover-foreground shadow-2xl shadow-black/15 backdrop-blur-xl",
        compact ? "w-full" : "w-[22rem]"
      )}
    >
      <div className="border-b border-border/70 px-3 py-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Dimension Shell
            </p>
            <h2 className="mt-1 truncate text-sm font-semibold text-foreground">Agentic CAD</h2>
          </div>
          <StatusPill state={readyState}>{selectedFormatLabel}</StatusPill>
        </div>

        <div className="mt-3 grid grid-cols-2 gap-1.5">
          {WORKFLOW_OPTIONS.map((option) => (
            <WorkflowButton
              key={option.id}
              option={option}
              active={option.id === activeWorkflowId}
              suggested={option.id === suggestedWorkflowId}
              onClick={() => setActiveWorkflowId(option.id)}
            />
          ))}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
        <section className="rounded-md border border-border/65 bg-background/35 p-3">
          <div className="flex min-w-0 items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                Active Artifact
              </p>
              <h3 className="mt-1 truncate text-sm font-semibold text-foreground" title={artifactLabel}>
                {artifactLabel}
              </h3>
            </div>
            <activeWorkflow.Icon className="mt-0.5 size-4 shrink-0 text-primary" strokeWidth={2} aria-hidden="true" />
          </div>

          <div className="mt-3 grid grid-cols-3 gap-1.5">
            <div className="rounded-md border border-border/60 bg-muted/25 px-2 py-1.5">
              <p className="text-[10px] text-muted-foreground">Assets</p>
              <p className="mt-0.5 text-xs font-semibold text-foreground">{assetCount}</p>
            </div>
            <div className="rounded-md border border-border/60 bg-muted/25 px-2 py-1.5">
              <p className="text-[10px] text-muted-foreground">Bodies</p>
              <p className="mt-0.5 text-xs font-semibold text-foreground">{meshPartCount || (hasGeometry ? 1 : 0)}</p>
            </div>
            <div className="rounded-md border border-border/60 bg-muted/25 px-2 py-1.5">
              <p className="text-[10px] text-muted-foreground">Files</p>
              <p className="mt-0.5 text-xs font-semibold text-foreground">{catalogEntries.length}</p>
            </div>
          </div>

          <p className="mt-2 truncate text-[10px] leading-4 text-muted-foreground" title={entryPath}>
            {entryPath || "Select an artifact from the tree."}
          </p>
        </section>

        <section className="mt-3">
          <div className="mb-2 flex items-center justify-between gap-2">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Validation Loop
            </p>
            <StatusPill state={verificationState}>{verificationState === "pass" ? "Ready" : "Open"}</StatusPill>
          </div>
          <div className="space-y-1.5">
            {loopRows.map((row) => (
              <LoopRow key={row.title} {...row} />
            ))}
          </div>
        </section>

        <section className="mt-3 rounded-md border border-border/65 bg-background/35 p-3">
          <div className="flex items-center justify-between gap-2">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Runner
            </p>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              title="Copy benchmark command"
              aria-label="Copy benchmark command"
              onClick={copyBenchmarkCommand}
              className="size-7"
            >
              <TerminalSquare className="size-3.5" aria-hidden="true" />
            </Button>
          </div>
          <code className="mt-2 block rounded-md border border-border/60 bg-muted/40 px-2 py-2 text-[10px] leading-4 text-muted-foreground">
            {benchmarkCommand}
          </code>
          <div className="mt-2 flex items-center justify-between gap-2">
            <span className="truncate text-[10px] text-muted-foreground">
              {commandCopied ? "Command copied" : "Smoke benchmark: 2 tasks"}
            </span>
            <StatusPill state={benchmarkState}>Harness</StatusPill>
          </div>
        </section>
      </div>

      <form onSubmit={handleSubmitPrompt} className="border-t border-border/70 p-3">
        {lastPrompt ? (
          <div className="mb-2 rounded-md border border-primary/20 bg-primary/10 px-2.5 py-2">
            <div className="flex items-center gap-2 text-[10px] font-semibold text-primary">
              <Play className="size-3.5" aria-hidden="true" />
              <span>Iteration staged</span>
            </div>
            <p className="mt-1 line-clamp-2 text-[10px] leading-4 text-muted-foreground">{lastPrompt}</p>
          </div>
        ) : null}
        <label className="sr-only" htmlFor="agentic-cad-prompt">Agent prompt</label>
        <textarea
          id="agentic-cad-prompt"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          rows={3}
          className="min-h-20 w-full resize-none rounded-md border border-border/70 bg-background/65 px-2.5 py-2 text-xs leading-5 text-foreground outline-none transition-colors placeholder:text-muted-foreground focus-visible:border-primary/50 focus-visible:ring-2 focus-visible:ring-primary/20"
          placeholder="Describe the next CAD change..."
        />
        <div className="mt-2 flex items-center justify-between gap-2">
          <span className="truncate text-[10px] text-muted-foreground">{activeWorkflow.label}</span>
          <Button type="submit" size="sm" className="h-8 gap-1.5 px-3 text-[11px]">
            <Send className="size-3.5" aria-hidden="true" />
            Run
          </Button>
        </div>
      </form>
    </aside>
  );
}
