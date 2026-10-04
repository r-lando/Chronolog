import { Link } from "react-router-dom";
import { useLabs, useSetPortfolioStatus } from "../../hooks/useLabs";
import { Button } from "../../components/ui/Button";
import { DifficultyBadge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { ApiError } from "../../api/client";
import type { Lab } from "../../types/lab";

function PortfolioRow({ lab }: { lab: Lab }) {
  const setPortfolioStatus = useSetPortfolioStatus(lab.id);

  return (
    <div className="flex items-center justify-between bg-surface-800 border border-surface-700 rounded-md px-4 py-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <Link to={`/labs/${lab.id}`} className="text-slate-200 hover:text-accent-400 font-medium text-sm">
            {lab.title}
          </Link>
          <DifficultyBadge difficulty={lab.difficulty} />
        </div>
        {lab.portfolio_slug && (
          <Link
            to={`/p/${lab.portfolio_slug}`}
            target="_blank"
            className="text-xs text-accent-400 hover:underline"
          >
            /p/{lab.portfolio_slug}
          </Link>
        )}
      </div>
      <Button variant="secondary" onClick={() => setPortfolioStatus.mutate(false)} disabled={setPortfolioStatus.isPending}>
        Remove from portfolio
      </Button>
    </div>
  );
}

export function PortfolioPage() {
  const { data: labs, isLoading, error } = useLabs();
  const publishedLabs = labs?.filter((lab) => lab.is_portfolio_ready) ?? [];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Portfolio</h1>
        <p className="text-slate-500 text-sm mt-1">
          Labs you've published publicly. Mark a lab "portfolio-ready" from its detail page to add it here.
        </p>
      </div>

      {isLoading && <LoadingState label="Loading portfolio..." />}
      {error && <ErrorState message={error instanceof ApiError ? error.message : "Failed to load labs."} />}

      {labs && publishedLabs.length === 0 && (
        <EmptyState
          title="Nothing published yet"
          description="Open a lab and use the Portfolio control to publish its write-up publicly."
        />
      )}

      {publishedLabs.length > 0 && (
        <>
          <div className="mb-4">
            <Link to="/p" target="_blank" className="text-sm text-accent-400 hover:underline">
              View your public portfolio page →
            </Link>
          </div>
          <div className="space-y-2">
            {publishedLabs.map((lab) => (
              <PortfolioRow key={lab.id} lab={lab} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
