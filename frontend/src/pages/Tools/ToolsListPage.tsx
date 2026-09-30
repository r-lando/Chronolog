import { Link } from "react-router-dom";
import { useTools } from "../../hooks/useTools";
import { EmptyState } from "../../components/ui/EmptyState";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { ApiError } from "../../api/client";

export function ToolsListPage() {
  const { data: tools, isLoading, error } = useTools();

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Tools</h1>
        <p className="text-slate-500 text-sm mt-1">Security tools used across your labs.</p>
      </div>

      {isLoading && <LoadingState label="Loading tools..." />}
      {error && <ErrorState message={error instanceof ApiError ? error.message : "Failed to load tools."} />}

      {tools && tools.length === 0 && (
        <EmptyState
          title="No tools tracked yet"
          description="Attach a tool to a lab from its detail page to start building this list."
        />
      )}

      {tools && tools.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {tools.map((tool) => (
            <Link
              key={tool.id}
              to={`/tools/${tool.id}`}
              className="card p-5 hover:border-accent-500/50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <h3 className="font-semibold text-slate-100">{tool.name}</h3>
                {tool.category && (
                  <span className="text-xs bg-surface-700 text-slate-400 px-1.5 py-0.5 rounded shrink-0 ml-2">
                    {tool.category}
                  </span>
                )}
              </div>
              <div className="mt-3 flex items-baseline gap-1.5">
                <span className="text-2xl font-bold text-accent-400">{tool.lab_count}</span>
                <span className="text-sm text-slate-500">{tool.lab_count === 1 ? "lab" : "labs"}</span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                {tool.last_used ? `Last used ${new Date(tool.last_used).toLocaleDateString()}` : "Not yet used"}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
