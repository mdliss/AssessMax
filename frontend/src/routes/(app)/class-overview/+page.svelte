<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { ROUTES } from '$lib/config';
  import { clearCache } from '$lib/api/client';
  import { getClassDashboard, type ClassDashboardResponse, type StudentSummary } from '$lib/api/assessments';
  import RadarChart from '$lib/components/RadarChart.svelte';

  let classId = 'MS-7A';
  let loading = false;
  let error: string | null = null;
  let hydrated = false;
  let dashboardData: ClassDashboardResponse | null = null;

  $: students = dashboardData?.students ?? [];
  $: metrics = dashboardData?.metrics;
  $: classAverages = metrics?.class_averages ?? {};
  $: avgPerStudent = metrics && metrics.student_count > 0
    ? (metrics.total_assessments / metrics.student_count).toFixed(1)
    : '--';
  $: dateRange = metrics?.date_range
    ? `${new Date(metrics.date_range[0]).toLocaleDateString()} - ${new Date(metrics.date_range[1]).toLocaleDateString()}`
    : '--';

  onMount(() => {
    hydrated = true;
    loadClassData();
  });

  async function loadClassData() {
    if (!classId) return;

    loading = true;
    error = null;
    try {
      dashboardData = await getClassDashboard(classId);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unable to load class data';
      console.error('Failed to load class data:', err);
    } finally {
      loading = false;
    }
  }

  async function handleRefresh() {
    clearCache('GET:/v1/classes');
    await loadClassData();
  }

  function handleClearCache() {
    clearCache();
  }

  function openStudentDetail(student: StudentSummary) {
    const params = new URLSearchParams({
      id: student.student_id,
      class: classId
    });
    goto(`${ROUTES.studentDetail}?${params.toString()}`);
  }

  function calculateStudentAverage(student: StudentSummary): string {
    const scores = Object.values(student.average_scores);
    if (scores.length === 0) return '--';
    const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
    return avg.toFixed(1);
  }

  function getLastAssessedDate(student: StudentSummary): string {
    if (!student.latest_assessment) return '--';
    return new Date(student.latest_assessment.assessed_on).toLocaleDateString();
  }
</script>

<svelte:head>
  <title>Class Overview · AssessMax</title>
</svelte:head>

<div class="space-y-8">
  <section class="pulse-card drop-in-1">
    <div class="pulse-subheading">Class Identifier</div>
    <div class="grid gap-4 md:grid-cols-[2fr_1fr_1fr]">
      <label class="pulse-form-field">
        <span class="text-muted text-sm">Class ID</span>
        <input class="input-text" bind:value={classId} placeholder="e.g., MS-7A" />
      </label>
      <button class="pulse-button" type="button" on:click={handleRefresh} disabled={loading}>
        {#if loading}
          Refreshing…
        {:else}
          Refresh Pulse
        {/if}
      </button>
      <button class="btn-outline" type="button" on:click={handleClearCache} disabled={loading}>
        Clear Cache
      </button>
    </div>
    {#if error}
      <div class="pulse-notification error mt-4" role="alert">{error}</div>
    {/if}
  </section>

  <section class="drop-in-2">
    <div class="pulse-card">
      <div class="pulse-subheading">Snapshot</div>
      <div class="grid gap-4 md:grid-cols-4">
        <div class="pulse-metric">
          <div class="pulse-metric-value">{metrics?.student_count ?? '--'}</div>
          <p class="text-muted">Active Students</p>
        </div>
        <div class="pulse-metric">
          <div class="pulse-metric-value">{metrics?.total_assessments ?? '--'}</div>
          <p class="text-muted">Assessments Captured</p>
        </div>
        <div class="pulse-metric">
          <div class="pulse-metric-value">{avgPerStudent}</div>
          <p class="text-muted">Avg / Student</p>
        </div>
        <div class="pulse-metric">
          <div class="pulse-metric-value text-xs">{dateRange}</div>
          <p class="text-muted">Coverage Window</p>
        </div>
      </div>
    </div>
  </section>

  <section class="grid gap-6 lg:grid-cols-[2fr_1fr] drop-in-3">
    <div class="pulse-card">
      <div class="pulse-subheading">Skill Averages</div>
      {#if Object.keys(classAverages).length > 0}
        <RadarChart data={classAverages} title="Class Averages" />
      {:else}
        <div class="h-[360px] rounded-xl border border-[color:var(--border-color)] bg-[color:var(--background)]/60 flex items-center justify-center text-muted">
          {loading ? 'Loading...' : 'No data available'}
        </div>
      {/if}
    </div>
    <div class="pulse-card space-y-3">
      <div class="pulse-subheading">Signal Strength</div>
      {#if metrics}
        <div class="space-y-3">
          {#each Object.entries(classAverages) as [skill, score]}
            <div class="flex items-center justify-between">
              <span class="text-sm capitalize">{skill.replace('_', ' ')}</span>
              <span class="text-sm font-mono" style="color: var(--accent)">{score.toFixed(1)}/100</span>
            </div>
          {/each}
        </div>
      {:else}
        <div class="space-y-2 text-sm text-muted">
          <p>Scores will render here once data is loaded.</p>
        </div>
      {/if}
    </div>
  </section>

  <section class="pulse-card drop-in-4">
    <div class="pulse-subheading">Student Summaries</div>
    <div class="overflow-x-auto">
      <table class="min-w-full text-left text-sm">
        <thead class="text-muted uppercase tracking-wider">
          <tr>
            <th class="py-2 pr-6">Student</th>
            <th class="py-2 pr-6">Student ID</th>
            <th class="py-2 pr-6">Assessments</th>
            <th class="py-2 pr-6">Last Assessed</th>
            <th class="py-2 pr-6">Overall Avg</th>
            <th class="py-2 pr-6">Actions</th>
          </tr>
        </thead>
        <tbody>
          {#if loading}
            <tr>
              <td class="py-6 text-muted" colspan={6}>
                Loading class data...
              </td>
            </tr>
          {:else if students.length === 0}
            <tr>
              <td class="py-6 text-muted" colspan={6}>
                No students found in class {classId}. Try a different class ID (MS-7A, MS-7B, or MS-8A).
              </td>
            </tr>
          {:else}
            {#each students as student}
              <tr class="border-t border-[color:var(--border-color)]">
                <td class="py-3 pr-6">
                  <button
                    class="btn-ghost px-0 text-left font-medium"
                    type="button"
                    on:click={() => openStudentDetail(student)}
                  >
                    {student.name ?? 'Unknown'}
                  </button>
                </td>
                <td class="py-3 pr-6 font-mono text-xs">{student.student_id}</td>
                <td class="py-3 pr-6">{student.assessment_count}</td>
                <td class="py-3 pr-6">{getLastAssessedDate(student)}</td>
                <td class="py-3 pr-6">{calculateStudentAverage(student)}</td>
                <td class="py-3 pr-6">
                  <button class="btn-outline text-xs" type="button" on:click={() => openStudentDetail(student)}>
                    View Detail
                  </button>
                </td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  </section>
</div>
