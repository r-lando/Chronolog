import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { evidenceApi, findingsApi, type UploadEvidencePayload } from "../api/evidence";

const EVIDENCE_KEY = "evidence";
const FINDINGS_KEY = "findings";

export function useLabEvidence(labId: string | undefined) {
  return useQuery({
    queryKey: [EVIDENCE_KEY, "lab", labId],
    queryFn: () => evidenceApi.listForLab(labId as string),
    enabled: Boolean(labId),
  });
}

export function useAllEvidence(evidenceType?: string) {
  return useQuery({
    queryKey: [EVIDENCE_KEY, "all", evidenceType],
    queryFn: () => evidenceApi.listAll(evidenceType),
  });
}

export function useUploadEvidence(labId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UploadEvidencePayload) => evidenceApi.upload(labId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [EVIDENCE_KEY, "lab", labId] });
      queryClient.invalidateQueries({ queryKey: [EVIDENCE_KEY, "all"] });
    },
  });
}

export function useDeleteEvidence(labId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => evidenceApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [EVIDENCE_KEY, "lab", labId] });
      queryClient.invalidateQueries({ queryKey: [EVIDENCE_KEY, "all"] });
    },
  });
}

export function useLabFindings(labId: string | undefined) {
  return useQuery({
    queryKey: [FINDINGS_KEY, labId],
    queryFn: () => findingsApi.listForLab(labId as string),
    enabled: Boolean(labId),
  });
}

export function useCreateFinding(labId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { title: string; description?: string; severity?: string }) =>
      findingsApi.create(labId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [FINDINGS_KEY, labId] });
    },
  });
}

export function useDeleteFinding(labId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => findingsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [FINDINGS_KEY, labId] });
    },
  });
}
