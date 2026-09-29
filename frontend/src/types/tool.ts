import type { LabSummary, NameId } from "./skill";

export interface Tool {
  id: string;
  name: string;
  category: string | null;
  description: string | null;
}

export interface ToolWithStats extends Tool {
  lab_count: number;
  last_used: string | null;
}

export interface ToolDetail extends ToolWithStats {
  related_labs: LabSummary[];
  related_skills: NameId[];
  related_techniques: { id: string; technique_id: string; name: string }[];
}
