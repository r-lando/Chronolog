import { Link, useSearchParams } from "react-router-dom";
import { useSearch } from "../../hooks/useSearch";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { EmptyState } from "../../components/ui/EmptyState";
import { ApiError } from "../../api/client";
import type { SearchResultType } from "../../types/search";

const TYPE_LABELS: Record<SearchResultType, string> = {
  lab: "Labs",
  ctf_challenge: "CTF Challenges",
  finding: "Findings",
  tag: "Tags",
  skill: "Skills",
  tool: "Tools",
  mitre_technique: "MITRE ATT&CK Techniques",
};

const TYPE_ORDER: SearchResultType[] = ["lab", "ctf_challenge", "finding", "tag", "skill", "tool", "mitre_technique"];

export function SearchResultsPage() {
  const [searchParams] = useSearchParams();
  const query = searchParams.get("q") ?? "";
  const { data, isLoading, error } = useSearch(query);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Search results</h1>
        {query && <p className="text-slate-500 text-sm mt-1">Showing results for "{query}"</p>}
      </div>

      {!query && <EmptyState title="Type something to search" description="Search across labs, CTFs, skills, tools, MITRE techniques, tags, and findings." />}

      {isLoading && <LoadingState label="Searching..." />}
      {error && <ErrorState message={error instanceof ApiError ? error.message : "Search failed."} />}

      {data && data.results.length === 0 && (
        <EmptyState title="No results" description={`Nothing matched "${query}".`} />
      )}

      {data && data.results.length > 0 && (
        <div className="space-y-6">
          {TYPE_ORDER.map((type) => {
            const items = data.results.filter((r) => r.type === type);
            if (items.length === 0) return null;
            return (
              <div key={type}>
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-2">
                  {TYPE_LABELS[type]}
                </h2>
                <div className="space-y-2">
                  {items.map((item) => (
                    <Link
                      key={`${item.type}-${item.id}`}
                      to={item.url}
                      className="flex items-center justify-between bg-surface-800 border border-surface-700 rounded-md px-4 py-3 hover:border-accent-500/50 transition-colors"
                    >
                      <span className="text-sm text-slate-200">{item.title}</span>
                      {item.subtitle && <span className="text-xs text-slate-500">{item.subtitle}</span>}
                    </Link>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
