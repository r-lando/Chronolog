import { useQuery } from "@tanstack/react-query";
import { toolsApi } from "../api/tools";

export function useTools() {
  return useQuery({
    queryKey: ["tools"],
    queryFn: () => toolsApi.list(),
  });
}

export function useTool(id: string | undefined) {
  return useQuery({
    queryKey: ["tools", id],
    queryFn: () => toolsApi.get(id as string),
    enabled: Boolean(id),
  });
}
