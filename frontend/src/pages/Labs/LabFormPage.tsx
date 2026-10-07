import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useCreateLab, useLab, useLabOptions, useUpdateLab } from "../../hooks/useLabs";
import { FormField } from "../../components/ui/FormField";
import { SelectField } from "../../components/ui/SelectField";
import { TextareaField } from "../../components/ui/TextareaField";
import { Button } from "../../components/ui/Button";
import { AlertBanner } from "../../components/ui/AlertBanner";
import { LoadingState } from "../../components/ui/StatusStates";
import { ApiError } from "../../api/client";
import type { LabFormValues } from "../../types/lab";
import type { LabPayload } from "../../api/labs";

const EMPTY_FORM: LabFormValues = {
  title: "",
  platform: "",
  category: "",
  difficulty: "",
  status: "Planned",
  date_started: "",
  date_completed: "",
  time_spent_minutes: "",
  description: "",
  objective: "",
  environment: "",
};

function toPayload(form: LabFormValues): LabPayload {
  return {
    title: form.title,
    platform: form.platform || null,
    category: form.category,
    difficulty: form.difficulty,
    status: form.status,
    date_started: form.date_started || null,
    date_completed: form.date_completed || null,
    time_spent_minutes: form.time_spent_minutes ? Number(form.time_spent_minutes) : null,
    description: form.description || null,
    objective: form.objective || null,
    environment: form.environment || null,
  };
}

export function LabFormPage() {
  const { id } = useParams<{ id: string }>();
  const isEditing = Boolean(id);
  const navigate = useNavigate();

  const { data: options } = useLabOptions();
  const { data: existingLab, isLoading: isLoadingLab } = useLab(id);
  const createLab = useCreateLab();
  const updateLab = useUpdateLab(id ?? "");

  const [form, setForm] = useState<LabFormValues>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (existingLab) {
      setForm({
        title: existingLab.title,
        platform: existingLab.platform ?? "",
        category: existingLab.category,
        difficulty: existingLab.difficulty,
        status: existingLab.status,
        date_started: existingLab.date_started ?? "",
        date_completed: existingLab.date_completed ?? "",
        time_spent_minutes: existingLab.time_spent_minutes?.toString() ?? "",
        description: existingLab.description ?? "",
        objective: existingLab.objective ?? "",
        environment: existingLab.environment ?? "",
      });
    }
  }, [existingLab]);

  function updateField<K extends keyof LabFormValues>(key: K, value: LabFormValues[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const payload = toPayload(form);
      if (isEditing && id) {
        await updateLab.mutateAsync(payload);
        navigate(`/labs/${id}`);
      } else {
        const created = await createLab.mutateAsync(payload);
        navigate(`/labs/${created.id}`);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to save this lab. Please try again.");
    }
  }

  if (isEditing && isLoadingLab) {
    return <LoadingState label="Loading lab..." />;
  }

  const isSubmitting = createLab.isPending || updateLab.isPending;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-100 mb-6">
        {isEditing ? "Edit Lab" : "New Lab"}
      </h1>

      <form onSubmit={handleSubmit} className="card p-6 space-y-4">
        {error && <AlertBanner message={error} />}

        <FormField
          id="title"
          label="Title"
          required
          value={form.title}
          onChange={(e) => updateField("title", e.target.value)}
          placeholder="e.g. Windows Event Log Investigation"
        />

        <div className="grid grid-cols-2 gap-4">
          <FormField
            id="platform"
            label="Platform"
            value={form.platform}
            onChange={(e) => updateField("platform", e.target.value)}
            placeholder="TryHackMe, HTB, Home Lab..."
          />
          <SelectField
            id="difficulty"
            label="Difficulty"
            required
            options={options?.difficulties ?? []}
            placeholder="Select difficulty"
            value={form.difficulty}
            onChange={(e) => updateField("difficulty", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <SelectField
            id="category"
            label="Category"
            required
            options={options?.categories ?? []}
            placeholder="Select category"
            value={form.category}
            onChange={(e) => updateField("category", e.target.value)}
          />
          <SelectField
            id="status"
            label="Status"
            required
            options={options?.statuses ?? []}
            value={form.status}
            onChange={(e) => updateField("status", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <FormField
            id="date_started"
            label="Date started"
            type="date"
            value={form.date_started}
            onChange={(e) => updateField("date_started", e.target.value)}
          />
          <FormField
            id="date_completed"
            label="Date completed"
            type="date"
            value={form.date_completed}
            onChange={(e) => updateField("date_completed", e.target.value)}
          />
          <FormField
            id="time_spent_minutes"
            label="Time spent (min)"
            type="number"
            min={0}
            value={form.time_spent_minutes}
            onChange={(e) => updateField("time_spent_minutes", e.target.value)}
          />
        </div>

        <TextareaField
          id="objective"
          label="Objective"
          value={form.objective}
          onChange={(e) => updateField("objective", e.target.value)}
          placeholder="What was the purpose of this lab?"
        />
        <TextareaField
          id="environment"
          label="Environment"
          value={form.environment}
          onChange={(e) => updateField("environment", e.target.value)}
          placeholder="OS, machines, network setup involved..."
        />
        <TextareaField
          id="description"
          label="Description"
          value={form.description}
          onChange={(e) => updateField("description", e.target.value)}
          placeholder="A short summary of this lab"
        />

        <div className="flex gap-3 pt-2">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Saving..." : isEditing ? "Save changes" : "Create lab"}
          </Button>
          <Button type="button" variant="secondary" onClick={() => navigate(-1)}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
