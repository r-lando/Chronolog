export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return <p className="text-slate-500 text-sm py-8 text-center">{label}</p>;
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-status-danger/10 border border-status-danger/40 text-status-danger text-sm rounded-md px-4 py-3">
      {message}
    </div>
  );
}
