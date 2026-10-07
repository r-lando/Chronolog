import { api } from "./client";
import type { ChartPoint, Overview, RecentActivity } from "../types/stats";

export const statsApi = {
  overview: () => api.get<Overview>("/stats/overview"),
  labsByCategory: () => api.get<ChartPoint[]>("/stats/labs-by-category"),
  difficultyDistribution: () => api.get<ChartPoint[]>("/stats/difficulty-distribution"),
  activityTimeline: () => api.get<ChartPoint[]>("/stats/activity-timeline"),
  skillsPracticed: () => api.get<ChartPoint[]>("/stats/skills-practiced"),
  toolsUsed: () => api.get<ChartPoint[]>("/stats/tools-used"),
  mitreCoverage: () => api.get<ChartPoint[]>("/stats/mitre-coverage"),
  recent: () => api.get<RecentActivity>("/stats/recent"),
};
