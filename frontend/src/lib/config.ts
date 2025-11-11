export const API_BASE_URL = import.meta.env.PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
export const API_TIMEOUT = 30_000;
export const CACHE_TTL_MS = 5 * 60 * 1000; // five minutes to mirror Streamlit cache behaviour
export const STORAGE_KEYS = {
  token: 'assessmax.auth.token',
  user: 'assessmax.auth.user'
} as const;

export const ROUTES = {
  login: '/login',
  classOverview: '/class-overview',
  studentDetail: '/student-detail',
  trends: '/trends',
  uploadsJobs: '/uploads-jobs'
} as const;
