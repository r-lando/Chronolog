import { api } from "./client";
import type { LearningGoal, LearningGoalProgress } from "../types/roadmap";

export interface LearningGoalPayload {
  title: string;
  parent_goal_id: string | null;
  related_skill_id: string | null;
  target_notes: string | null;
}

export const roadmapApi = {
  list: () => api.get<LearningGoal[]>("/learning-goals"),
  create: (payload: LearningGoalPayload) => api.post<LearningGoal>("/learning-goals", payload),
  update: (id: string, payload: LearningGoalPayload) => api.put<LearningGoal>(`/learning-goals/${id}`, payload),
  delete: (id: string) => api.delete<void>(`/learning-goals/${id}`),
  getProgress: (id: string) => api.get<LearningGoalProgress>(`/learning-goals/${id}/progress`),
};
