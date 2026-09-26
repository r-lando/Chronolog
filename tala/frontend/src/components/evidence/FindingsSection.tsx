import { useState, type FormEvent } from "react";
import { useCreateFinding, useDeleteFinding, useLabFindings } from "../../hooks/useEvidence";
import { Button } from "../ui/Button";
import { LoadingState } from "../ui/StatusStates";

const SEVERITY_STYLES: Record<string, string> = {
  Info: "bg-status-neutral/15 text-slate-400",
  Low: "bg-status-info/15 text-status-info",
  Medium: "bg-status-warning/15 text-status-warning",
  High: "bg-status-danger/15 text-status-danger",
};

export function FindingsSection({ labId }: { labId: string }) {
  const { data: findings, isLoading } = useLabFindings(labId);
  const createFinding = useCreateFinding(labId);
  const deleteFinding = useDeleteFinding(labId);

  const [title, setTitle] = useState("");
  const [severity, setSeverity] = useState("");

  async function handleAdd(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    await createFinding.mutateAsync({ title: title.trim(), severity: severity || undefined });
    setTitle("");
    setSeverity("");
  }

  if (isLoading) return <LoadingState label="Loading findings..." />;

  return (
    <div>
      <div className="space-y-2 mb-4">
        {findings && findings.length === 0 && (
          <p className="text-slate-500 text-sm">No structured findings recorded yet.</p>
        )}
        {findings?.map((finding) => (
          <div
            key={finding.id}
            className="flex items-center justify-between bg-surface-800 border border-surface-700 rounded-md px-4 py-2"
          >
            <div>
              <div className="flex items-center gap-2">
                <span className="text-slate-200 text-sm font-medium">{finding.title}</span>
                {finding.severity && (
                  <span className={`text-xs px-1.5 py-0.5 rounded ${SEVERITY_STYLES[finding.severity]}`}>
                    {finding.severity}
                  </span>
                )}
              </div>
              {finding.description && <p className="text-xs text-slate-500 mt-0.5">{finding.description}</p>}
            </div>
            <button
              onClick={() => deleteFinding.mutate(finding.id)}
              className="text-slate-500 hover:text-status-danger text-sm"
            >
              Delete
            </button>
          </div>
        ))}
      </div>

      <form onSubmit={handleAdd} className="flex gap-2">
        <input
          className="input-field"
          placeholder="Add a finding..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <select className="input-field max-w-[120px]" value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="">Severity</option>
          <option value="Info">Info</option>
          <option value="Low">Low</option>
          <option value="Medium">Medium</option>
          <option value="High">High</option>
        </select>
        <Button type="submit" disabled={createFinding.isPending}>
          Add
        </Button>
      </form>
    </div>
  );
}
