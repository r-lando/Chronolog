import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { labsApi, type LabPayload } from "../api/labs";
import type { LabFilters, LabWriteupUpdatePayload } from "../types/lab";

const LABS_KEY = "labs";

export function useLabs(filters: LabFilters = {}) {
  return useQuery({
    queryKey: [LABS_KEY, filters],
    queryFn: () => labsApi.list(filters),
  });
}

export function useLab(id: string | undefined) {
  return useQuery({
    queryKey: [LABS_KEY, id],
    queryFn: () => labsApi.get(id as string),
    enabled: Boolean(id),
  });
}

export function useLabOptions() {
  return useQuery({
    queryKey: [LABS_KEY, "options"],
    queryFn: () => labsApi.getOptions(),
    staleTime: Infinity, // controlled vocabulary, effectively static
  });
}

export function useCreateLab() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: LabPayload) => labsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [LABS_KEY] });
    },
  });
}

export function useUpdateLab(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: LabPayload) => labsApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [LABS_KEY] });
    },
  });
}

export function useUpdateLabStatus(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (status: string) => labsApi.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [LABS_KEY] });
    },
  });
}

export function useDeleteLab() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => labsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [LABS_KEY] });
    },
  });
}

export function useUpdateWriteup(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: LabWriteupUpdatePayload) => labsApi.updateWriteup(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [LABS_KEY, id] });
    },
  });
}

export function useAddTag(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => labsApi.addTag(id, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [LABS_KEY, id] });
    },
  });
}

export function useRemoveTag(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (tagId: string) => labsApi.removeTag(id, tagId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [LABS_KEY, id] });
    },
  });
}
