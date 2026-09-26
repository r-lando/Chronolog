export function AlertBanner({ message }: { message: string }) {
  return (
    <div className="bg-status-danger/10 border border-status-danger/40 text-status-danger text-sm rounded-md px-3 py-2">
      {message}
    </div>
  );
}
