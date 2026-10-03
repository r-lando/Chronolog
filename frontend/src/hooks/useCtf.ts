import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ctfApi, type CtfChallengePayload, type CtfEventPayload } from "../api/ctf";
import { ctfEvidenceApi, type UploadCtfEvidencePayload } from "../api/ctfEvidence";

const CTF_KEY = "ctf";

export function useCtfOptions() {
  return useQuery({
    queryKey: [CTF_KEY, "options"],
    queryFn: () => ctfApi.getOptions(),
    staleTime: Infinity,
  });
}

export function useCtfEvents() {
  return useQuery({ queryKey: [CTF_KEY, "events"], queryFn: () => ctfApi.listEvents() });
}

export function useCtfEvent(id: string | undefined) {
  return useQuery({
    queryKey: [CTF_KEY, "event", id],
    queryFn: () => ctfApi.getEvent(id as string),
    enabled: Boolean(id),
  });
}

export function useCtfChallenge(id: string | undefined) {
  return useQuery({
    queryKey: [CTF_KEY, "challenge", id],
    queryFn: () => ctfApi.getChallenge(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateCtfEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CtfEventPayload) => ctfApi.createEvent(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [CTF_KEY, "events"] }),
  });
}

export function useDeleteCtfEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => ctfApi.deleteEvent(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [CTF_KEY] }),
  });
}

export function useCreateCtfChallenge(eventId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CtfChallengePayload) => ctfApi.createChallenge(eventId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [CTF_KEY, "event", eventId] }),
  });
}

export function useUpdateCtfChallenge(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CtfChallengePayload) => ctfApi.updateChallenge(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [CTF_KEY] }),
  });
}

export function useDeleteCtfChallenge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => ctfApi.deleteChallenge(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [CTF_KEY] }),
  });
}

function useChallengeAttachment<TArg>(id: string, fn: (id: string, arg: TArg) => Promise<unknown>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (arg: TArg) => fn(id, arg),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [CTF_KEY, "challenge", id] }),
  });
}

export const useAddCtfSkill = (id: string) => useChallengeAttachment(id, ctfApi.addSkill);
export const useRemoveCtfSkill = (id: string) => useChallengeAttachment(id, ctfApi.removeSkill);
export const useAddCtfTool = (id: string) => useChallengeAttachment(id, ctfApi.addTool);
export const useRemoveCtfTool = (id: string) => useChallengeAttachment(id, ctfApi.removeTool);
export const useRemoveCtfTechnique = (id: string) => useChallengeAttachment(id, ctfApi.removeTechnique);

export function useAddCtfTechnique(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ techniqueId, justification }: { techniqueId: string; justification: string }) =>
      ctfApi.addTechnique(id, techniqueId, justification),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [CTF_KEY, "challenge", id] }),
  });
}

export function useCtfEvidence(challengeId: string | undefined) {
  return useQuery({
    queryKey: [CTF_KEY, "evidence", challengeId],
    queryFn: () => ctfEvidenceApi.list(challengeId as string),
    enabled: Boolean(challengeId),
  });
}

export function useUploadCtfEvidence(challengeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UploadCtfEvidencePayload) => ctfEvidenceApi.upload(challengeId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [CTF_KEY, "evidence", challengeId] }),
  });
}

export function useDeleteCtfEvidence(challengeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => ctfEvidenceApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [CTF_KEY, "evidence", challengeId] }),
  });
}
