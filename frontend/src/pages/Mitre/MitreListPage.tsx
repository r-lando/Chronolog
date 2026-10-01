import { Link } from "react-router-dom";
import { useMitreTechniques } from "../../hooks/useMitre";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { ApiError } from "../../api/client";
import type { MitreTechniqueWithStats } from "../../types/mitre";

function groupByTactic(techniques: MitreTechniqueWithStats[]): Record<string, MitreTechniqueWithStats[]> {
  return techniques.reduce<Record<string, MitreTechniqueWithStats[]>>((groups, technique) => {
    (groups[technique.tactic] ??= []).push(technique);
    return groups;
  }, {});
}

export function MitreListPage() {
  const { data: techniques, isLoading, error } = useMitreTechniques();

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">MITRE ATT&CK</h1>
        <p className="text-slate-500 text-sm mt-1">
          Techniques you've mapped to your labs, grouped by tactic. Practiced techniques show how many
          labs and when — click any technique to see the labs and your justification.
        </p>
      </div>

      {isLoading && <LoadingState label="Loading techniques..." />}
      {error && (
        <ErrorState message={error instanceof ApiError ? error.message : "Failed to load MITRE techniques."} />
      )}

      {techniques && (
        <div className="space-y-6">
          {Object.entries(groupByTactic(techniques)).map(([tactic, group]) => (
            <div key={tactic}>
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-2">{tactic}</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {group.map((technique) => (
                  <Link
                    key={technique.id}
                    to={`/mitre/${technique.id}`}
                    className={`card p-4 hover:border-accent-500/50 transition-colors ${
                      technique.lab_count > 0 ? "" : "opacity-60"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono text-slate-500">
                        {technique.sub_technique_id ?? technique.technique_id}
                      </span>
                      {technique.lab_count > 0 && (
                        <span className="text-xs bg-accent-500/15 text-accent-400 px-1.5 py-0.5 rounded">
                          {technique.lab_count} {technique.lab_count === 1 ? "lab" : "labs"}
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium text-slate-200 mt-1">{technique.name}</p>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
