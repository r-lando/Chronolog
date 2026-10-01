export function StatCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="card p-4">
      <p className="text-2xl font-bold text-accent-400">{value}</p>
      <p className="text-xs text-slate-500 mt-1">{label}</p>
      {hint && <p className="text-xs text-slate-600 mt-0.5">{hint}</p>}
    </div>
  );
}
