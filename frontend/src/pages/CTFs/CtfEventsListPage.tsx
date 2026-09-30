import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useCreateCtfEvent, useCtfEvents } from "../../hooks/useCtf";
import { Button } from "../../components/ui/Button";
import { FormField } from "../../components/ui/FormField";
import { AlertBanner } from "../../components/ui/AlertBanner";
import { EmptyState } from "../../components/ui/EmptyState";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { ApiError } from "../../api/client";

export function CtfEventsListPage() {
  const { data: events, isLoading, error } = useCtfEvents();
  const createEvent = useCreateCtfEvent();

  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [platform, setPlatform] = useState("");
  const [eventDate, setEventDate] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await createEvent.mutateAsync({
        name,
        platform: platform || null,
        event_date: eventDate || null,
      });
      setName("");
      setPlatform("");
      setEventDate("");
      setShowForm(false);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Unable to create this event.");
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">CTFs</h1>
          <p className="text-slate-500 text-sm mt-1">
            Competitions and platforms you've played, with the challenges you attempted.
          </p>
        </div>
        <Button onClick={() => setShowForm((v) => !v)}>{showForm ? "Cancel" : "+ New CTF Event"}</Button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card p-5 mb-6 space-y-4 max-w-xl">
          {formError && <AlertBanner message={formError} />}
          <FormField
            id="ctf-event-name"
            label="Event / competition name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. PicoCTF 2026"
          />
          <div className="grid grid-cols-2 gap-4">
            <FormField
              id="ctf-event-platform"
              label="Platform"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              placeholder="PicoCTF, HTB, CTFtime..."
            />
            <FormField
              id="ctf-event-date"
              label="Date"
              type="date"
              value={eventDate}
              onChange={(e) => setEventDate(e.target.value)}
            />
          </div>
          <Button type="submit" disabled={createEvent.isPending}>
            {createEvent.isPending ? "Creating..." : "Create event"}
          </Button>
        </form>
      )}

      {isLoading && <LoadingState label="Loading CTF events..." />}
      {error && <ErrorState message={error instanceof ApiError ? error.message : "Failed to load CTF events."} />}

      {events && events.length === 0 && !showForm && (
        <EmptyState
          title="No CTF events yet"
          description="Create an event for a competition or platform, then add the challenges you attempt."
        />
      )}

      {events && events.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {events.map((ctfEvent) => (
            <Link
              key={ctfEvent.id}
              to={`/ctfs/${ctfEvent.id}`}
              className="card p-5 hover:border-accent-500/50 transition-colors"
            >
              <h3 className="font-semibold text-slate-100">{ctfEvent.name}</h3>
              <p className="text-sm text-slate-500 mt-1">
                {[ctfEvent.platform, ctfEvent.event_date && new Date(ctfEvent.event_date).toLocaleDateString()]
                  .filter(Boolean)
                  .join(" · ") || "No details"}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
