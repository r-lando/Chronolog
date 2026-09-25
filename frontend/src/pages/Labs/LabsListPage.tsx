import { useState } from "react";
import { Link } from "react-router-dom";
import { useLabOptions, useLabs } from "../../hooks/useLabs";
import { Button } from "../../components/ui/Button";
import { StatusBadge, DifficultyBadge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { ApiError } from "../../api/client";
import type { LabFilters } from "../../types/lab";

export function LabsListPage() {
  const [filters, setFilters] = useState<LabFilters>({});
  const { data: options } = useLabOptions();
  const { data: labs, isLoading, error } = useLabs(filters);

  function updateFilter(key: keyof LabFilters, value: string) {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Labs</h1>
          <p className="text-slate-500 text-sm mt-1">
            TryHackMe/HTB labs, home labs, and security investigations you've documented.
          </p>
        </div>
        <Link to="/labs/new">
          <Button>+ New Lab</Button>
        </Link>
      </div>

      <div className="card p-4 mb-6 flex flex-wrap gap-3">
        <input
          className="input-field max-w-xs"
          placeholder="Search title or description..."
          value={filters.search ?? ""}
          onChange={(e) => updateFilter("search", e.target.value)}
        />
        <select
          className="input-field max-w-[180px]"
          value={filters.category ?? ""}
          onChange={(e) => updateFilter("category", e.target.value)}
        >
          <option value="">All categories</option>
          {options?.categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <select
          className="input-field max-w-[150px]"
          value={filters.difficulty ?? ""}
          onChange={(e) => updateFilter("difficulty", e.target.value)}
        >
          <option value="">All difficulties</option>
          {options?.difficulties.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
        <select
          className="input-field max-w-[150px]"
          value={filters.status ?? ""}
          onChange={(e) => updateFilter("status", e.target.value)}
        >
          <option value="">All statuses</option>
          {options?.statuses.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {isLoading && <LoadingState label="Loading labs..." />}
      {error && <ErrorState message={error instanceof ApiError ? error.message : "Failed to load labs."} />}

      {labs && labs.length === 0 && (
        <EmptyState
          title="No labs yet"
          description="Document your first TryHackMe, HTB, or home lab to start building your journal."
          action={
            <Link to="/labs/new">
              <Button>+ New Lab</Button>
            </Link>
          }
        />
      )}

      {labs && labs.length > 0 && (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-surface-800 text-slate-400 text-left">
              <tr>
                <th className="px-4 py-3 font-medium">Title</th>
                <th className="px-4 py-3 font-medium">Category</th>
                <th className="px-4 py-3 font-medium">Difficulty</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Platform</th>
                <th className="px-4 py-3 font-medium">Updated</th>
              </tr>
            </thead>
            <tbody>
              {labs.map((lab) => (
                <tr
                  key={lab.id}
                  className="border-t border-surface-700 hover:bg-surface-800/60 transition-colors"
                >
                  <td className="px-4 py-3">
                    <Link to={`/labs/${lab.id}`} className="text-slate-200 hover:text-accent-400 font-medium">
                      {lab.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-400">{lab.category}</td>
                  <td className="px-4 py-3">
                    <DifficultyBadge difficulty={lab.difficulty} />
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={lab.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-400">{lab.platform ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(lab.updated_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
