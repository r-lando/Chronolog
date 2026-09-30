import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useCreateCtfChallenge, useCtfEvent, useCtfOptions, useDeleteCtfEvent } from "../../hooks/useCtf";
import { Button } from "../../components/ui/Button";
import { FormField } from "../../components/ui/FormField";
import { SelectField } from "../../components/ui/SelectField";
import { AlertBanner } from "../../components/ui/AlertBanner";
import { EmptyState } from "../../components/ui/EmptyState";
import { CtfStatusBadge, DifficultyBadge } from "../../components/ui/Badge";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { ApiError } from "../../api/client";

export function CtfEventDetailPage() {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();

  const { data: event, isLoading, error } = useCtfEvent(eventId);
  const { data: options } = useCtfOptions();
  const createChallenge = useCreateCtfChallenge(eventId ?? "");
  const deleteEvent = useDeleteCtfEvent();

  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  if (isLoading) return <LoadingState label="Loading CTF event..." />;
  if (error || !event) {
    return <ErrorState message={error instanceof ApiError ? error.message : "CTF event not found."} />;
  }

  const solvedCount = event.challenges.filter((c) => c.status === "Solved").length;
  const partialCount = event.challenges.filter((c) => c.status === "Partially Solved").length;

  async function handleCreate(formEvent: FormEvent) {
    formEvent.preventDefault();
    setFormError(null);
    try {
      const created = await createChallenge.mutateAsync({
        title,
        category,
        difficulty,
        status: "Unsolved",
        time_spent_minutes: null,
        description: null,
        solution_writeup: null,
        lessons_learned: null,
      });
      navigate(`/ctfs/challenges/${created.id}`);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Unable to create this challenge.");
    }
  }

  async function handleDeleteEvent() {
    if (!eventId) return;
    if (!window.confirm("Delete this event, all its challenges, and their evidence permanently?")) return;
    await deleteEvent.mutateAsync(eventId);
    navigate("/ctfs");
  }

  return (
    <div className="max-w-4xl">
      <div className="flex items-start justify-between mb-6">
        <div>
          <Link to="/ctfs" className="text-xs text-slate-500 hover:text-accent-400">
            ← All CTF events
          </Link>
          <h1 className="text-2xl font-bold text-slate-100 mt-1">{event.name}</h1>
          <p className="text-slate-500 text-sm mt-1">
            {[event.platform, event.event_date && new Date(event.event_date).toLocaleDateString()]
              .filter(Boolean)
              .join(" · ")}
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setShowForm((v) => !v)}>{showForm ? "Cancel" : "+ New Challenge"}</Button>
          <Button variant="secondary" onClick={handleDeleteEvent}>
            Delete event
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="card p-4">
          <p className="text-2xl font-bold text-accent-400">{event.challenges.length}</p>
          <p className="text-xs text-slate-500 mt-1">Challenges</p>
        </div>
        <div className="card p-4">
          <p className="text-2xl font-bold text-status-success">{solvedCount}</p>
          <p className="text-xs text-slate-500 mt-1">Solved</p>
        </div>
        <div className="card p-4">
          <p className="text-2xl font-bold text-status-warning">{partialCount}</p>
          <p className="text-xs text-slate-500 mt-1">Partially solved</p>
        </div>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card p-5 mb-6 space-y-4">
          {formError && <AlertBanner message={formError} />}
          <FormField
            id="challenge-title"
            label="Challenge name"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <div className="grid grid-cols-2 gap-4">
            <SelectField
              id="challenge-category"
              label="Category"
              required
              options={options?.categories ?? []}
              placeholder="Select category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            />
            <SelectField
              id="challenge-difficulty"
              label="Difficulty"
              required
              options={options?.difficulties ?? []}
              placeholder="Select difficulty"
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
            />
          </div>
          <Button type="submit" disabled={createChallenge.isPending}>
            {createChallenge.isPending ? "Creating..." : "Create challenge"}
          </Button>
        </form>
      )}

      {event.challenges.length === 0 && !showForm && (
        <EmptyState
          title="No challenges yet"
          description="Add the challenges you attempted at this event to document your approach and what you learned."
        />
      )}

      {event.challenges.length > 0 && (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-surface-800 text-slate-400 text-left">
              <tr>
                <th className="px-4 py-3 font-medium">Challenge</th>
                <th className="px-4 py-3 font-medium">Category</th>
                <th className="px-4 py-3 font-medium">Difficulty</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {event.challenges.map((challenge) => (
                <tr key={challenge.id} className="border-t border-surface-700 hover:bg-surface-800/60">
                  <td className="px-4 py-3">
                    <Link
                      to={`/ctfs/challenges/${challenge.id}`}
                      className="text-slate-200 hover:text-accent-400 font-medium"
                    >
                      {challenge.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-400">{challenge.category}</td>
                  <td className="px-4 py-3">
                    <DifficultyBadge difficulty={challenge.difficulty} />
                  </td>
                  <td className="px-4 py-3">
                    <CtfStatusBadge status={challenge.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
