import type { LabSummary } from "./skill";

export interface MitreTechnique {
  id: string;
  technique_id: string;
  sub_technique_id: string | null;
  name: string;
  tactic: string;
  description: string | null;
}

export interface MitreTechniqueWithStats extends MitreTechnique {
  lab_count: number;
  last_practiced: string | null;
}

export interface RelatedLabWithJustification {
  lab: LabSummary;
  justification: string;
}

export interface MitreTechniqueDetail extends MitreTechniqueWithStats {
  related_labs: RelatedLabWithJustification[];
}

export interface LabTechnique {
  technique: MitreTechnique;
  justification: string;
  created_at: string;
}
