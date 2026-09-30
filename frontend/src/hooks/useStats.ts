import { useQuery } from "@tanstack/react-query";
import { statsApi } from "../api/stats";

const STATS_KEY = "stats";

export function useOverview() {
  return useQuery({ queryKey: [STATS_KEY, "overview"], queryFn: () => statsApi.overview() });
}

export function useLabsByCategory() {
  return useQuery({ queryKey: [STATS_KEY, "labs-by-category"], queryFn: () => statsApi.labsByCategory() });
}

export function useDifficultyDistribution() {
  return useQuery({
    queryKey: [STATS_KEY, "difficulty-distribution"],
    queryFn: () => statsApi.difficultyDistribution(),
  });
}

export function useActivityTimeline() {
  return useQuery({ queryKey: [STATS_KEY, "activity-timeline"], queryFn: () => statsApi.activityTimeline() });
}

export function useSkillsPracticed() {
  return useQuery({ queryKey: [STATS_KEY, "skills-practiced"], queryFn: () => statsApi.skillsPracticed() });
}

export function useToolsUsed() {
  return useQuery({ queryKey: [STATS_KEY, "tools-used"], queryFn: () => statsApi.toolsUsed() });
}

export function useMitreCoverage() {
  return useQuery({ queryKey: [STATS_KEY, "mitre-coverage"], queryFn: () => statsApi.mitreCoverage() });
}

export function useRecentActivity() {
  return useQuery({ queryKey: [STATS_KEY, "recent"], queryFn: () => statsApi.recent() });
}
