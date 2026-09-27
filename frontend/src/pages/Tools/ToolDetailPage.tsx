import { Link, useParams } from "react-router-dom";
import { useTool } from "../../hooks/useTools";
import { StatusBadge, DifficultyBadge } from "../../components/ui/Badge";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { ApiError } from "../../api/client";

export function ToolDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: tool, isLoading, error } = useTool(id);

  if (isLoading) return <LoadingState label="Loading tool..." />;
  if (error || !tool) {
    return <ErrorState message={error instanceof ApiError ? error.message : "Tool not found."} />;
  }

  return (
    <div className="max-w-3xl">
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-bold text-slate-100">{tool.name}</h1>
          {tool.category && (
            <span className="text-xs bg-surface-700 text-slate-400 px-1.5 py-0.5 rounded">{tool.category}</span>
          )}
        </div>
        {tool.description && <p className="text-slate-500 text-sm mt-1">{tool.description}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="card p-5">
          <p className="text-3xl font-bold text-accent-400">{tool.lab_count}</p>
          <p className="text-sm text-slate-500 mt-1">Labs used in</p>
        </div>
        <div className="card p-5">
          <p className="text-lg font-semibold text-slate-200">
            {tool.last_used ? new Date(tool.last_used).toLocaleDateString() : "—"}
          </p>
          <p className="text-sm text-slate-500 mt-1">Last used</p>
        </div>
      </div>

      {tool.related_skills.length > 0 && (
        <div className="card p-6 mb-6">
          <h2 className="text-sm font-semibold text-slate-300 mb-3">Related skills</h2>
          <div className="flex flex-wrap gap-2">
            {tool.related_skills.map((skill) => (
              <span key={skill.id} className="text-xs bg-surface-700 text-slate-300 px-2 py-1 rounded">
                {skill.name}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="card p-6">
        <h2 className="text-sm font-semibold text-slate-300 mb-3">Related labs</h2>
        {tool.related_labs.length === 0 ? (
          <p className="text-slate-500 text-sm">No labs use this tool yet.</p>
        ) : (
          <div className="space-y-2">
            {tool.related_labs.map((lab) => (
              <Link
                key={lab.id}
                to={`/labs/${lab.id}`}
                className="flex items-center justify-between bg-surface-800 border border-surface-700 rounded-md px-4 py-2 hover:border-accent-500/50 transition-colors"
              >
                <span className="text-slate-200 text-sm font-medium">{lab.title}</span>
                <div className="flex items-center gap-2">
                  <DifficultyBadge difficulty={lab.difficulty} />
                  <StatusBadge status={lab.status} />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
