import { useRef, useState } from "react";
import { AlertCircle, ArrowRight, FileUp, UploadCloud, X } from "lucide-react";
import { DIMENSION_RUN_MODES, isStepFile } from "./useDimensionRuns";

const MODE_OPTIONS = [
  { id: DIMENSION_RUN_MODES.TEXT_TO_CAD, label: "Text to CAD" },
  { id: DIMENSION_RUN_MODES.DRAWING_TO_CAD, label: "Drawing to CAD" },
  { id: DIMENSION_RUN_MODES.VALIDATE, label: "Validate" },
  { id: DIMENSION_RUN_MODES.BATCH, label: "Batch" },
];

function formatFileSize(size) {
  const bytes = Number(size || 0);
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

export default function DimensionComposer({
  compact = false,
  onCreateRun,
  sampleEntries = [],
  onCreateSampleRun,
}) {
  const fileInputRef = useRef(null);
  const [mode, setMode] = useState(DIMENSION_RUN_MODES.TEXT_TO_CAD);
  const [prompt, setPrompt] = useState("");
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");

  function chooseFile(nextFile) {
    setError("");
    if (!nextFile) {
      setFile(null);
      return;
    }
    if (!isStepFile(nextFile)) {
      setFile(null);
      setError("Upload a STEP or STP file. PDF and drawing conversion are not connected yet.");
      return;
    }
    setFile(nextFile);
  }

  function handleSubmit(event) {
    event.preventDefault();
    setError("");
    try {
      onCreateRun?.({ file, prompt, mode });
      setPrompt("");
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (submitError) {
      setError(submitError?.message || "Could not start a Dimension run.");
    }
  }

  return (
    <form
      className={compact
        ? "rounded-xl border border-neutral-200 bg-white p-4 shadow-[0_18px_40px_-34px_rgba(0,0,0,0.35)]"
        : "mx-auto w-full max-w-3xl rounded-2xl border border-neutral-200 bg-white p-5 shadow-[0_24px_70px_-54px_rgba(0,0,0,0.45)]"}
      onSubmit={handleSubmit}
    >
      <div className="mb-4 flex flex-wrap gap-2">
        {MODE_OPTIONS.map((option) => {
          const active = option.id === mode;
          return (
            <button
              key={option.id}
              type="button"
              className={active
                ? "rounded-md border border-neutral-900 bg-neutral-900 px-3 py-1.5 text-xs font-medium text-white"
                : "rounded-md border border-neutral-200 bg-white px-3 py-1.5 text-xs font-medium text-neutral-500 hover:border-neutral-300 hover:text-neutral-900"}
              onClick={() => setMode(option.id)}
            >
              {option.label}
            </button>
          );
        })}
      </div>

      <label className="block text-sm font-medium text-neutral-900" htmlFor="dimension-prompt">
        Describe the CAD work
      </label>
      <textarea
        id="dimension-prompt"
        className="mt-2 min-h-24 w-full resize-none rounded-xl border border-neutral-200 bg-neutral-50 px-4 py-3 text-sm leading-6 text-neutral-900 outline-none transition focus:border-neutral-400 focus:bg-white"
        placeholder="Add a note for this run. Backend generation is not connected yet."
        value={prompt}
        onChange={(event) => setPrompt(event.target.value)}
      />

      <div className="mt-4 rounded-xl border border-dashed border-neutral-300 bg-neutral-50 p-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-neutral-200 bg-white text-neutral-500">
              <UploadCloud className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-neutral-900">Upload STEP/STP</p>
              <p className="text-xs text-neutral-500">Creates a local run and waits for a real CAD viewer artifact.</p>
            </div>
          </div>
          <input
            ref={fileInputRef}
            className="hidden"
            type="file"
            accept=".step,.stp"
            onChange={(event) => chooseFile(event.target.files?.[0] || null)}
          />
          <button
            type="button"
            className="inline-flex items-center justify-center gap-2 rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm font-medium text-neutral-700 hover:border-neutral-400 hover:text-neutral-950"
            onClick={() => fileInputRef.current?.click()}
          >
            <FileUp className="h-4 w-4" />
            Choose file
          </button>
        </div>
        {file ? (
          <div className="mt-3 flex items-center justify-between rounded-lg border border-neutral-200 bg-white px-3 py-2 text-sm">
            <span className="min-w-0 truncate text-neutral-900">{file.name}</span>
            <span className="mx-3 shrink-0 text-xs text-neutral-400">{formatFileSize(file.size)}</span>
            <button
              type="button"
              className="shrink-0 rounded p-1 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-700"
              aria-label="Remove selected file"
              onClick={() => chooseFile(null)}
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : null}
      </div>

      {sampleEntries.length ? (
        <div className="mt-4 rounded-xl border border-neutral-200 bg-white p-3">
          <p className="mb-2 text-xs font-medium uppercase tracking-[0.16em] text-neutral-400">Local artifacts</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {sampleEntries.slice(0, 4).map((entry) => (
              <button
                key={entry.file || entry.name}
                type="button"
                className="min-w-0 rounded-lg border border-neutral-200 px-3 py-2 text-left hover:border-neutral-400 hover:bg-neutral-50"
                onClick={() => onCreateSampleRun?.(entry)}
              >
                <span className="block truncate text-sm font-medium text-neutral-900">{entry.name || entry.file}</span>
                <span className="block truncate text-xs text-neutral-500">{entry.assets?.glb?.path || entry.assets?.glb?.url}</span>
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {error ? (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      ) : null}

      <div className="mt-4 flex items-center justify-between gap-3">
        <p className="text-xs text-neutral-500">Runs stay in local state until backend conversion is connected.</p>
        <button
          type="submit"
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-700 disabled:cursor-not-allowed disabled:bg-neutral-300"
          disabled={!file}
        >
          Create run
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </form>
  );
}
