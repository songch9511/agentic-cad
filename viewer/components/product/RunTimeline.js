import { CheckCircle2, Circle, Clock, XCircle } from "lucide-react";

const STATUS_META = {
  idle: { label: "Idle", icon: Circle, className: "text-neutral-400" },
  queued: { label: "Queued", icon: Clock, className: "text-neutral-500" },
  running: { label: "Running", icon: Clock, className: "text-blue-600" },
  succeeded: { label: "Succeeded", icon: CheckCircle2, className: "text-green-600" },
  failed: { label: "Failed", icon: XCircle, className: "text-red-600" },
};

function statusMeta(status) {
  return STATUS_META[status] || STATUS_META.idle;
}

export default function RunTimeline({ run = null }) {
  if (!run) {
    return (
      <section className="rounded-xl border border-neutral-200 bg-white p-4">
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-neutral-400">Activity</p>
        <p className="mt-3 text-sm text-neutral-500">Create or select a run to see its timeline.</p>
      </section>
    );
  }

  const runStatus = statusMeta(run.status);

  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-neutral-400">Activity</p>
          <h2 className="mt-1 truncate text-sm font-semibold text-neutral-900">{run.uploadedFiles?.[0]?.name || run.id}</h2>
        </div>
        <span className="rounded-md border border-neutral-200 bg-neutral-50 px-2 py-1 text-xs font-medium capitalize text-neutral-600">
          {runStatus.label}
        </span>
      </div>

      <div className="mt-4 space-y-4">
        {(run.steps || []).map((step) => {
          const meta = statusMeta(step.status);
          const Icon = meta.icon;
          return (
            <div key={step.id} className="flex gap-3">
              <div className={`mt-0.5 ${meta.className}`}>
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-neutral-900">{step.label}</p>
                  <span className="text-xs capitalize text-neutral-400">{meta.label}</span>
                </div>
                {step.detail ? <p className="mt-1 text-xs leading-5 text-neutral-500">{step.detail}</p> : null}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
