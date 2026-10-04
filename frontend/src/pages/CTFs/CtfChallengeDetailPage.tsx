import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  useAddCtfSkill,
  useAddCtfTechnique,
  useAddCtfTool,
  useCtfChallenge,
  useCtfEvent,
  useCtfOptions,
  useDeleteCtfChallenge,
  useRemoveCtfSkill,
  useRemoveCtfTechnique,
  useRemoveCtfTool,
  useUpdateCtfChallenge,
} from "../../hooks/useCtf";
import { Button } from "../../components/ui/Button";
import { FormField } from "../../components/ui/FormField";
import { SelectField } from "../../components/ui/SelectField";
import { MarkdownEditor } from "../../components/ui/MarkdownEditor";
import { CtfStatusBadge, DifficultyBadge } from "../../components/ui/Badge";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { TechniqueSection } from "../../components/mitre/TechniqueSection";
import { CtfEvidenceSection } from "../../components/ctf/CtfEvidenceSection";
import { ApiError } from "../../api/client";
import type { CtfChallengeFormValues } from "../../types/ctf";

export function CtfChallengeDetailPage() {
  const { challengeId } = useParams<{ challengeId: string }>();
  const navigate = useNavigate();
  const id = challengeId ?? "";

  const { data: challenge, isLoading, error } = useCtfChallenge(challengeId);
  const { data: parentEvent } = useCtfEvent(challenge?.ctf_event_id);
  const { data: options } = useCtfOptions();

  const updateChallenge = useUpdateCtfChallenge(id);
  const deleteChallenge = useDeleteCtfChallenge();
  const addSkill = useAddCtfSkill(id);
  const removeSkill = useRemoveCtfSkill(id);
  const addTool = useAddCtfTool(id);
  const removeTool = useRemoveCtfTool(id);
  const addTechnique = useAddCtfTechnique(id);
  const removeTechnique = useRemoveCtfTechnique(id);

  const [form, setForm] = useState<CtfChallengeFormValues | null>(null);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [newSkill, setNewSkill] = useState("");
  const [newTool, setNewTool] = useState("");

  useEffect(() => {
    if (challenge) {
      setForm({
        title: challenge.title,
        category: challenge.category,
        difficulty: challenge.difficulty,
        status: challenge.status,
        time_spent_minutes: challenge.time_spent_minutes?.toString() ?? "",
        description: challenge.description ?? "",
        solution_writeup: challenge.solution_writeup ?? "",
        lessons_learned: challenge.lessons_learned ?? "",
      });
    }
  }, [challenge]);

  if (isLoading || (challenge && !form)) return <LoadingState label="Loading challenge..." />;
  if (error || !challenge || !form) {
    return <ErrorState message={error instanceof ApiError ? error.message : "Challenge not found."} />;
  }

  function updateField<K extends keyof CtfChallengeFormValues>(key: K, value: CtfChallengeFormValues[K]) {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  async function handleSave() {
    if (!form) return;
    setSaveState("saving");
    setSaveError(null);
    try {
      await updateChallenge.mutateAsync({
        title: form.title,
        category: form.category,
        difficulty: form.difficulty,
        status: form.status,
        time_spent_minutes: form.time_spent_minutes ? Number(form.time_spent_minutes) : null,
        description: form.description || null,
        solution_writeup: form.solution_writeup || null,
        lessons_learned: form.lessons_learned || null,
      });
      setSaveState("saved");
      setTimeout(() => setSaveState("idle"), 2000);
    } catch (err) {
      setSaveState("error");
      setSaveError(err instanceof ApiError ? err.message : "Save failed.");
    }
  }

  async function handleDelete() {
    if (!window.confirm("Delete this challenge and its evidence permanently?")) return;
    await deleteChallenge.mutateAsync(id);
    navigate(`/ctfs/${challenge?.ctf_event_id ?? ""}`);
  }

  return (
    <div className="max-w-4xl">
      <div className="flex items-start justify-between mb-6">
        <div>
          <Link to={`/ctfs/${challenge.ctf_event_id}`} className="text-xs text-slate-500 hover:text-accent-400">
            ← {parentEvent?.name ?? "Back to event"}
          </Link>
          <h1 className="text-2xl font-bold text-slate-100 mt-1">{challenge.title}</h1>
          <div className="flex items-center gap-2 mt-2">
            <DifficultyBadge difficulty={challenge.difficulty} />
            <CtfStatusBadge status={challenge.status} />
            <span className="text-slate-500 text-sm">{challenge.category}</span>
          </div>
        </div>
        <Button variant="secondary" onClick={handleDelete}>
          Delete
        </Button>
      </div>

      {/* Details + write-up (saved together) */}
      <div className="card p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-100">Details & write-up</h2>
          <div className="flex items-center gap-3">
            {saveState === "saved" && <span className="text-xs text-status-success">Saved</span>}
            {saveState === "error" && <span className="text-xs text-status-danger">{saveError}</span>}
            <Button onClick={handleSave} disabled={saveState === "saving"}>
              {saveState === "saving" ? "Saving..." : "Save changes"}
            </Button>
          </div>
        </div>

        <div className="space-y-4">
          <FormField
            id="challenge-title-edit"
            label="Challenge name"
            value={form.title}
            onChange={(e) => updateField("title", e.target.value)}
          />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <SelectField
              id="challenge-category-edit"
              label="Category"
              options={options?.categories ?? []}
              value={form.category}
              onChange={(e) => updateField("category", e.target.value)}
            />
            <SelectField
              id="challenge-difficulty-edit"
              label="Difficulty"
              options={options?.difficulties ?? []}
              value={form.difficulty}
              onChange={(e) => updateField("difficulty", e.target.value)}
            />
            <SelectField
              id="challenge-status-edit"
              label="Status"
              options={options?.statuses ?? []}
              value={form.status}
              onChange={(e) => updateField("status", e.target.value)}
            />
            <FormField
              id="challenge-time-edit"
              label="Time spent (min)"
              type="number"
              min={0}
              value={form.time_spent_minutes}
              onChange={(e) => updateField("time_spent_minutes", e.target.value)}
            />
          </div>

          <MarkdownEditor
            label="Challenge description"
            value={form.description}
            onChange={(v) => updateField("description", v)}
            placeholder="What was the challenge asking?"
            minRows={3}
          />
          <MarkdownEditor
            label="Solution / write-up"
            value={form.solution_writeup}
            onChange={(v) => updateField("solution_writeup", v)}
            placeholder="Your own approach and steps. TALA never provides or generates solutions — this is your record."
            minRows={6}
          />
          <MarkdownEditor
            label="Lessons learned"
            value={form.lessons_learned}
            onChange={(v) => updateField("lessons_learned", v)}
            placeholder="What concepts did this challenge teach you?"
            minRows={3}
          />
        </div>
      </div>

      {/* Skills */}
      <div className="card p-4 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-2">Skills</h3>
        <div className="flex flex-wrap items-center gap-2">
          {challenge.skills.map((skill) => (
            <span
              key={skill.id}
              className="inline-flex items-center gap-1 bg-surface-700 text-slate-300 text-xs px-2 py-1 rounded"
            >
              {skill.name}
              <button
                onClick={() => removeSkill.mutate(skill.id)}
                className="text-slate-500 hover:text-status-danger"
                aria-label={`Remove skill ${skill.name}`}
              >
                ×
              </button>
            </span>
          ))}
          <input
            className="input-field max-w-[160px] text-xs py-1"
            placeholder="Add skill..."
            value={newSkill}
            onChange={(e) => setNewSkill(e.target.value)}
            onKeyDown={async (e) => {
              if (e.key === "Enter" && newSkill.trim()) {
                e.preventDefault();
                await addSkill.mutateAsync(newSkill.trim());
                setNewSkill("");
              }
            }}
          />
        </div>
      </div>

      {/* Tools */}
      <div className="card p-4 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-2">Tools</h3>
        <div className="flex flex-wrap items-center gap-2">
          {challenge.tools.map((tool) => (
            <span
              key={tool.id}
              className="inline-flex items-center gap-1 bg-surface-700 text-slate-300 text-xs px-2 py-1 rounded"
            >
              {tool.name}
              <button
                onClick={() => removeTool.mutate(tool.id)}
                className="text-slate-500 hover:text-status-danger"
                aria-label={`Remove tool ${tool.name}`}
              >
                ×
              </button>
            </span>
          ))}
          <input
            className="input-field max-w-[160px] text-xs py-1"
            placeholder="Add tool..."
            value={newTool}
            onChange={(e) => setNewTool(e.target.value)}
            onKeyDown={async (e) => {
              if (e.key === "Enter" && newTool.trim()) {
                e.preventDefault();
                await addTool.mutateAsync(newTool.trim());
                setNewTool("");
              }
            }}
          />
        </div>
      </div>

      {/* MITRE ATT&CK */}
      <div className="card p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">MITRE ATT&CK Techniques</h2>
        <TechniqueSection
          attached={challenge.techniques}
          onAdd={(techniqueId, justification) => addTechnique.mutateAsync({ techniqueId, justification })}
          onRemove={(techniqueId) => removeTechnique.mutate(techniqueId)}
          isAdding={addTechnique.isPending}
        />
      </div>

      {/* Evidence */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">Evidence</h2>
        <CtfEvidenceSection challengeId={challenge.id} />
      </div>
    </div>
  );
}
