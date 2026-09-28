import { Link, useParams } from "react-router-dom";
import { useMitreTechnique } from "../../hooks/useMitre";
import { StatusBadge, DifficultyBadge } from "../../components/ui/Badge";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { ApiError } from "../../api/client";

export function MitreDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: technique, isLoading, error } = useMitreTechnique(id);

  if (isLoading) return <LoadingState label="Loading technique..." />;
  if (error || !technique) {
    return <ErrorState message={error instanceof ApiError ? error.message : "Technique not found."} />;
  }

  return (
    <div className="max-w-3xl">
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <span className="text-sm font-mono text-slate-500">
            {technique.sub_technique_id ?? technique.technique_id}
          </span>
          <span className="text-xs bg-surface-700 text-slate-400 px-1.5 py-0.5 rounded">{technique.tactic}</span>
        </div>
        <h1 className="text-2xl font-bold text-slate-100 mt-1">{technique.name}</h1>
        {technique.description && <p className="text-slate-500 text-sm mt-2">{technique.description}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="card p-5">
          <p className="text-3xl font-bold text-accent-400">{technique.lab_count}</p>
          <p className="text-sm text-slate-500 mt-1">Labs practiced in</p>
        </div>
        <div className="card p-5">
          <p className="text-lg font-semibold text-slate-200">
            {technique.last_practiced ? new Date(technique.last_practiced).toLocaleDateString() : "—"}
          </p>
          <p className="text-sm text-slate-500 mt-1">Last practiced</p>
        </div>
      </div>

      <div className="card p-6">
        <h2 className="text-sm font-semibold text-slate-300 mb-3">Labs and justification</h2>
        {technique.related_labs.length === 0 ? (
          <p className="text-slate-500 text-sm">
            This technique hasn't been mapped to any of your labs yet.
          </p>
        ) : (
          <div className="space-y-3">
            {technique.related_labs.map(({ lab, justification }) => (
              <div key={lab.id} className="bg-surface-800 border border-surface-700 rounded-md px-4 py-3">
                <div className="flex items-center justify-between">
                  <Link to={`/labs/${lab.id}`} className="text-slate-200 text-sm font-medium hover:text-accent-400">
                    {lab.title}
                  </Link>
                  <div className="flex items-center gap-2">
                    <DifficultyBadge difficulty={lab.difficulty} />
                    <StatusBadge status={lab.status} />
                  </div>
                </div>
                <p className="text-xs text-slate-500 mt-1.5">{justification}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
