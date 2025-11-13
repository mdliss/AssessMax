export type SkillKey = 'empathy' | 'adaptability' | 'collaboration' | 'communication' | 'self_regulation';

export interface SkillScore {
  skill: SkillKey;
  score: number;
  confidence?: number;
}

export interface ClassMetrics {
  class_id: string;
  student_count: number;
  total_assessments: number;
  date_range: [string, string] | null;
  class_averages: Record<SkillKey, number>;
}

export interface StudentSummary {
  student_id: string;
  name: string;
  assessment_count: number;
  latest_assessment?: {
    assessment_id: string;
    assessed_on: string;
    class_id: string;
  } | null;
  average_scores: Record<SkillKey, number>;
}

export interface ClassDashboardResponse {
  class_id: string;
  metrics: ClassMetrics;
  students: StudentSummary[];
  last_updated: string;
}

export interface AssessmentSummary {
  assessment_id: string;
  model_version: string;
  assessed_on: string;
  class_id: string;
  skills: SkillScore[];
}

export interface SkillTrendPoint {
  assessed_on: string;
  value: number;
}

export interface SkillTrendSeries {
  skill: SkillKey;
  points: SkillTrendPoint[];
}

export interface EvidenceHighlight {
  span_text: string;
  span_location: string;
  rationale: string;
  score_contrib: number;
  skill: SkillKey;
}

export interface EvidenceBySkill {
  skill: SkillKey;
  highlights: EvidenceHighlight[];
}

export interface AssessmentLedgerRow {
  assessment_id: string;
  assessed_on: string;
  class_id: string;
  model_version: string;
  score: number;
}

export interface StudentDetailPayload {
  latest_assessment: AssessmentSummary | null;
  history: AssessmentSummary[];
  evidence: EvidenceBySkill[];
  ledger: AssessmentLedgerRow[];
}

export interface TrendRequestParams {
  class_id?: string;
  student_id?: string;
  window_weeks: 4 | 8 | 12;
  mode: 'class' | 'student';
  smoothing: 'none' | 'simple' | 'ema';
}

export interface TrendResponse {
  summary: Record<string, number>;
  series: SkillTrendSeries[];
}

export interface JobRecord {
  job_id: string;
  class_id: string;
  status: 'pending' | 'running' | 'succeeded' | 'failed';
  started_at: string;
  ended_at?: string;
  error?: string;
}

export interface UploadHistoryBar {
  date: string;
  transcripts: number;
  artifacts: number;
}

export interface JobsDashboardResponse {
  metrics: {
    jobs_today: number;
    success_rate: number;
    median_duration: number;
    active_batches: number;
  };
  jobs: JobRecord[];
  upload_history: UploadHistoryBar[];
}
