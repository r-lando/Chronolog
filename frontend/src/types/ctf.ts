import type { Skill } from "./skill";
import type { Tool } from "./tool";
import type { LabTechnique } from "./mitre";

export interface CtfEvent {
  id: string;
  name: string;
  platform: string | null;
  event_date: string | null;
  created_at: string;
}

export interface CtfChallenge {
  id: string;
  ctf_event_id: string;
  title: string;
  category: string;
  difficulty: string;
  status: "Solved" | "Partially Solved" | "Unsolved";
  time_spent_minutes: number | null;
  description: string | null;
  solution_writeup: string | null;
  lessons_learned: string | null;
  created_at: string;
  updated_at: string;
  skills: Skill[];
  tools: Tool[];
  techniques: LabTechnique[];
}

export interface CtfEventDetail extends CtfEvent {
  challenges: CtfChallenge[];
}

export interface CtfOptions {
  categories: string[];
  difficulties: string[];
  statuses: string[];
}

export interface CtfChallengeFormValues {
  title: string;
  category: string;
  difficulty: string;
  status: string;
  time_spent_minutes: string;
  description: string;
  solution_writeup: string;
  lessons_learned: string;
}
