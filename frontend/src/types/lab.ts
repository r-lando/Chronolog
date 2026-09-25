export interface Tag {
  id: string;
  name: string;
}

export interface LabWriteup {
  methodology: string | null;
  findings: string | null;
  analysis: string | null;
  lessons_learned: string | null;
  reflection: string | null;
  next_steps: string | null;
  format: string;
  updated_at: string;
}

export interface Lab {
  id: string;
  title: string;
  platform: string | null;
  category: string;
  difficulty: string;
  status: string;
  date_started: string | null;
  date_completed: string | null;
  time_spent_minutes: number | null;
  description: string | null;
  objective: string | null;
  environment: string | null;
  is_portfolio_ready: boolean;
  portfolio_slug: string | null;
  created_at: string;
  updated_at: string;
  tags: Tag[];
}

export interface LabDetail extends Lab {
  writeup: LabWriteup | null;
}

export interface LabFormValues {
  title: string;
  platform: string;
  category: string;
  difficulty: string;
  status: string;
  date_started: string;
  date_completed: string;
  time_spent_minutes: string;
  description: string;
  objective: string;
  environment: string;
}

export interface LabOptions {
  categories: string[];
  difficulties: string[];
  statuses: string[];
}

export interface LabFilters {
  category?: string;
  difficulty?: string;
  status?: string;
  platform?: string;
  tag?: string;
  search?: string;
}

export interface LabWriteupUpdatePayload {
  methodology?: string;
  findings?: string;
  analysis?: string;
  lessons_learned?: string;
  reflection?: string;
  next_steps?: string;
}
