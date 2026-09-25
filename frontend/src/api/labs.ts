import { api } from "./client";
import type {
  Lab,
  LabDetail,
  LabFilters,
  LabOptions,
  LabWriteup,
  LabWriteupUpdatePayload,
  Tag,
} from "../types/lab";

function buildQueryString(filters: LabFilters): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

export interface LabPayload {
  title: string;
  platform: string | null;
  category: string;
  difficulty: string;
  status: string;
  date_started: string | null;
  date_completed: string | null;
  time_spent_minutes: number | null;
  description: string | null;
  objective: string | null;
  environment: string | null;
}

export const labsApi = {
  list: (filters: LabFilters = {}) => api.get<Lab[]>(`/labs${buildQueryString(filters)}`),
  get: (id: string) => api.get<LabDetail>(`/labs/${id}`),
  create: (payload: LabPayload) => api.post<LabDetail>("/labs", payload),
  update: (id: string, payload: LabPayload) => api.put<LabDetail>(`/labs/${id}`, payload),
  updateStatus: (id: string, status: string) => api.patch<Lab>(`/labs/${id}/status`, { status }),
  delete: (id: string) => api.delete<void>(`/labs/${id}`),
  updateWriteup: (id: string, payload: LabWriteupUpdatePayload) =>
    api.put<LabWriteup>(`/labs/${id}/writeup`, payload),
  addTag: (id: string, name: string) => api.post<Tag[]>(`/labs/${id}/tags`, { name }),
  removeTag: (id: string, tagId: string) => api.delete<Tag[]>(`/labs/${id}/tags/${tagId}`),
  getOptions: () => api.get<LabOptions>("/labs/options"),
};
