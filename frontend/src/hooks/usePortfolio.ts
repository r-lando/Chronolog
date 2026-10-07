import { useQuery } from "@tanstack/react-query";
import { portfolioApi } from "../api/portfolio";

export function usePublicPortfolio() {
  return useQuery({ queryKey: ["public-portfolio"], queryFn: () => portfolioApi.list() });
}

export function usePublicLab(slug: string | undefined) {
  return useQuery({
    queryKey: ["public-portfolio", slug],
    queryFn: () => portfolioApi.get(slug as string),
    enabled: Boolean(slug),
    retry: false, // a 404 here means "not published" — retrying won't help
  });
}
