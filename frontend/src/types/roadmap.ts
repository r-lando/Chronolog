import type { LabSummary } from "./skill";

export interface LearningGoal {
  id: string;
  title: string;
  parent_goal_id: string | null;
  related_skill_id: string | null;
  target_notes: string | null;
  created_at: string;
}

export interface LearningGoalTreeNode extends LearningGoal {
  children: LearningGoalTreeNode[];
}

export interface CtfChallengeSummary {
  id: string;
  title: string;
  status: string;
  category: string;
}

export interface LearningGoalProgress {
  goal_id: string;
  has_related_skill: boolean;
  labs_completed: number;
  related_labs: LabSummary[];
  related_ctf_challenges: CtfChallengeSummary[];
  recommended_next_activity: string;
  child_count: number;
  children_with_activity: number;
}
