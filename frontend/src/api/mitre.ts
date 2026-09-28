import { api } from "./client";
import type { MitreTechniqueDetail, MitreTechniqueWithStats } from "../types/mitre";

export const mitreApi = {
  list: () => api.get<MitreTechniqueWithStats[]>("/mitre-techniques"),
  get: (id: string) => api.get<MitreTechniqueDetail>(`/mitre-techniques/${id}`),
};
