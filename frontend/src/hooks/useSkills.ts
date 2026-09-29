import { useQuery } from "@tanstack/react-query";
import { skillsApi } from "../api/skills";

export function useSkills() {
  return useQuery({
    queryKey: ["skills"],
    queryFn: () => skillsApi.list(),
  });
}

export function useSkill(id: string | undefined) {
  return useQuery({
    queryKey: ["skills", id],
    queryFn: () => skillsApi.get(id as string),
    enabled: Boolean(id),
  });
}
