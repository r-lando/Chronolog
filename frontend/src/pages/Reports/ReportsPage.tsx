import { useState } from "react";
import { Link } from "react-router-dom";
import { useLabs } from "../../hooks/useLabs";
import { reportsApi, type ReportFormat } from "../../api/reports";
import { Button } from "../../components/ui/Button";
import { AlertBanner } from "../../components/ui/AlertBanner";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { EmptyState } from "../../components/ui/EmptyState";
import { DifficultyBadge, StatusBadge } from "../../components/ui/Badge";
import { ApiError } from "../../api/client";

export function ReportsPage() {
  const { data: labs, isLoading, error } = useLabs();
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [downloadingKey, setDownloadingKey] = useState<string | null>(null);

  async function handleLabDownload(labId: string, format: ReportFormat) {
    const key = `${labId}-${format}`;
    setDownloadError(null);
    setDownloadingKey(key);
    try {
      await reportsApi.downloadLabReport(labId, format);
    } catch (err) {
      setDownloadError(err instanceof ApiError ? err.message : "Failed to generate this report.");
    } finally {
      setDownloadingKey(null);
    }
  }

  async function handleSummaryDownload(format: ReportFormat) {
    setDownloadError(null);
    setDownloadingKey(`summary-${format}`);
    try {
      await reportsApi.downloadLearningSummary(format);
    } catch (err) {
      setDownloadError(err instanceof ApiError ? err.message : "Failed to generate the learning summary.");
    } finally {
      setDownloadingKey(null);
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Reports</h1>
        <p className="text-slate-500 text-sm mt-1">
          Export a full write-up for a single lab, or a summary of all your learning activity. These are
          private downloads — not published anywhere.
        </p>
      </div>

      {downloadError && (
        <div className="mb-4">
          <AlertBanner message={downloadError} />
        </div>
      )}

      {/* Learning summary */}
      <div className="card p-5 mb-6">
        <h2 className="text-sm font-semibold text-slate-300 mb-1">Learning Summary</h2>
        <p className="text-xs text-slate-500 mb-3">
          Labs completed, CTFs, skills, tools, MITRE coverage, and activity over time — everything on your
          dashboard, as a document.
        </p>
        <div className="flex gap-2">
          <Button onClick={() => handleSummaryDownload("pdf")} disabled={downloadingKey === "summary-pdf"}>
            {downloadingKey === "summary-pdf" ? "Generating..." : "Download PDF"}
          </Button>
          <Button
            variant="secondary"
            onClick={() => handleSummaryDownload("markdown")}
            disabled={downloadingKey === "summary-markdown"}
          >
            {downloadingKey === "summary-markdown" ? "Generating..." : "Download Markdown"}
          </Button>
        </div>
      </div>

      {/* Per-lab reports */}
      <div className="card p-5">
        <h2 className="text-sm font-semibold text-slate-300 mb-1">Lab Reports</h2>
        <p className="text-xs text-slate-500 mb-4">
          Objective, environment, methodology, findings, evidence, MITRE techniques, and lessons learned for
          one lab — including private notes and evidence, since this is your own export.
        </p>

        {isLoading && <LoadingState label="Loading labs..." />}
        {error && <ErrorState message={error instanceof ApiError ? error.message : "Failed to load labs."} />}

        {labs && labs.length === 0 && (
          <EmptyState title="No labs yet" description="Document a lab first, then come back to export it." />
        )}

        {labs && labs.length > 0 && (
          <div className="space-y-2">
            {labs.map((lab) => (
              <div
                key={lab.id}
                className="flex items-center justify-between bg-surface-800 border border-surface-700 rounded-md px-4 py-3"
              >
                <div className="min-w-0 mr-4">
                  <Link to={`/labs/${lab.id}`} className="text-sm text-slate-200 hover:text-accent-400 font-medium">
                    {lab.title}
                  </Link>
                  <div className="flex items-center gap-1.5 mt-1">
                    <DifficultyBadge difficulty={lab.difficulty} />
                    <StatusBadge status={lab.status} />
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  <Button
                    variant="secondary"
                    onClick={() => handleLabDownload(lab.id, "pdf")}
                    disabled={downloadingKey === `${lab.id}-pdf`}
                  >
                    {downloadingKey === `${lab.id}-pdf` ? "..." : "PDF"}
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => handleLabDownload(lab.id, "markdown")}
                    disabled={downloadingKey === `${lab.id}-markdown`}
                  >
                    {downloadingKey === `${lab.id}-markdown` ? "..." : "Markdown"}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
