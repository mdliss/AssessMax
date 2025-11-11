import type { PageLoad } from './$types';

export const load: PageLoad = async ({ url }) => {
  return {
    initialStudentId: url.searchParams.get('id')
  };
};
