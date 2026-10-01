import { api } from "./client";
import type { CtfChallenge, CtfEvent, CtfEventDetail, CtfOptions } from "../types/ctf";
import type { Skill } from "../types/skill";
import type { Tool } from "../types/tool";
import type { LabTechnique } from "../types/mitre";

export interface CtfEventPayload {
  name: string;
  platform: string | null;
  event_date: string | null;
}

export interface CtfChallengePayload {
  title: string;
  category: string;
  difficulty: string;
  status: string;
  time_spent_minutes: number | null;
  description: string | null;
  solution_writeup: string | null;
  lessons_learned: string | null;
}

export const ctfApi = {
  getOptions: () => api.get<CtfOptions>("/ctf-options"),

  listEvents: () => api.get<CtfEvent[]>("/ctf-events"),
  getEvent: (id: string) => api.get<CtfEventDetail>(`/ctf-events/${id}`),
  createEvent: (payload: CtfEventPayload) => api.post<CtfEvent>("/ctf-events", payload),
  deleteEvent: (id: string) => api.delete<void>(`/ctf-events/${id}`),

  createChallenge: (eventId: string, payload: CtfChallengePayload) =>
    api.post<CtfChallenge>(`/ctf-events/${eventId}/challenges`, payload),
  getChallenge: (id: string) => api.get<CtfChallenge>(`/ctf-challenges/${id}`),
  updateChallenge: (id: string, payload: CtfChallengePayload) =>
    api.put<CtfChallenge>(`/ctf-challenges/${id}`, payload),
  deleteChallenge: (id: string) => api.delete<void>(`/ctf-challenges/${id}`),

  addSkill: (id: string, name: string) => api.post<Skill[]>(`/ctf-challenges/${id}/skills`, { name }),
  removeSkill: (id: string, skillId: string) => api.delete<Skill[]>(`/ctf-challenges/${id}/skills/${skillId}`),
  addTool: (id: string, name: string) => api.post<Tool[]>(`/ctf-challenges/${id}/tools`, { name }),
  removeTool: (id: string, toolId: string) => api.delete<Tool[]>(`/ctf-challenges/${id}/tools/${toolId}`),
  addTechnique: (id: string, techniqueId: string, justification: string) =>
    api.post<LabTechnique[]>(`/ctf-challenges/${id}/techniques`, {
      technique_id: techniqueId,
      justification,
    }),
  removeTechnique: (id: string, techniqueId: string) =>
    api.delete<LabTechnique[]>(`/ctf-challenges/${id}/techniques/${techniqueId}`),
};
