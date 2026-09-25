import type { ReactNode } from "react";

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="card p-10 text-center">
      <h3 className="text-slate-200 font-semibold">{title}</h3>
      <p className="text-slate-500 text-sm mt-1 max-w-md mx-auto">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
