import { useRef, useState, type FormEvent } from "react";
import { useCtfEvidence, useDeleteCtfEvidence, useUploadCtfEvidence } from "../../hooks/useCtf";
import { getCtfEvidenceFileUrl } from "../../api/ctfEvidence";
import { EVIDENCE_TYPE_LABELS, type EvidenceType } from "../../types/evidence";
import { Button } from "../ui/Button";
import { AlertBanner } from "../ui/AlertBanner";
import { LoadingState } from "../ui/StatusStates";
import { ApiError } from "../../api/client";

const EVIDENCE_TYPES = Object.keys(EVIDENCE_TYPE_LABELS) as EvidenceType[];

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function CtfEvidenceSection({ challengeId }: { challengeId: string }) {
  const { data: evidence, isLoading } = useCtfEvidence(challengeId);
  const upload = useUploadCtfEvidence(challengeId);
  const remove = useDeleteCtfEvidence(challengeId);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [evidenceType, setEvidenceType] = useState<EvidenceType>("screenshot");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!file) {
      setError("Choose a file to upload.");
      return;
    }
    try {
      await upload.mutateAsync({ file, evidence_type: evidenceType, description: description || undefined });
      setFile(null);
      setDescription("");
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Please try again.");
    }
  }

  return (
    <div>
      {isLoading && <LoadingState label="Loading evidence..." />}

      <div className="space-y-2 mb-4">
        {evidence && evidence.length === 0 && (
          <p className="text-slate-500 text-sm">No evidence uploaded yet for this challenge.</p>
        )}
        {evidence?.map((item) => (
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
                href={getCtfEvidenceFileUrl(item.id)}
                target="_blank"
                rel="noreferrer"
                className="text-accent-400 hover:underline text-sm"
              >
                Download
              </a>
              <button
                onClick={() => remove.mutate(item.id)}
                className="text-slate-500 hover:text-status-danger text-sm"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        {error && <AlertBanner message={error} />}
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="label" htmlFor="ctf-evidence-file">
              File
            </label>
            <input
              id="ctf-evidence-file"
              ref={fileInputRef}
              type="file"
              className="text-sm text-slate-400"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
          <div>
            <label className="label" htmlFor="ctf-evidence-type">
              Type
            </label>
            <select
              id="ctf-evidence-type"
              className="input-field"
              value={evidenceType}
              onChange={(e) => setEvidenceType(e.target.value as EvidenceType)}
            >
              {EVIDENCE_TYPES.map((type) => (
                <option key={type} value={type}>
                  {EVIDENCE_TYPE_LABELS[type]}
                </option>
              ))}
            </select>
          </div>
          <Button type="submit" disabled={upload.isPending}>
            {upload.isPending ? "Uploading..." : "Upload"}
          </Button>
        </div>
        <input
          className="input-field"
          placeholder="Short description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <p className="text-xs text-slate-500">
          Never upload real credentials, private keys, or personal data. Files are validated server-side.
        </p>
      </form>
    </div>
  );
}
