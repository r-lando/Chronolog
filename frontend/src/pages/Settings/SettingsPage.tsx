import { useState, type FormEvent } from "react";
import { useAuth } from "../../context/AuthContext";
import { authApi } from "../../api/auth";
import { ApiError } from "../../api/client";
import { FormField } from "../../components/ui/FormField";
import { Button } from "../../components/ui/Button";
import { AlertBanner } from "../../components/ui/AlertBanner";

export function SettingsPage() {
  const { user } = useAuth();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSuccess(false);
    setIsSubmitting(true);
    try {
      await authApi.changePassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setSuccess(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to change your password.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="max-w-md">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Settings</h1>
        <p className="text-slate-500 text-sm mt-1">Account details and security.</p>
      </div>

      <div className="card p-5 mb-6">
        <h2 className="text-sm font-semibold text-slate-300 mb-3">Account</h2>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-slate-500">Display name</dt>
            <dd className="text-slate-200">{user?.display_name}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-500">Email</dt>
            <dd className="text-slate-200">{user?.email}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-500">Member since</dt>
            <dd className="text-slate-200">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}
            </dd>
          </div>
        </dl>
      </div>

      <form onSubmit={handleSubmit} className="card p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-300">Change password</h2>

        {error && <AlertBanner message={error} />}
        {success && (
          <div className="bg-status-success/10 border border-status-success/40 text-status-success text-sm rounded-md px-3 py-2">
            Password changed successfully.
          </div>
        )}

        <FormField
          id="current-password"
          label="Current password"
          type="password"
          autoComplete="current-password"
          required
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
        />
        <FormField
          id="new-password"
          label="New password"
          type="password"
          autoComplete="new-password"
          required
          minLength={10}
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
        />
        <p className="text-xs text-slate-500 -mt-2">At least 10 characters, with a letter and a number.</p>

        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Changing..." : "Change password"}
        </Button>
      </form>
    </div>
  );
}
