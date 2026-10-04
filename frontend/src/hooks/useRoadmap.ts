import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { roadmapApi, type LearningGoalPayload } from "../api/roadmap";

const ROADMAP_KEY = "learning-goals";

export function useLearningGoals() {
  return useQuery({ queryKey: [ROADMAP_KEY], queryFn: () => roadmapApi.list() });
}

export function useGoalProgress(id: string | undefined) {
  return useQuery({
    queryKey: [ROADMAP_KEY, "progress", id],
    queryFn: () => roadmapApi.getProgress(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: LearningGoalPayload) => roadmapApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [ROADMAP_KEY] }),
  });
}

export function useUpdateGoal(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: LearningGoalPayload) => roadmapApi.update(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [ROADMAP_KEY] }),
  });
}

export function useDeleteGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => roadmapApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [ROADMAP_KEY] }),
  });
}
