export type SearchResultType = "lab" | "ctf_challenge" | "skill" | "tool" | "mitre_technique" | "tag" | "finding";

export interface SearchResultItem {
  id: string;
  type: SearchResultType;
  title: string;
  subtitle: string | null;
  url: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
}
