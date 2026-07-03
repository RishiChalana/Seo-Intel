// TypeScript mirror of the backend Pydantic schema (app/core/schemas.py and
// app/core/usage.py). Keep in sync with the API contract.

export type SearchIntent =
  | "informational"
  | "commercial"
  | "transactional"
  | "navigational";

export interface KeywordCluster {
  primary_keyword: string;
  related_keywords: string[];
  intent: SearchIntent;
  est_difficulty: number | null;
}

export interface OutlineSection {
  heading: string;
  level: number; // 1=H1, 2=H2, 3=H3
  talking_points: string[];
  target_keywords: string[];
}

export interface ContentOutline {
  title: string;
  meta_description: string;
  sections: OutlineSection[];
  estimated_word_count: number;
  content_gaps_addressed: string[];
}

export interface BriefScore {
  keyword_coverage: number; // 0..1
  structure_completeness: number; // 0..1
  readability_grade: number; // Flesch-Kincaid grade level
  eeat_signal_score: number; // 0..1
  overall: number; // 0..1
  notes: string[];
}

export interface StepUsage {
  label: string;
  calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
}

export interface TokenUsage {
  total_calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  by_step: StepUsage[];
}

export interface ContentBrief {
  topic: string;
  keyword_clusters: KeywordCluster[];
  competitor_pages_analyzed: number;
  outline: ContentOutline;
  score: BriefScore;
  usage: TokenUsage;
}

export interface PipelineRequest {
  topic: string;
  target_audience?: string | null;
  max_competitors: number;
}
