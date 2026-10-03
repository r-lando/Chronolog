import { api, ApiError } from "./client";
import type { Evidence } from "../types/evidence";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export interface CtfEvidence extends Omit<Evidence, "lab_id" | "finding_id"> {
  ctf_challenge_id: string;
}

export interface UploadCtfEvidencePayload {
  file: File;
  evidence_type: string;
  description?: string;
}

async function uploadCtfEvidence(challengeId: string, payload: UploadCtfEvidencePayload): Promise<CtfEvidence> {
  const formData = new FormData();
  formData.append("file", payload.file);
  formData.append("evidence_type", payload.evidence_type);
  if (payload.description) formData.append("description", payload.description);

  // Not using the shared JSON `api` client: multipart uploads need the
  // browser to set its own Content-Type (with the boundary).
  const response = await fetch(`${API_BASE_URL}/ctf-challenges/${challengeId}/evidence`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });

  if (!response.ok) {
    let detail = "Upload failed. Please try again.";
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // no JSON body
    }
    throw new ApiError(response.status, detail);
  }
  return response.json();
}

export function getCtfEvidenceFileUrl(evidenceId: string): string {
  return `${API_BASE_URL}/ctf-evidence/${evidenceId}/file`;
}

export const ctfEvidenceApi = {
  upload: uploadCtfEvidence,
  list: (challengeId: string) => api.get<CtfEvidence[]>(`/ctf-challenges/${challengeId}/evidence`),
  delete: (id: string) => api.delete<void>(`/ctf-evidence/${id}`),
};
