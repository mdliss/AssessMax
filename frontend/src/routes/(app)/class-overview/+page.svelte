<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { ROUTES } from '$lib/config';
  import { clearCache } from '$lib/api/client';

  let classId = 'MS-7A';
  let loading = false;
  let error: string | null = null;
  let hydrated = false;
  let students: Array<Record<string, string | number>> = [];
  let metrics: Record<string, number | string> = {};

  onMount(() => {
    hydrated = true;
  });

  async function handleRefresh() {
    loading = true;
    error = null;
    try {
      clearCache('GET:/v1/classes');
      // TODO: integrate real data fetch via API client (migration follow-up)
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unable to refresh class data';
    } finally {
      loading = false;
    }
  }

  function handleClearCache() {
    clearCache();
  }

  function openStudentDetail(studentId: string) {
    goto(`${ROUTES.studentDetail}?id=${studentId}`);
  }
</script>

<svelte:head>
  <title>Class Overview · PulseMax</title>
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
          <div class="pulse-metric-value">{metrics.student_count ?? '--'}</div>
          <p class="text-muted">Active Students</p>
        </div>
        <div class="pulse-metric">
          <div class="pulse-metric-value">{metrics.total_assessments ?? '--'}</div>
          <p class="text-muted">Assessments Captured</p>
        </div>
        <div class="pulse-metric">
          <div class="pulse-metric-value">{metrics.avg_per_student ?? '--'}</div>
          <p class="text-muted">Avg / Student</p>
        </div>
        <div class="pulse-metric">
          <div class="pulse-metric-value">{metrics.coverage ?? '--'}</div>
          <p class="text-muted">Coverage Window</p>
        </div>
      </div>
    </div>
  </section>

  <section class="grid gap-6 lg:grid-cols-[2fr_1fr] drop-in-3">
    <div class="pulse-card">
      <div class="pulse-subheading">Skill Averages</div>
      <div class="h-[360px] rounded-xl border border-[color:var(--border-color)] bg-[color:var(--background)]/60 flex items-center justify-center text-muted">
        Radar chart placeholder
      </div>
    </div>
    <div class="pulse-card space-y-3">
      <div class="pulse-subheading">Signal Strength</div>
      <div class="space-y-2 text-sm text-muted">
        <p>Scores will render here once data integration is complete.</p>
      </div>
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
          {#if students.length === 0}
            <tr>
              <td class="py-6 text-muted" colspan={6}>
                Data will populate once API wiring is completed. CSV/PDF exports will live in this section.
              </td>
            </tr>
          {:else}
            {#each students as student}
              <tr class="border-t border-[color:var(--border-color)]">
                <td class="py-3 pr-6">{student.name}</td>
                <td class="py-3 pr-6 font-mono text-sm">{student.student_id}</td>
                <td class="py-3 pr-6">{student.assessment_count}</td>
                <td class="py-3 pr-6">{student.last_assessed}</td>
                <td class="py-3 pr-6">{student.overall_avg}</td>
                <td class="py-3 pr-6">
                  <button class="btn-outline text-xs" type="button" on:click={() => openStudentDetail(String(student.student_id))}>
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
