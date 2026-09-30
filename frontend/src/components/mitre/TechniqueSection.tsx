import { useState, type FormEvent } from "react";
import { useMitreTechniques } from "../../hooks/useMitre";
import type { LabTechnique } from "../../types/mitre";
import { Button } from "../ui/Button";
import { AlertBanner } from "../ui/AlertBanner";
import { ApiError } from "../../api/client";

const MIN_JUSTIFICATION_LENGTH = 10;

interface TechniqueSectionProps {
  attached: LabTechnique[];
  onAdd: (techniqueId: string, justification: string) => Promise<unknown>;
  onRemove: (techniqueId: string) => void;
  isAdding: boolean;
}

/**
 * Shared by the Lab and CTF challenge detail pages. The parent supplies
 * the add/remove behavior (each calls its own API endpoints), so this
 * component only owns the form UI and the client-side justification check.
 * The server independently enforces the same minimum length and rejects
 * technique ids that aren't in the seeded reference list.
 */
export function TechniqueSection({ attached, onAdd, onRemove, isAdding }: TechniqueSectionProps) {
  const { data: allTechniques } = useMitreTechniques();

  const [techniqueId, setTechniqueId] = useState("");
  const [justification, setJustification] = useState("");
  const [error, setError] = useState<string | null>(null);

  const attachedIds = new Set(attached.map((lt) => lt.technique.id));
  const availableTechniques = (allTechniques ?? []).filter((t) => !attachedIds.has(t.id));

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!techniqueId) {
      setError("Choose a technique.");
      return;
    }
    if (justification.trim().length < MIN_JUSTIFICATION_LENGTH) {
      setError(
        `Justification must be at least ${MIN_JUSTIFICATION_LENGTH} characters — explain why this technique applies.`
      );
      return;
    }
    try {
      await onAdd(techniqueId, justification.trim());
      setTechniqueId("");
      setJustification("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to attach this technique.");
    }
  }

  return (
    <div>
      <div className="space-y-2 mb-4">
        {attached.length === 0 && <p className="text-slate-500 text-sm">No MITRE ATT&CK techniques mapped yet.</p>}
        {attached.map((lt) => (
          <div key={lt.technique.id} className="bg-surface-800 border border-surface-700 rounded-md px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-slate-500">
                  {lt.technique.sub_technique_id ?? lt.technique.technique_id}
                </span>
                <span className="text-sm font-medium text-slate-200">{lt.technique.name}</span>
                <span className="text-xs bg-surface-700 text-slate-400 px-1.5 py-0.5 rounded">
                  {lt.technique.tactic}
                </span>
              </div>
              <button
                onClick={() => onRemove(lt.technique.id)}
                className="text-slate-500 hover:text-status-danger text-sm"
              >
                Remove
              </button>
            </div>
            <p className="text-xs text-slate-500 mt-1.5">{lt.justification}</p>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-2">
        {error && <AlertBanner message={error} />}
        <div className="flex gap-2">
          <select className="input-field" value={techniqueId} onChange={(e) => setTechniqueId(e.target.value)}>
            <option value="">Select a technique...</option>
            {availableTechniques.map((technique) => (
              <option key={technique.id} value={technique.id}>
                {technique.sub_technique_id ?? technique.technique_id} — {technique.name}
              </option>
            ))}
          </select>
          <Button type="submit" disabled={isAdding}>
            {isAdding ? "Saving..." : "Add"}
          </Button>
        </div>
        <textarea
          className="input-field text-sm min-h-[70px]"
          placeholder="Why does this technique apply? e.g. 'Observed repeated failed logons (Event ID 4625) in the log data.'"
          value={justification}
          onChange={(e) => setJustification(e.target.value)}
        />
      </form>
    </div>
  );
}
