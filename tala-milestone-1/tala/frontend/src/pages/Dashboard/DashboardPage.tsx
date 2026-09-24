import { useAuth } from "../../context/AuthContext";

export function DashboardPage() {
  const { user } = useAuth();

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-100">Welcome back, {user?.display_name}</h1>
      <p className="text-slate-500 mt-1">
        This is a placeholder dashboard. Real statistics, charts, and recent activity will be
        built in Milestone 7 once labs, skills, tools, and MITRE data exist to summarize.
      </p>

      <div className="card p-6 mt-6">
        <p className="text-sm text-slate-400">
          Authentication is working end-to-end: registration, login, protected routing, and
          session persistence via an HttpOnly cookie.
        </p>
      </div>
    </div>
  );
}
