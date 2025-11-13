import { apiGet } from './client';

export interface SkillScore {
  skill: string;
  score: number;
  confidence: number;
}

export interface AssessmentResponse {
  assessment_id: string;
  student_id: string;
  class_id: string;
  assessed_on: string;
  model_version: string;
  skills: SkillScore[];
  created_at: string;
}

export interface StudentSummary {
  student_id: string;
  name: string | null;
  class_id: string;
  assessment_count: number;
  latest_assessment: AssessmentResponse | null;
  average_scores: Record<string, number>;
}

export interface ClassMetrics {
  class_id: string;
  student_count: number;
  total_assessments: number;
  date_range: [string, string] | null;
  class_averages: Record<string, number>;
}

export interface ClassDashboardResponse {
  class_id: string;
  metrics: ClassMetrics;
  students: StudentSummary[];
  last_updated: string;
}

export interface EvidenceSpan {
  start: number;
  end: number;
  text: string;
}

export interface EvidenceResponse {
  evidence_id: string;
  assessment_id: string;
  skill: string;
  span_text: string;
  span_location: string;
  rationale: string;
  score_contrib: number | null;
}

export interface AssessmentHistoryResponse {
  student_id: string;
  assessments: AssessmentResponse[];
  total: number;
}

/**
 * Get latest assessment for a student
 */
export async function getLatestAssessment(studentId: string): Promise<AssessmentResponse> {
  return apiGet<AssessmentResponse>(`/v1/assessments/${studentId}`);
}

/**
 * Get assessment history for a student
 */
export async function getAssessmentHistory(studentId: string): Promise<AssessmentHistoryResponse> {
  return apiGet<AssessmentHistoryResponse>(`/v1/assessments/${studentId}/history`);
}

/**
 * Get class dashboard with metrics and student summaries
 */
export async function getClassDashboard(classId: string): Promise<ClassDashboardResponse> {
  return apiGet<ClassDashboardResponse>(`/v1/classes/${classId}/dashboard`);
}

/**
 * Get evidence for a specific assessment
 */
export async function getAssessmentEvidence(assessmentId: string): Promise<EvidenceResponse[]> {
  return apiGet<EvidenceResponse[]>(`/v1/assessments/${assessmentId}/evidence`);
}
