import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen bg-surface-950">
      <Sidebar />
      <main className="flex-1 p-8 max-w-6xl mx-auto w-full">{children}</main>
    </div>
  );
}
