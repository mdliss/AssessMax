<script lang="ts">
  import type { PageData } from './$types';
  import { invalidateAll } from '$app/navigation';
  import { clearCache } from '$lib/api/client';

  export let data: PageData;

  type TabKey = 'uploads' | 'status' | 'history';
  type StatusFilter = 'all' | 'completed' | 'processing' | 'failed';

  const ACTIVE_STATUSES = new Set([
    'processing',
    'running',
    'queued',
    'normalizing',
    'normalized',
    'scoring',
    'aggregating'
  ]);
  const COMPLETED_STATUSES = new Set(['completed', 'succeeded']);
  const FAILED_STATUSES = new Set(['failed']);

  const dateTimeFormat = new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  });
  const dateFormat = new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });

  let activeTab: TabKey = 'uploads';
  let statusFilter: StatusFilter = 'all';
  let sortDirection: 'desc' | 'asc' = 'desc';
  let refreshing = false;

  let jobs = data.jobs ?? [];
  let stats = data.stats;
  let error: string | null = data.error ?? null;

  $: jobs = data.jobs ?? [];
  $: stats = data.stats;
  $: error = data.error ?? null;

  $: activeJobs = jobs.filter((job) => ACTIVE_STATUSES.has(job.status));
  $: recentUploads = jobs.slice(0, 5);
  $: filteredHistory = filterHistoryJobs();

  const statusLabels: Record<string, string> = {
    completed: 'Completed',
    succeeded: 'Completed',
    processing: 'Processing',
    running: 'Processing',
    queued: 'Queued',
    normalizing: 'Normalizing',
    normalized: 'Normalized',
    scoring: 'Scoring',
    aggregating: 'Aggregating',
    failed: 'Failed',
    cancelled: 'Cancelled'
  };

  const statusBadgeStyles: Record<string, { bg: string; color: string }> = {
    completed: { bg: 'rgba(16, 185, 129, 0.2)', color: '#10B981' },
    succeeded: { bg: 'rgba(16, 185, 129, 0.2)', color: '#10B981' },
    processing: { bg: 'rgba(20, 184, 166, 0.2)', color: '#14b8a6' },
    running: { bg: 'rgba(20, 184, 166, 0.2)', color: '#14b8a6' },
    queued: { bg: 'rgba(59, 130, 246, 0.2)', color: '#3B82F6' },
    normalizing: { bg: 'rgba(20, 184, 166, 0.2)', color: '#14b8a6' },
    normalized: { bg: 'rgba(20, 184, 166, 0.2)', color: '#14b8a6' },
    scoring: { bg: 'rgba(20, 184, 166, 0.2)', color: '#14b8a6' },
    aggregating: { bg: 'rgba(20, 184, 166, 0.2)', color: '#14b8a6' },
    failed: { bg: 'rgba(239, 68, 68, 0.2)', color: '#ef4444' },
    cancelled: { bg: 'rgba(148, 163, 184, 0.2)', color: '#94a3b8' }
  };

  function statusLabel(value: string) {
    return statusLabels[value] ?? value.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }

  function badgeStyle(value: string) {
    const style = statusBadgeStyles[value];
    if (!style) {
      return {
        backgroundColor: 'rgba(148, 163, 184, 0.2)',
        color: '#94a3b8'
      };
    }
    return {
      backgroundColor: style.bg,
      color: style.color
    };
  }

  function filterHistoryJobs() {
    let filtered = jobs;

    if (statusFilter === 'completed') {
      filtered = jobs.filter((job) => COMPLETED_STATUSES.has(job.status));
    } else if (statusFilter === 'processing') {
      filtered = jobs.filter((job) => ACTIVE_STATUSES.has(job.status));
    } else if (statusFilter === 'failed') {
      filtered = jobs.filter((job) => FAILED_STATUSES.has(job.status));
    }

    const sorted = [...filtered].sort((a, b) => {
      const delta =
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      return sortDirection === 'desc' ? -delta : delta;
    });

    return sorted;
  }

  function formatDateTime(value: string | null) {
    return value ? dateTimeFormat.format(new Date(value)) : '—';
  }

  function formatDate(value: string | null) {
    return value ? dateFormat.format(new Date(value)) : '—';
  }

  function formatDurationMs(value: number | null) {
    if (value === null || Number.isNaN(value)) return '—';
    const totalSeconds = Math.max(0, Math.round(value / 1000));
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    if (minutes === 0) {
      return `${seconds}s`;
    }
    return `${minutes}m ${seconds.toString().padStart(2, '0')}s`;
  }

  function successRateDisplay() {
    if (stats.successRate === null || Number.isNaN(stats.successRate)) {
      return '—';
    }
    return `${stats.successRate.toFixed(1)}%`;
  }

  function medianDurationDisplay() {
    return formatDurationMs(stats.medianDuration);
  }

  async function refreshJobs() {
    refreshing = true;
    clearCache('GET:/v1/admin/jobs');
    try {
      await invalidateAll();
    } finally {
      refreshing = false;
    }
  }
</script>

<svelte:head>
  <title>Uploads & Jobs · AssessMax</title>
</svelte:head>

<div class="space-y-8">
  <section class="pulse-card drop-in-1 space-y-4">
    <div class="flex items-center justify-between gap-4">
      <div class="pulse-subheading">Pipeline Pulse</div>
      <button class="btn-outline text-sm" type="button" on:click={refreshJobs} disabled={refreshing}>
        {#if refreshing}
          Refreshing…
        {:else}
          Refresh
        {/if}
      </button>
    </div>
    <div class="grid gap-4 md:grid-cols-4">
      <div class="pulse-metric">
        <div class="pulse-metric-value">{stats.jobsToday}</div>
        <p class="text-muted">Jobs Today</p>
      </div>
      <div class="pulse-metric">
        <div class="pulse-metric-value">{successRateDisplay()}</div>
        <p class="text-muted">Success Rate</p>
      </div>
      <div class="pulse-metric">
        <div class="pulse-metric-value">{medianDurationDisplay()}</div>
        <p class="text-muted">Median Duration</p>
      </div>
      <div class="pulse-metric">
        <div class="pulse-metric-value">{stats.activeBatches}</div>
        <p class="text-muted">Active Batches</p>
      </div>
    </div>
    {#if error}
      <div class="pulse-notification error" role="alert">
        {error}
      </div>
    {/if}
  </section>

  <section class="pulse-card drop-in-2 space-y-6">
    <div class="flex gap-3 flex-wrap">
      <button
        class={`btn-outline ${activeTab === 'uploads' ? 'bg-[color:var(--accent)] text-[color:var(--background)]' : ''}`}
        type="button"
        on:click={() => (activeTab = 'uploads')}
      >
        Upload Files
      </button>
      <button
        class={`btn-outline ${activeTab === 'status' ? 'bg-[color:var(--accent)] text-[color:var(--background)]' : ''}`}
        type="button"
        on:click={() => (activeTab = 'status')}
      >
        Job Status
      </button>
      <button
        class={`btn-outline ${activeTab === 'history' ? 'bg-[color:var(--accent)] text-[color:var(--background)]' : ''}`}
        type="button"
        on:click={() => (activeTab = 'history')}
      >
        Upload History
      </button>
    </div>

    {#if activeTab === 'uploads'}
      <div class="grid gap-6 lg:grid-cols-2">
        <div class="card-bordered space-y-4">
          <div class="pulse-subheading">Transcript Upload</div>
          <p class="text-muted text-sm">
            JSONL, CSV, TXT up to 50MB. Metadata mirrors educator upload workflow.
          </p>
          <button class="pulse-button" type="button">Choose Files</button>
        </div>
        <div class="card-bordered space-y-4">
          <div class="pulse-subheading">Artifact Upload</div>
          <p class="text-muted text-sm">
            PDF, DOCX, PNG, JPG with student metadata (class, date, description).
          </p>
          <button class="pulse-button" type="button">Choose Files</button>
        </div>
      </div>
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <div class="pulse-subheading text-sm uppercase tracking-wide text-muted">Recent Uploads</div>
          <span class="text-xs text-muted">{recentUploads.length} most recent jobs</span>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="text-muted uppercase tracking-wider border-b border-[color:var(--border-color)]">
              <tr>
                <th class="py-2 pr-6">File</th>
                <th class="py-2 pr-6">Status</th>
                <th class="py-2 pr-6">Class</th>
                <th class="py-2 pr-6">Created</th>
              </tr>
            </thead>
            <tbody>
              {#if recentUploads.length === 0}
                <tr>
                  <td class="py-4 text-muted" colspan={4}>No recent uploads.</td>
                </tr>
              {:else}
                {#each recentUploads as job}
                  <tr class="border-b border-[color:var(--border-color)]">
                    <td class="py-3 pr-6 font-mono text-xs">{job.file_name}</td>
                    <td class="py-3 pr-6">
                      {#if job.status}
                        <span
                          class="px-2 py-1 rounded-full text-xs"
                          style={`background-color: ${badgeStyle(job.status).backgroundColor}; color: ${badgeStyle(job.status).color}`}
                        >
                          {statusLabel(job.status)}
                        </span>
                      {:else}
                        —
                      {/if}
                    </td>
                    <td class="py-3 pr-6">{job.class_id}</td>
                    <td class="py-3 pr-6">{formatDateTime(job.created_at)}</td>
                  </tr>
                {/each}
              {/if}
            </tbody>
          </table>
        </div>
      </div>
    {:else if activeTab === 'status'}
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <div class="pulse-subheading text-base">Active Jobs</div>
            <p class="text-muted text-sm">
              Jobs currently running through the normalization or scoring pipeline.
            </p>
          </div>
          <span class="text-sm text-muted">{activeJobs.length} active</span>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="text-muted uppercase tracking-wider border-b border-[color:var(--border-color)]">
              <tr>
                <th class="py-2 pr-6">File</th>
                <th class="py-2 pr-6">Status</th>
                <th class="py-2 pr-6">Started</th>
                <th class="py-2 pr-6">Class</th>
                <th class="py-2 pr-6">Elapsed</th>
                <th class="py-2 pr-6">Notes</th>
              </tr>
            </thead>
            <tbody>
              {#if activeJobs.length === 0}
                <tr>
                  <td class="py-4 text-muted" colspan={6}>
                    All clear—no jobs are currently processing.
                  </td>
                </tr>
              {:else}
                {#each activeJobs as job}
                  <tr class="border-b border-[color:var(--border-color)] hover:bg-[color:var(--card-bg)]/40 transition">
                    <td class="py-3 pr-6 font-mono text-xs">{job.file_name}</td>
                    <td class="py-3 pr-6">
                      <span
                        class="px-2 py-1 rounded-full text-xs"
                        style={`background-color: ${badgeStyle(job.status).backgroundColor}; color: ${badgeStyle(job.status).color}`}
                      >
                        {statusLabel(job.status)}
                      </span>
                    </td>
                    <td class="py-3 pr-6">{formatDateTime(job.started_at)}</td>
                    <td class="py-3 pr-6">{job.class_id}</td>
                    <td class="py-3 pr-6">
                      {#if job.duration_ms !== null}
                        {formatDurationMs(job.duration_ms)}
                      {:else}
                        {formatDurationMs(Date.now() - new Date(job.started_at).getTime())}
                      {/if}
                    </td>
                    <td class="py-3 pr-6 text-xs text-muted">
                      {job.error ? job.error : 'Processing'}
                    </td>
                  </tr>
                {/each}
              {/if}
            </tbody>
          </table>
        </div>
      </div>
    {:else}
      <div class="space-y-4">
        <div class="flex flex-wrap items-center gap-3">
          <label class="pulse-form-field w-48">
            <span class="text-xs text-muted uppercase tracking-wide">Status</span>
            <select class="input-select text-sm" bind:value={statusFilter}>
              <option value="all">All</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </label>
          <label class="pulse-form-field w-48">
            <span class="text-xs text-muted uppercase tracking-wide">Sort</span>
            <select class="input-select text-sm" bind:value={sortDirection}>
              <option value="desc">Newest first</option>
              <option value="asc">Oldest first</option>
            </select>
          </label>
        </div>

        <div class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="text-muted uppercase tracking-wider border-b border-[color:var(--border-color)]">
              <tr>
                <th class="py-2 pr-6">File</th>
                <th class="py-2 pr-6">Status</th>
                <th class="py-2 pr-6">Created</th>
                <th class="py-2 pr-6">Completed</th>
                <th class="py-2 pr-6">Duration</th>
                <th class="py-2 pr-6">Class</th>
                <th class="py-2 pr-6">Error</th>
              </tr>
            </thead>
            <tbody>
              {#if filteredHistory.length === 0}
                <tr>
                  <td class="py-4 text-muted" colspan={7}>
                    No jobs match the selected filters.
                  </td>
                </tr>
              {:else}
                {#each filteredHistory as job}
                  <tr class="border-b border-[color:var(--border-color)] hover:bg-[color:var(--card-bg)]/40 transition">
                    <td class="py-3 pr-6 font-mono text-xs">{job.file_name}</td>
                    <td class="py-3 pr-6">
                      <span
                        class="px-2 py-1 rounded-full text-xs"
                        style={`background-color: ${badgeStyle(job.status).backgroundColor}; color: ${badgeStyle(job.status).color}`}
                      >
                        {statusLabel(job.status)}
                      </span>
                    </td>
                    <td class="py-3 pr-6">{formatDate(job.created_at)}</td>
                    <td class="py-3 pr-6">{formatDate(job.completed_at)}</td>
                    <td class="py-3 pr-6">{formatDurationMs(job.duration_ms)}</td>
                    <td class="py-3 pr-6">{job.class_id}</td>
                    <td class="py-3 pr-6 text-xs text-muted">
                      {job.error ?? '—'}
                    </td>
                  </tr>
                {/each}
              {/if}
            </tbody>
          </table>
        </div>
      </div>
    {/if}
  </section>
</div>
