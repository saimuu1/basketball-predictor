export interface UpcomingGame {
  game_id: string;
  game_date: string;
  team_a_id: string;
  team_b_id: string;
  team_a_name: string;
  team_b_name: string;
  home_team_id?: string | null;
  team_a_logo?: string | null;
  team_b_logo?: string | null;
}

export interface PastGame {
  game_id: string;
  game_date: string;
  team_a_id: string;
  team_b_id: string;
  team_a_name: string;
  team_b_name: string;
  home_team_id?: string | null;
  team_a_score: number;
  team_b_score: number;
  status: string;
  team_a_logo?: string | null;
  team_b_logo?: string | null;
}

export interface PredictRequest {
  game_id?: string;
  game_date?: string;
  team_a_id: string;
  team_b_id: string;
  team_a_name: string;
  team_b_name: string;
  home_team_id?: string | null;
}

export interface Factor {
  name: string;
  value: number;
  impact: 'team_a' | 'team_b' | 'neutral';
  description: string;
}

export interface PredictResponse {
  predicted_winner: string;
  team_a_win_probability: number;
  team_b_win_probability: number;
  confidence: number;
  summary: string;
  factors: Factor[];
  model_used: 'trained_model' | 'fallback';
}
