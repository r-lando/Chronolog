import { api, ApiError } from "./client";
import type { Evidence, EvidenceUpdatePayload, EvidenceWithLab, Finding } from "../types/evidence";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export interface UploadEvidencePayload {
  file: File;
  evidence_type: string;
  description?: string;
  notes?: string;
  finding_id?: string;
}

async function uploadEvidence(labId: string, payload: UploadEvidencePayload): Promise<Evidence> {
  const formData = new FormData();
  formData.append("file", payload.file);
  formData.append("evidence_type", payload.evidence_type);
  if (payload.description) formData.append("description", payload.description);
  if (payload.notes) formData.append("notes", payload.notes);
  if (payload.finding_id) formData.append("finding_id", payload.finding_id);

  // Deliberately not using the shared `api` client here: it always sets
  // Content-Type: application/json, but a multipart upload needs the
  // browser to set its own Content-Type with the correct boundary.
  const response = await fetch(`${API_BASE_URL}/labs/${labId}/evidence`, {
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

export function getEvidenceFileUrl(evidenceId: string): string {
  return `${API_BASE_URL}/evidence/${evidenceId}/file`;
}

export const evidenceApi = {
  upload: uploadEvidence,
  listForLab: (labId: string) => api.get<Evidence[]>(`/labs/${labId}/evidence`),
  listAll: (evidenceType?: string) =>
    api.get<EvidenceWithLab[]>(`/evidence${evidenceType ? `?evidence_type=${evidenceType}` : ""}`),
  update: (id: string, payload: EvidenceUpdatePayload) => api.patch<Evidence>(`/evidence/${id}`, payload),
  delete: (id: string) => api.delete<void>(`/evidence/${id}`),
};

export const findingsApi = {
  listForLab: (labId: string) => api.get<Finding[]>(`/labs/${labId}/findings`),
  create: (labId: string, payload: { title: string; description?: string; severity?: string }) =>
    api.post<Finding>(`/labs/${labId}/findings`, payload),
  delete: (id: string) => api.delete<void>(`/findings/${id}`),
};
