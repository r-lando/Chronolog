import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth, ApiError } from "../../context/AuthContext";
import { FormField } from "../../components/ui/FormField";
import { Button } from "../../components/ui/Button";
import { AlertBanner } from "../../components/ui/AlertBanner";

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register({ email, display_name: displayName, password });
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to create account. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-950 px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-slate-100">TALA</h1>
          <p className="text-sm text-slate-500 mt-1">Document. Analyze. Learn.</p>
        </div>

        <form onSubmit={handleSubmit} className="card p-6 space-y-4">
          <h2 className="text-lg font-semibold text-slate-100">Create your account</h2>
          <p className="text-xs text-slate-500 -mt-2">
            TALA is configured for a single user. This form only works once.
          </p>

          {error && <AlertBanner message={error} />}

          <FormField
            id="displayName"
            label="Display name"
            type="text"
            required
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
          <FormField
            id="email"
            label="Email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <FormField
            id="password"
            label="Password"
            type="password"
            autoComplete="new-password"
            required
            minLength={10}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <p className="text-xs text-slate-500">At least 10 characters, with a letter and a number.</p>

          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? "Creating account..." : "Create account"}
          </Button>

          <p className="text-sm text-slate-500 text-center">
            Already have an account?{" "}
            <Link to="/login" className="text-accent-400 hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
