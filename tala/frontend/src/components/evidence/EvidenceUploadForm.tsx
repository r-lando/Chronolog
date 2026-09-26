import { useRef, useState, type FormEvent } from "react";
import { useUploadEvidence } from "../../hooks/useEvidence";
import { EVIDENCE_TYPE_LABELS, type EvidenceType, type Finding } from "../../types/evidence";
import { Button } from "../ui/Button";
import { AlertBanner } from "../ui/AlertBanner";
import { ApiError } from "../../api/client";

const EVIDENCE_TYPES = Object.keys(EVIDENCE_TYPE_LABELS) as EvidenceType[];

export function EvidenceUploadForm({ labId, findings }: { labId: string; findings: Finding[] }) {
  const upload = useUploadEvidence(labId);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [evidenceType, setEvidenceType] = useState<EvidenceType>("screenshot");
  const [description, setDescription] = useState("");
  const [findingId, setFindingId] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!file) {
      setError("Choose a file to upload.");
      return;
    }
    try {
      await upload.mutateAsync({
        file,
        evidence_type: evidenceType,
        description: description || undefined,
        finding_id: findingId || undefined,
      });
      setFile(null);
      setDescription("");
      setFindingId("");
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Please try again.");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {error && <AlertBanner message={error} />}

      <div className="flex flex-wrap gap-3 items-end">
        <div>
          <label className="label" htmlFor="evidence-file-input">
            File
          </label>
          <input
            id="evidence-file-input"
            ref={fileInputRef}
            type="file"
            className="text-sm text-slate-400"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>

        <div>
          <label className="label" htmlFor="evidence-type-select">
            Type
          </label>
          <select
            id="evidence-type-select"
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

        {findings.length > 0 && (
          <div>
            <label className="label" htmlFor="evidence-finding-select">
              Related finding (optional)
            </label>
            <select
              id="evidence-finding-select"
              className="input-field"
              value={findingId}
              onChange={(e) => setFindingId(e.target.value)}
            >
              <option value="">None</option>
              {findings.map((finding) => (
                <option key={finding.id} value={finding.id}>
                  {finding.title}
                </option>
              ))}
            </select>
          </div>
        )}

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
        Allowed types: images (png/jpg/gif), logs/text (.log/.txt/.md/.json/.yaml/.csv/.xml), PCAP, PDF.
        Max size is set by the server. Never upload real credentials, private keys, or personal data.
      </p>
    </form>
  );
}
