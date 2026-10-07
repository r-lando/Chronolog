from pydantic import BaseModel


class SearchResultItem(BaseModel):
    id: str
    type: str  # "lab" | "ctf_challenge" | "skill" | "tool" | "mitre_technique" | "tag" | "finding"
    title: str
    subtitle: str | None = None
    url: str  # frontend route to navigate to on click


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
