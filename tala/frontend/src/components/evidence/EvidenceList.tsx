import type { Evidence } from "../../types/evidence";
import { EVIDENCE_TYPE_LABELS } from "../../types/evidence";
import { getEvidenceFileUrl } from "../../api/evidence";
import { useDeleteEvidence } from "../../hooks/useEvidence";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function EvidenceList({ labId, evidence }: { labId: string; evidence: Evidence[] }) {
  const deleteEvidence = useDeleteEvidence(labId);

  if (evidence.length === 0) {
    return <p className="text-slate-500 text-sm">No evidence uploaded yet for this lab.</p>;
  }

  return (
    <div className="space-y-2">
      {evidence.map((item) => (
        <div
          key={item.id}
          className="flex items-center justify-between bg-surface-800 border border-surface-700 rounded-md px-4 py-3"
        >
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-slate-200 text-sm font-medium truncate">{item.original_filename}</span>
              <span className="text-xs bg-surface-700 text-slate-400 px-1.5 py-0.5 rounded">
                {EVIDENCE_TYPE_LABELS[item.evidence_type]}
              </span>
            </div>
            {item.description && <p className="text-xs text-slate-500 mt-0.5">{item.description}</p>}
            <p className="text-xs text-slate-600 mt-0.5 font-mono truncate">
              {formatBytes(item.file_size_bytes)} · sha256:{item.sha256_hash.slice(0, 16)}...
            </p>
          </div>
          <div className="flex items-center gap-3 shrink-0 ml-4">
            <a
              href={getEvidenceFileUrl(item.id)}
              target="_blank"
              rel="noreferrer"
              className="text-accent-400 hover:underline text-sm"
            >
              Download
            </a>
            <button
              onClick={() => deleteEvidence.mutate(item.id)}
              className="text-slate-500 hover:text-status-danger text-sm"
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
