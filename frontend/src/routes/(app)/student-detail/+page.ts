import type { PageLoad } from './$types';

export const load: PageLoad = async ({ url }) => ({
  initialStudentId: url.searchParams.get('id'),
  initialClassId: url.searchParams.get('class')
});
