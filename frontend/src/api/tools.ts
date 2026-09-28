import { api } from "./client";
import type { ToolDetail, ToolWithStats } from "../types/tool";

export const toolsApi = {
  list: () => api.get<ToolWithStats[]>("/tools"),
  get: (id: string) => api.get<ToolDetail>(`/tools/${id}`),
};
