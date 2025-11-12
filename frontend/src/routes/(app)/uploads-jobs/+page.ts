import type { PageLoad } from './$types';
import { apiGet } from '$lib/api/client';

type JobStatus =
  | 'queued'
  | 'running'
  | 'normalizing'
  | 'normalized'
  | 'scoring'
  | 'aggregating'
  | 'processing'
  | 'completed'
  | 'succeeded'
  | 'failed'
  | 'cancelled';

interface JobSummaryResponse {
  job_id: string;
  status: JobStatus | string;
  class_id: string;
  date: string;
  started_at: string;
  ended_at?: string | null;
  error?: string;
}

interface JobListResponse {
  jobs: JobSummaryResponse[];
  total: number;
  page: number;
  page_size: number;
}

interface JobDetailResponse {
  job_id: string;
  status: JobStatus | string;
  class_id: string;
  date: string;
  input_keys: string[];
  output_keys: string[];
  error?: string;
  metadata?: Record<string, unknown>;
  started_at: string;
  ended_at?: string | null;
  created_at: string;
  duration_seconds?: number | null;
}

interface DisplayJob {
  job_id: string;
  status: JobStatus;
  class_id: string;
  file_name: string;
  created_at: string;
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
  error: string | null;
}

interface JobStats {
  jobsToday: number;
  successRate: number;
  medianDuration: number;
  activeBatches: number;
}

function toStatus(value: string): JobStatus {
  const normalized = value.toLowerCase() as JobStatus;
  return normalized;
}

function deriveFileName(detail?: JobDetailResponse | null): string {
  if (!detail) {
    return 'Session upload';
  }

  const metadata = detail.metadata ?? {};
  const metaFileName =
    (metadata.file_name as string | undefined) ??
    (metadata.filename as string | undefined) ??
    (metadata.original_filename as string | undefined);
  if (metaFileName) {
    return metaFileName;
  }

  const key =
    detail.input_keys?.[0] ??
    detail.output_keys?.[0] ??
    '';
  if (!key) {
    return `${detail.class_id} batch`;
  }

  const parts = key.split('/');
  return parts[parts.length - 1] || `${detail.class_id} batch`;
}

function computeStats(jobs: DisplayJob[]): JobStats {
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  const jobsToday = jobs.filter(
    (job) => new Date(job.created_at).getTime() >= startOfToday.getTime()
  ).length;

  const completedStatuses: JobStatus[] = ['completed', 'succeeded'];
  const failedStatuses: JobStatus[] = ['failed'];
  const activeStatuses: JobStatus[] = [
    'processing',
    'running',
    'queued',
    'normalizing',
    'normalized',
    'scoring',
    'aggregating'
  ];

  const completed = jobs.filter((job) => completedStatuses.includes(job.status)).length;
  const failed = jobs.filter((job) => failedStatuses.includes(job.status)).length;
  const denominator = completed + failed;
  const successRate = denominator === 0 ? 0 : (completed / denominator) * 100;

  const durations = jobs
    .map((job) => job.duration_ms)
    .filter((value): value is number => value !== null)
    .sort((a, b) => a - b);

  let medianDuration = 0;
  if (durations.length === 1) {
    medianDuration = durations[0];
  } else if (durations.length > 1) {
    const middle = Math.floor(durations.length / 2);
    medianDuration =
      durations.length % 2 === 0
        ? (durations[middle - 1] + durations[middle]) / 2
        : durations[middle];
  }

  const activeBatches = jobs.filter((job) => activeStatuses.includes(job.status)).length;

  return {
    jobsToday,
    successRate: Number(successRate.toFixed(1)),
    medianDuration,
    activeBatches
  };
}

export const load: PageLoad = async ({ depends }) => {
  depends('assessmax:uploads-jobs');

  try {
    const list = await apiGet<JobListResponse>('/v1/admin/jobs', { useCache: false });

    const jobs = await Promise.all(
      list.jobs.map(async (summary) => {
        let detail: JobDetailResponse | null = null;
        try {
          detail = await apiGet<JobDetailResponse>(`/v1/admin/jobs/${summary.job_id}`, {
            useCache: false
          });
        } catch {
          detail = null;
        }

        const createdAt = detail?.created_at ?? summary.started_at;
        const startedAt = detail?.started_at ?? summary.started_at;
        const completedAt = detail?.ended_at ?? summary.ended_at ?? null;
        const durationMs =
          detail?.duration_seconds != null
            ? detail.duration_seconds * 1000
            : completedAt
            ? new Date(completedAt).getTime() - new Date(startedAt).getTime()
            : null;

        return {
          job_id: summary.job_id,
          status: toStatus((detail?.status ?? summary.status) as string),
          class_id: detail?.class_id ?? summary.class_id,
          file_name: deriveFileName(detail),
          created_at: createdAt,
          started_at: startedAt,
          completed_at: completedAt,
          duration_ms: durationMs,
          error: detail?.error ?? summary.error ?? null
        } satisfies DisplayJob;
      })
    );

    jobs.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

    const stats = computeStats(jobs);

    return {
      jobs,
      stats
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unable to load job data.';
    return {
      jobs: [] as DisplayJob[],
      stats: {
        jobsToday: 0,
        successRate: 0,
        medianDuration: 0,
        activeBatches: 0
      } satisfies JobStats,
      error: message
    };
  }
};
