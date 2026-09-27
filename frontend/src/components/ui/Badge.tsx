import clsx from "clsx";

const STATUS_STYLES: Record<string, string> = {
  Planned: "bg-status-neutral/15 text-slate-400",
  "In Progress": "bg-status-info/15 text-status-info",
  Completed: "bg-status-success/15 text-status-success",
  Paused: "bg-status-warning/15 text-status-warning",
  Archived: "bg-surface-700 text-slate-500",
};

const DIFFICULTY_STYLES: Record<string, string> = {
  Beginner: "bg-status-success/15 text-status-success",
  Easy: "bg-status-info/15 text-status-info",
  Medium: "bg-status-warning/15 text-status-warning",
  Hard: "bg-status-danger/15 text-status-danger",
  Expert: "bg-status-danger/25 text-status-danger",
};

function Badge({ label, className }: { label: string; className: string }) {
  return (
    <span className={clsx("inline-block px-2 py-0.5 rounded text-xs font-medium", className)}>
      {label}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  return <Badge label={status} className={STATUS_STYLES[status] ?? "bg-surface-700 text-slate-400"} />;
}

export function DifficultyBadge({ difficulty }: { difficulty: string }) {
  return (
    <Badge label={difficulty} className={DIFFICULTY_STYLES[difficulty] ?? "bg-surface-700 text-slate-400"} />
  );
}
