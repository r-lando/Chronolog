import type { LabSummary } from "./skill";

export interface ChartPoint {
  label: string;
  count: number;
}

export interface Overview {
  labs_completed: number;
  ctf_challenges_solved: number;
  total_learning_hours: number;
  current_streak_days: number;
  skills_practiced: number;
  tools_used: number;
  techniques_practiced: number;
  labs_completed_this_month: number;
  completed_labs_without_date: number;
}

export interface RecentCtfChallenge {
  id: string;
  ctf_event_id: string;
  title: string;
  category: string;
  status: string;
  event_name: string;
  created_at: string;
}

export interface RecentSkill {
  id: string;
  name: string;
  last_practiced: string;
}

export interface RecentActivity {
  recent_labs: LabSummary[];
  recent_ctf_challenges: RecentCtfChallenge[];
  recently_practiced_skills: RecentSkill[];
}
