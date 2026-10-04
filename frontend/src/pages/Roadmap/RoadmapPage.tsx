import { useMemo, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import {
  useCreateGoal,
  useDeleteGoal,
  useGoalProgress,
  useLearningGoals,
} from "../../hooks/useRoadmap";
import { useSkills } from "../../hooks/useSkills";
import { Button } from "../../components/ui/Button";
import { FormField } from "../../components/ui/FormField";
import { SelectField } from "../../components/ui/SelectField";
import { AlertBanner } from "../../components/ui/AlertBanner";
import { EmptyState } from "../../components/ui/EmptyState";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { CtfStatusBadge } from "../../components/ui/Badge";
import { ApiError } from "../../api/client";
import type { LearningGoal, LearningGoalTreeNode } from "../../types/roadmap";

function buildTree(goals: LearningGoal[]): LearningGoalTreeNode[] {
  const nodes = new Map<string, LearningGoalTreeNode>(goals.map((g) => [g.id, { ...g, children: [] }]));
  const roots: LearningGoalTreeNode[] = [];
  for (const goal of goals) {
    const node = nodes.get(goal.id)!;
    if (goal.parent_goal_id && nodes.has(goal.parent_goal_id)) {
      nodes.get(goal.parent_goal_id)!.children.push(node);
    } else {
      roots.push(node);
    }
  }
  return roots;
}

function GoalTreeItem({
  node,
  depth,
  selectedId,
  onSelect,
}: {
  node: LearningGoalTreeNode;
  depth: number;
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div>
      <button
        onClick={() => onSelect(node.id)}
        style={{ paddingLeft: `${depth * 1.25 + 0.75}rem` }}
        className={`w-full text-left py-1.5 pr-3 rounded text-sm transition-colors ${
          selectedId === node.id ? "bg-accent-500/15 text-accent-400" : "text-slate-300 hover:bg-surface-800"
        }`}
      >
        {node.title}
      </button>
      {node.children.map((child) => (
        <GoalTreeItem key={child.id} node={child} depth={depth + 1} selectedId={selectedId} onSelect={onSelect} />
      ))}
    </div>
  );
}

export function RoadmapPage() {
  const { data: goals, isLoading, error } = useLearningGoals();
  const { data: skills } = useSkills();
  const createGoal = useCreateGoal();
  const deleteGoal = useDeleteGoal();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [parentId, setParentId] = useState("");
  const [skillId, setSkillId] = useState("");
  const [notes, setNotes] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const tree = useMemo(() => buildTree(goals ?? []), [goals]);
  const selectedGoal = goals?.find((g) => g.id === selectedId);
  const { data: progress, isLoading: progressLoading } = useGoalProgress(selectedId ?? undefined);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createGoal.mutateAsync({
        title,
        parent_goal_id: parentId || null,
        related_skill_id: skillId || null,
        target_notes: notes || null,
      });
      setTitle("");
      setParentId("");
      setSkillId("");
      setNotes("");
      setShowForm(false);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Unable to create this goal.");
    }
  }

  async function handleDelete() {
    if (!selectedId) return;
    if (!window.confirm("Delete this goal and all its sub-goals?")) return;
    await deleteGoal.mutateAsync(selectedId);
    setSelectedId(null);
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Learning Roadmap</h1>
          <p className="text-slate-500 text-sm mt-1">
            Organize learning goals as a tree. Progress is computed from your actual labs — never self-rated.
          </p>
        </div>
        <Button onClick={() => setShowForm((v) => !v)}>{showForm ? "Cancel" : "+ New Goal"}</Button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card p-5 mb-6 space-y-4 max-w-xl">
          {formError && <AlertBanner message={formError} />}
          <FormField
            id="goal-title"
            label="Goal title"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. SOC Analyst, or a sub-goal like SIEM"
          />
          <div className="grid grid-cols-2 gap-4">
            <SelectField
              id="goal-parent"
              label="Parent goal (optional)"
              options={(goals ?? []).map((g) => g.title)}
              placeholder="None (top-level goal)"
              value={goals?.find((g) => g.id === parentId)?.title ?? ""}
              onChange={(e) => {
                const match = goals?.find((g) => g.title === e.target.value);
                setParentId(match?.id ?? "");
              }}
            />
            <SelectField
              id="goal-skill"
              label="Linked skill (optional)"
              options={(skills ?? []).map((s) => s.name)}
              placeholder="None (grouping goal)"
              value={skills?.find((s) => s.id === skillId)?.name ?? ""}
              onChange={(e) => {
                const match = skills?.find((s) => s.name === e.target.value);
                setSkillId(match?.id ?? "");
              }}
            />
          </div>
          <p className="text-xs text-slate-500 -mt-2">
            Link a goal to a skill to get real progress (labs completed, related CTFs, a recommended next
            activity). Leave it unlinked to use the goal purely as a grouping node, like "SOC Analyst" above
            its sub-goals.
          </p>
          <FormField
            id="goal-notes"
            label="Notes (optional)"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="What does reaching this goal look like?"
          />
          <Button type="submit" disabled={createGoal.isPending}>
            {createGoal.isPending ? "Creating..." : "Create goal"}
          </Button>
        </form>
      )}

      {isLoading && <LoadingState label="Loading roadmap..." />}
      {error && <ErrorState message={error instanceof ApiError ? error.message : "Failed to load roadmap."} />}

      {goals && goals.length === 0 && !showForm && (
        <EmptyState
          title="No learning goals yet"
          description='Create a top-level goal like "SOC Analyst", then add sub-goals linked to specific skills.'
        />
      )}

      {goals && goals.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="card p-3 lg:col-span-1">
            {tree.map((root) => (
              <GoalTreeItem key={root.id} node={root} depth={0} selectedId={selectedId} onSelect={setSelectedId} />
            ))}
          </div>

          <div className="lg:col-span-2">
            {!selectedGoal && (
              <div className="card p-6 text-slate-500 text-sm">Select a goal to see its progress.</div>
            )}

            {selectedGoal && (
              <div className="card p-6">
                <div className="flex items-start justify-between mb-4">
                  <h2 className="text-lg font-semibold text-slate-100">{selectedGoal.title}</h2>
                  <Button variant="secondary" onClick={handleDelete}>
                    Delete
                  </Button>
                </div>

                {selectedGoal.target_notes && (
                  <p className="text-sm text-slate-400 mb-4">{selectedGoal.target_notes}</p>
                )}

                {progressLoading && <LoadingState label="Loading progress..." />}

                {progress && (
                  <>
                    {progress.has_related_skill ? (
                      <>
                        <div className="grid grid-cols-1 gap-4 mb-4">
                          <div className="bg-surface-800 border border-surface-700 rounded-md p-4">
                            <p className="text-2xl font-bold text-accent-400">{progress.labs_completed}</p>
                            <p className="text-xs text-slate-500 mt-1">Labs completed for this skill</p>
                          </div>
                        </div>

                        {progress.related_labs.length > 0 && (
                          <div className="mb-4">
                            <h3 className="text-sm font-semibold text-slate-300 mb-2">Related labs</h3>
                            <div className="space-y-2">
                              {progress.related_labs.map((lab) => (
                                <Link
                                  key={lab.id}
                                  to={`/labs/${lab.id}`}
                                  className="block text-sm text-slate-300 hover:text-accent-400 bg-surface-800 border border-surface-700 rounded-md px-3 py-2"
                                >
                                  {lab.title}
                                </Link>
                              ))}
                            </div>
                          </div>
                        )}

                        {progress.related_ctf_challenges.length > 0 && (
                          <div className="mb-4">
                            <h3 className="text-sm font-semibold text-slate-300 mb-2">Related CTF challenges</h3>
                            <div className="space-y-2">
                              {progress.related_ctf_challenges.map((challenge) => (
                                <div
                                  key={challenge.id}
                                  className="flex items-center justify-between bg-surface-800 border border-surface-700 rounded-md px-3 py-2"
                                >
                                  <span className="text-sm text-slate-300">{challenge.title}</span>
                                  <CtfStatusBadge status={challenge.status} />
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="grid grid-cols-2 gap-4 mb-4">
                        <div className="bg-surface-800 border border-surface-700 rounded-md p-4">
                          <p className="text-2xl font-bold text-accent-400">{progress.child_count}</p>
                          <p className="text-xs text-slate-500 mt-1">Sub-goals</p>
                        </div>
                        <div className="bg-surface-800 border border-surface-700 rounded-md p-4">
                          <p className="text-2xl font-bold text-status-success">{progress.children_with_activity}</p>
                          <p className="text-xs text-slate-500 mt-1">With documented activity</p>
                        </div>
                      </div>
                    )}

                    <div className="bg-accent-500/10 border border-accent-500/30 rounded-md px-4 py-3">
                      <p className="text-sm text-accent-400">{progress.recommended_next_activity}</p>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
