export function ComingSoonPage({ title, milestone }: { title: string; milestone: string }) {
  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-100">{title}</h1>
      <div className="card p-6 mt-6">
        <p className="text-sm text-slate-400">This section will be built in {milestone}.</p>
      </div>
    </div>
  );
}
