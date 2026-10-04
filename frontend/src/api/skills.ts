import { api } from "./client";
import type { SkillDetail, SkillWithStats } from "../types/skill";

export const skillsApi = {
  list: () => api.get<SkillWithStats[]>("/skills"),
  get: (id: string) => api.get<SkillDetail>(`/skills/${id}`),
};
