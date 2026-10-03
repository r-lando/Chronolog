import { Link } from "react-router-dom";
import { usePublicPortfolio } from "../../hooks/usePortfolio";
import { DifficultyBadge } from "../../components/ui/Badge";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { EmptyState } from "../../components/ui/EmptyState";
import { ApiError } from "../../api/client";

export function PublicPortfolioIndexPage() {
  const { data: labs, isLoading, error } = usePublicPortfolio();

  return (
    <div className="min-h-screen bg-surface-950">
      <div className="max-w-3xl mx-auto px-6 py-12">
        <header className="mb-10">
          <h1 className="text-2xl font-bold text-slate-100">Cybersecurity Lab Portfolio</h1>
          <p className="text-slate-500 text-sm mt-1">
            Documented labs, investigations, and write-ups. Built with TALA.
          </p>
        </header>

        {isLoading && <LoadingState label="Loading portfolio..." />}
        {error && (
          <ErrorState message={error instanceof ApiError ? error.message : "Failed to load this portfolio."} />
        )}

        {labs && labs.length === 0 && (
          <EmptyState title="No published labs yet" description="Check back soon." />
        )}

        {labs && labs.length > 0 && (
          <div className="space-y-4">
            {labs.map((lab) => (
              <Link
                key={lab.slug}
                to={`/p/${lab.slug}`}
                className="block card p-5 hover:border-accent-500/50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <h2 className="font-semibold text-slate-100">{lab.title}</h2>
                  <DifficultyBadge difficulty={lab.difficulty} />
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  {lab.category}
                  {lab.platform && ` · ${lab.platform}`}
                </p>
                {lab.summary && <p className="text-sm text-slate-400 mt-2">{lab.summary}</p>}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
