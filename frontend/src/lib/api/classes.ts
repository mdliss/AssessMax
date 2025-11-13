import { apiGet } from './client';

export interface ClassInfo {
  class_id: string;
  student_count: number;
}

export interface ClassListResponse {
  classes: ClassInfo[];
  total: number;
}

export async function getClasses(): Promise<ClassListResponse> {
  return apiGet<ClassListResponse>('/v1/classes');
}
