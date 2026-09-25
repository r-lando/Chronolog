import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  useAddTag,
  useDeleteLab,
  useLab,
  useLabOptions,
  useRemoveTag,
  useUpdateLabStatus,
  useUpdateWriteup,
} from "../../hooks/useLabs";
import { Button } from "../../components/ui/Button";
import { StatusBadge, DifficultyBadge } from "../../components/ui/Badge";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { MarkdownEditor } from "../../components/ui/MarkdownEditor";
import { ApiError } from "../../api/client";
import type { LabWriteupUpdatePayload } from "../../types/lab";

const WRITEUP_SECTIONS: { key: keyof LabWriteupUpdatePayload; label: string; placeholder: string }[] = [
  { key: "methodology", label: "Methodology", placeholder: "What steps were performed?" },
  { key: "findings", label: "Findings", placeholder: "What was discovered?" },
  {
    key: "analysis",
    label: "Analysis",
    placeholder: "Why do these findings matter from a security perspective?",
  },
  { key: "lessons_learned", label: "Lessons Learned", placeholder: "What concepts were learned?" },
  {
    key: "reflection",
    label: "Reflection",
    placeholder: "What was difficult, and what could be improved?",
  },
  { key: "next_steps", label: "Next Steps", placeholder: "What should be practiced next?" },
];

export function LabDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: lab, isLoading, error } = useLab(id);
  const { data: options } = useLabOptions();
  const updateStatus = useUpdateLabStatus(id ?? "");
  const updateWriteup = useUpdateWriteup(id ?? "");
  const deleteLab = useDeleteLab();
  const addTag = useAddTag(id ?? "");
  const removeTag = useRemoveTag(id ?? "");

  const [writeupDraft, setWriteupDraft] = useState<LabWriteupUpdatePayload>({});
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [newTag, setNewTag] = useState("");

  useEffect(() => {
    if (lab?.writeup) {
      setWriteupDraft({
        methodology: lab.writeup.methodology ?? "",
        findings: lab.writeup.findings ?? "",
        analysis: lab.writeup.analysis ?? "",
        lessons_learned: lab.writeup.lessons_learned ?? "",
        reflection: lab.writeup.reflection ?? "",
        next_steps: lab.writeup.next_steps ?? "",
      });
    }
  }, [lab?.writeup]);

  if (isLoading) return <LoadingState label="Loading lab..." />;
  if (error || !lab) {
    return (
      <ErrorState message={error instanceof ApiError ? error.message : "This lab could not be found."} />
    );
  }

  async function handleSaveWriteup() {
    setSaveState("saving");
    try {
      await updateWriteup.mutateAsync(writeupDraft);
      setSaveState("saved");
      setTimeout(() => setSaveState("idle"), 2000);
    } catch {
      setSaveState("error");
    }
  }

  async function handleDelete() {
    if (!id) return;
    if (!window.confirm("Delete this lab and its write-up permanently? This cannot be undone.")) return;
    await deleteLab.mutateAsync(id);
    navigate("/labs");
  }

  async function handleAddTag() {
    if (!newTag.trim()) return;
    await addTag.mutateAsync(newTag.trim());
    setNewTag("");
  }

  return (
    <div className="max-w-4xl">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">{lab.title}</h1>
          <div className="flex items-center gap-2 mt-2">
            <DifficultyBadge difficulty={lab.difficulty} />
            <StatusBadge status={lab.status} />
            <span className="text-slate-500 text-sm">{lab.category}</span>
            {lab.platform && <span className="text-slate-500 text-sm">· {lab.platform}</span>}
          </div>
        </div>
        <div className="flex gap-2">
          <Link to={`/labs/${lab.id}/edit`}>
            <Button variant="secondary">Edit</Button>
          </Link>
          <Button variant="secondary" onClick={handleDelete}>
            Delete
          </Button>
        </div>
      </div>

      {/* Status control */}
      <div className="card p-4 mb-6 flex items-center gap-3">
        <span className="label mb-0">Status</span>
        <select
          className="input-field max-w-[180px]"
          value={lab.status}
          onChange={(e) => updateStatus.mutate(e.target.value)}
        >
          {options?.statuses.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        {updateStatus.isPending && <span className="text-xs text-slate-500">Saving...</span>}
      </div>

      {/* Overview */}
      {(lab.objective || lab.environment || lab.description) && (
        <div className="card p-6 mb-6 space-y-4">
          {lab.objective && (
            <div>
              <h3 className="text-sm font-semibold text-slate-300">Objective</h3>
              <p className="text-slate-400 text-sm mt-1 whitespace-pre-wrap">{lab.objective}</p>
            </div>
          )}
          {lab.environment && (
            <div>
              <h3 className="text-sm font-semibold text-slate-300">Environment</h3>
              <p className="text-slate-400 text-sm mt-1 whitespace-pre-wrap">{lab.environment}</p>
            </div>
          )}
          {lab.description && (
            <div>
              <h3 className="text-sm font-semibold text-slate-300">Description</h3>
              <p className="text-slate-400 text-sm mt-1 whitespace-pre-wrap">{lab.description}</p>
            </div>
          )}
        </div>
      )}

      {/* Tags */}
      <div className="card p-4 mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-2">Tags</h3>
        <div className="flex flex-wrap items-center gap-2">
          {lab.tags.map((tag) => (
            <span
              key={tag.id}
              className="inline-flex items-center gap-1 bg-surface-700 text-slate-300 text-xs px-2 py-1 rounded"
            >
              {tag.name}
              <button
                onClick={() => removeTag.mutate(tag.id)}
                className="text-slate-500 hover:text-status-danger"
                aria-label={`Remove tag ${tag.name}`}
              >
                ×
              </button>
            </span>
          ))}
          <input
            className="input-field max-w-[140px] text-xs py-1"
            placeholder="Add tag..."
            value={newTag}
            onChange={(e) => setNewTag(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                void handleAddTag();
              }
            }}
          />
        </div>
      </div>

      {/* Write-up editor */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-100">Write-up</h2>
          <div className="flex items-center gap-3">
            {saveState === "saved" && <span className="text-xs text-status-success">Saved</span>}
            {saveState === "error" && <span className="text-xs text-status-danger">Save failed</span>}
            <Button onClick={handleSaveWriteup} disabled={saveState === "saving"}>
              {saveState === "saving" ? "Saving..." : "Save write-up"}
            </Button>
          </div>
        </div>

        <div className="space-y-6">
          {WRITEUP_SECTIONS.map((section) => (
            <MarkdownEditor
              key={section.key}
              label={section.label}
              value={writeupDraft[section.key] ?? ""}
              onChange={(value) => setWriteupDraft((prev) => ({ ...prev, [section.key]: value }))}
              placeholder={section.placeholder}
              minRows={4}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
