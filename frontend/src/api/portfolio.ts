import { api } from "./client";
import type { PublicLab, PublicLabSummary } from "../types/portfolio";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const portfolioApi = {
  list: () => api.get<PublicLabSummary[]>("/public/portfolio"),
  get: (slug: string) => api.get<PublicLab>(`/public/portfolio/${slug}`),
};

/**
 * Built from the evidence id rather than the `file_url` the API returns
 * (which is a server-relative path like "/api/v1/public/evidence/{id}/file") —
 * prepending our already-"/api/v1"-suffixed API_BASE_URL to that would
 * duplicate the prefix. Simpler to just construct it directly.
 */
export function getPublicEvidenceFileUrl(evidenceId: string): string {
  return `${API_BASE_URL}/public/evidence/${evidenceId}/file`;
}
