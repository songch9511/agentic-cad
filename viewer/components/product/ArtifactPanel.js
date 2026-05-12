import { Box, FileCode2, FileText, Layers3, ScrollText } from "lucide-react";

const ARTIFACT_OPTIONS = [
  { key: "step", label: "STEP", icon: FileCode2 },
  { key: "glb", label: "GLB", icon: Box },
  { key: "topology", label: "Topology", icon: Layers3 },
  { key: "source", label: "Source", icon: FileText },
  { key: "report", label: "Report", icon: ScrollText },
];

function artifactDescription(key, artifact) {
  if (!artifact) {
    if (key === "glb") {
      return "Conversion not connected yet";
    }
    return "Not available";
  }
  return artifact.path || artifact.url || artifact.fileName || artifact.note || "Available";
}

export default function ArtifactPanel({ run = null, selectedArtifactKey = "", onSelectArtifact }) {
  if (!run) {
    return (
      <section className="rounded-xl border border-neutral-200 bg-white p-4">
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-neutral-400">Artifacts</p>
        <p className="mt-3 text-sm text-neutral-500">Run artifacts will appear here.</p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4">
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-neutral-400">Artifacts</p>
      <div className="mt-3 space-y-2">
        {ARTIFACT_OPTIONS.map((option) => {
          const artifact = run.artifacts?.[option.key] || null;
          const Icon = option.icon;
          const isSelected = selectedArtifactKey === option.key;
          const isAvailable = Boolean(artifact);
          return (
            <button
              key={option.key}
              type="button"
              className={isSelected
                ? "w-full rounded-lg border border-neutral-900 bg-neutral-900 px-3 py-2 text-left text-white"
                : "w-full rounded-lg border border-neutral-200 bg-white px-3 py-2 text-left hover:border-neutral-300 hover:bg-neutral-50"}
              onClick={() => onSelectArtifact?.(option.key)}
              disabled={!isAvailable}
            >
              <span className="flex items-center gap-2">
                <Icon className="h-4 w-4 shrink-0" />
                <span className="text-sm font-medium">{option.label}</span>
                <span className={isSelected
                  ? "ml-auto text-xs text-neutral-300"
                  : isAvailable ? "ml-auto text-xs text-green-600" : "ml-auto text-xs text-neutral-400"}
                >
                  {isAvailable ? "Available" : "Waiting"}
                </span>
              </span>
              <span className={isSelected
                ? "mt-1 block truncate text-xs text-neutral-300"
                : "mt-1 block truncate text-xs text-neutral-500"}
              >
                {artifactDescription(option.key, artifact)}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
