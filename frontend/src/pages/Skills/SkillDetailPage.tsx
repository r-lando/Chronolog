import { Link, useParams } from "react-router-dom";
import { useSkill } from "../../hooks/useSkills";
import { StatusBadge, DifficultyBadge } from "../../components/ui/Badge";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { ApiError } from "../../api/client";

export function SkillDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: skill, isLoading, error } = useSkill(id);

  if (isLoading) return <LoadingState label="Loading skill..." />;
  if (error || !skill) {
    return <ErrorState message={error instanceof ApiError ? error.message : "Skill not found."} />;
  }

  return (
    <div className="max-w-3xl">
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-bold text-slate-100">{skill.name}</h1>
          {skill.category && (
            <span className="text-xs bg-surface-700 text-slate-400 px-1.5 py-0.5 rounded">{skill.category}</span>
          )}
        </div>
        {skill.description && <p className="text-slate-500 text-sm mt-1">{skill.description}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="card p-5">
          <p className="text-3xl font-bold text-accent-400">{skill.lab_count}</p>
          <p className="text-sm text-slate-500 mt-1">Labs practiced in</p>
        </div>
        <div className="card p-5">
          <p className="text-lg font-semibold text-slate-200">
            {skill.last_practiced ? new Date(skill.last_practiced).toLocaleDateString() : "—"}
          </p>
          <p className="text-sm text-slate-500 mt-1">Last practiced</p>
        </div>
      </div>

      {skill.related_tools.length > 0 && (
        <div className="card p-6 mb-6">
          <h2 className="text-sm font-semibold text-slate-300 mb-3">Related tools</h2>
          <div className="flex flex-wrap gap-2">
            {skill.related_tools.map((tool) => (
              <span key={tool.id} className="text-xs bg-surface-700 text-slate-300 px-2 py-1 rounded">
                {tool.name}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="card p-6">
        <h2 className="text-sm font-semibold text-slate-300 mb-3">Related labs</h2>
        {skill.related_labs.length === 0 ? (
          <p className="text-slate-500 text-sm">No labs practice this skill yet.</p>
        ) : (
          <div className="space-y-2">
            {skill.related_labs.map((lab) => (
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
