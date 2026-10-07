import { useQuery } from "@tanstack/react-query";
import { mitreApi } from "../api/mitre";

export function useMitreTechniques() {
  return useQuery({
    queryKey: ["mitre-techniques"],
    queryFn: () => mitreApi.list(),
  });
}

export function useMitreTechnique(id: string | undefined) {
  return useQuery({
    queryKey: ["mitre-techniques", id],
    queryFn: () => mitreApi.get(id as string),
    enabled: Boolean(id),
  });
}
