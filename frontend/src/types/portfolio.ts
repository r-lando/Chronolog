export interface PublicLabSummary {
  slug: string;
  title: string;
  category: string;
  difficulty: string;
  platform: string | null;
  summary: string | null;
  published_at: string;
}

export interface PublicTechnique {
  technique_id: string;
  sub_technique_id: string | null;
  name: string;
  tactic: string;
  justification: string;
}

export interface PublicEvidence {
  id: string;
  evidence_type: string;
  original_filename: string;
  description: string | null;
  file_url: string;
}

export interface PublicLab {
  slug: string;
  title: string;
  category: string;
  difficulty: string;
  platform: string | null;
  summary: string | null;
  objective: string | null;
  environment: string | null;
  methodology: string | null;
  findings: string | null;
  analysis: string | null;
  lessons_learned: string | null;
  next_steps: string | null;
  skills: string[];
  tools: string[];
  techniques: PublicTechnique[];
  evidence: PublicEvidence[];
  published_at: string;
}
