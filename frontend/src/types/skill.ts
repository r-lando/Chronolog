export interface Skill {
  id: string;
  name: string;
  category: string | null;
  description: string | null;
}

export interface SkillWithStats extends Skill {
  lab_count: number;
  last_practiced: string | null;
}

export interface LabSummary {
  id: string;
  title: string;
  category: string;
  difficulty: string;
  status: string;
  date_completed: string | null;
}

export interface NameId {
  id: string;
  name: string;
}

export interface SkillDetail extends SkillWithStats {
  related_labs: LabSummary[];
  related_tools: NameId[];
}
