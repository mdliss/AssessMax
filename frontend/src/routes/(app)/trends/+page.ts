import type { PageLoad } from './$types';
import { getAssessmentHistory, getClassDashboard } from '$lib/api/assessments';

const DEFAULT_CLASS_ID = 'MS-7A';

export const load: PageLoad = async ({ url, depends }) => {
  depends('assessmax:trends');

  const modeParam = url.searchParams.get('mode');
  const mode = modeParam === 'student' ? 'student' : 'class';

  const classId = url.searchParams.get('class') ?? DEFAULT_CLASS_ID;
  const requestedStudentId = url.searchParams.get('student') ?? '';

  const errors: string[] = [];

  let classStudents: Array<{ student_id: string; name: string | null }> = [];
  let classHistories: Awaited<ReturnType<typeof getAssessmentHistory>>[] = [];
  let selectedStudentHistory: Awaited<ReturnType<typeof getAssessmentHistory>> | null = null;

  try {
    const dashboard = await getClassDashboard(classId);
    classStudents = dashboard.students.map((student) => ({
      student_id: student.student_id,
      name: student.name,
    }));

    if (mode === 'class' && classStudents.length > 0) {
      const historyResults = await Promise.all(
        classStudents.map(async (student) => {
          try {
            return await getAssessmentHistory(student.student_id);
          } catch (err) {
            const message =
              err instanceof Error ? err.message : `Unable to load history for ${student.student_id}`;
            errors.push(message);
            return null;
          }
        })
      );
      classHistories = historyResults.filter(
        (history): history is Awaited<ReturnType<typeof getAssessmentHistory>>
        => history !== null
      );
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unable to load class roster.';
    errors.push(message);
  }

  const fallbackStudentId =
    mode === 'student' && requestedStudentId === '' && classStudents.length > 0
      ? classStudents[0].student_id
      : requestedStudentId;

  if (fallbackStudentId) {
    try {
      selectedStudentHistory = await getAssessmentHistory(fallbackStudentId);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : `Unable to load student history for ${fallbackStudentId}.`;
      errors.push(message);
    }
  }

  return {
    initialMode: mode,
    initialClassId: classId,
    initialStudentId: fallbackStudentId,
    classStudents,
    classHistories,
    selectedStudentHistory,
    loadErrors: errors,
  };
};
