import { Link } from "react-router-dom";
import { useSkills } from "../../hooks/useSkills";
import { EmptyState } from "../../components/ui/EmptyState";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { ApiError } from "../../api/client";

export function SkillsListPage() {
  const { data: skills, isLoading, error } = useSkills();

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Skills</h1>
        <p className="text-slate-500 text-sm mt-1">
          Measurable, activity-based tracking — not a self-reported proficiency score.
        </p>
      </div>

      {isLoading && <LoadingState label="Loading skills..." />}
      {error && <ErrorState message={error instanceof ApiError ? error.message : "Failed to load skills."} />}

      {skills && skills.length === 0 && (
        <EmptyState
          title="No skills tracked yet"
          description="Attach a skill to a lab from its detail page to start building this list."
        />
      )}

      {skills && skills.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {skills.map((skill) => (
            <Link
              key={skill.id}
              to={`/skills/${skill.id}`}
              className="card p-5 hover:border-accent-500/50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <h3 className="font-semibold text-slate-100">{skill.name}</h3>
                {skill.category && (
                  <span className="text-xs bg-surface-700 text-slate-400 px-1.5 py-0.5 rounded shrink-0 ml-2">
                    {skill.category}
                  </span>
                )}
              </div>
              <div className="mt-3 flex items-baseline gap-1.5">
                <span className="text-2xl font-bold text-accent-400">{skill.lab_count}</span>
                <span className="text-sm text-slate-500">{skill.lab_count === 1 ? "lab" : "labs"}</span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                {skill.last_practiced
                  ? `Last practiced ${new Date(skill.last_practiced).toLocaleDateString()}`
                  : "Not yet practiced"}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
