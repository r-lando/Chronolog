import { useState } from "react";
import { Link } from "react-router-dom";
import { useAllEvidence } from "../../hooks/useEvidence";
import { EVIDENCE_TYPE_LABELS, type EvidenceType } from "../../types/evidence";
import { getEvidenceFileUrl } from "../../api/evidence";
import { EmptyState } from "../../components/ui/EmptyState";
import { LoadingState, ErrorState } from "../../components/ui/StatusStates";
import { ApiError } from "../../api/client";

const EVIDENCE_TYPES = Object.keys(EVIDENCE_TYPE_LABELS) as EvidenceType[];

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function EvidencePage() {
  const [typeFilter, setTypeFilter] = useState("");
  const { data: evidence, isLoading, error } = useAllEvidence(typeFilter || undefined);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Evidence</h1>
        <p className="text-slate-500 text-sm mt-1">
          Every screenshot, log, PCAP, and file uploaded across all your labs.
        </p>
      </div>

      <div className="card p-4 mb-6">
        <select className="input-field max-w-[220px]" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">All types</option>
          {EVIDENCE_TYPES.map((type) => (
            <option key={type} value={type}>
              {EVIDENCE_TYPE_LABELS[type]}
            </option>
          ))}
        </select>
      </div>

      {isLoading && <LoadingState label="Loading evidence..." />}
      {error && (
        <ErrorState message={error instanceof ApiError ? error.message : "Failed to load evidence."} />
      )}

      {evidence && evidence.length === 0 && (
        <EmptyState
          title="No evidence yet"
          description="Upload screenshots, logs, or other evidence from a lab's detail page to see it here."
        />
      )}

      {evidence && evidence.length > 0 && (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-surface-800 text-slate-400 text-left">
              <tr>
                <th className="px-4 py-3 font-medium">File</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Lab</th>
                <th className="px-4 py-3 font-medium">Size</th>
                <th className="px-4 py-3 font-medium">Uploaded</th>
                <th className="px-4 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {evidence.map((item) => (
                <tr key={item.id} className="border-t border-surface-700 hover:bg-surface-800/60">
                  <td className="px-4 py-3 text-slate-200">{item.original_filename}</td>
                  <td className="px-4 py-3 text-slate-400">{EVIDENCE_TYPE_LABELS[item.evidence_type]}</td>
                  <td className="px-4 py-3">
                    <Link to={`/labs/${item.lab_id}`} className="text-accent-400 hover:underline">
                      {item.lab_title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-500">{formatBytes(item.file_size_bytes)}</td>
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(item.uploaded_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <a
                      href={getEvidenceFileUrl(item.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="text-accent-400 hover:underline"
                    >
                      Download
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
