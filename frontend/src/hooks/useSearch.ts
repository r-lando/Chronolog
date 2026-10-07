import { useQuery } from "@tanstack/react-query";
import { searchApi } from "../api/search";

export function useSearch(query: string) {
  return useQuery({
    queryKey: ["search", query],
    queryFn: () => searchApi.search(query),
    enabled: query.trim().length > 0,
  });
}
