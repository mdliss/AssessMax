<script lang="ts">
  import { goto } from '$app/navigation';
  import type { PageData } from './$types';
  import { ROUTES } from '$lib/config';
  import { clearCache } from '$lib/api/client';

  export let data: PageData;

  const sampleStudents = [
    { name: 'Emma Johnson', id: '550e8400-e29b-41d4-a716-446655440001' },
    { name: 'Marcus Williams', id: '550e8400-e29b-41d4-a716-446655440002' },
    { name: 'Sarah Chen', id: '550e8400-e29b-41d4-a716-446655440003' },
    { name: 'Alicia Rivera', id: '550e8400-e29b-41d4-a716-446655440004' }
  ];

  let studentId = data.initialStudentId ?? sampleStudents[0]?.id ?? '';
  let loading = false;
  let error: string | null = null;

  async function handleRefresh() {
    error = null;
    loading = true;
    try {
      clearCache('GET:/v1/students');
      // TODO: fetch student detail data
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unable to refresh student data';
    } finally {
      loading = false;
    }
  }

  function selectStudent(id: string) {
    studentId = id;
    goto(`${ROUTES.studentDetail}?id=${id}`, { replaceState: true });
  }
</script>

<svelte:head>
  <title>Student Detail · PulseMax</title>
</svelte:head>

<div class="space-y-8">
  <section class="pulse-card drop-in-1 space-y-6">
    <div class="pulse-subheading">Student Identifier</div>
    <div class="grid gap-4 md:grid-cols-[2fr_1fr]">
      <label class="pulse-form-field">
        <span class="text-sm text-muted">Student UUID</span>
        <input class="input-text" bind:value={studentId} placeholder="UUID" />
      </label>
      <button class="pulse-button" type="button" on:click={handleRefresh} disabled={loading}>
        {#if loading}
          Refresh Records…
        {:else}
          Refresh Records
        {/if}
      </button>
    </div>

    <div class="text-sm text-muted font-mono">
      Quick selections:
      {#each sampleStudents as student, index}
        <button class="btn-ghost inline-flex items-center gap-1" type="button" on:click={() => selectStudent(student.id)}>
          {student.name}
        </button>{index < sampleStudents.length - 1 ? '·' : ''}
      {/each}
    </div>

    {#if error}
      <div class="pulse-notification error" role="alert">{error}</div>
    {/if}
  </section>

  <section class="drop-in-2 space-y-4">
    <div class="pulse-card">
      <div class="pulse-subheading">Student Hero</div>
      <div class="grid gap-4 md:grid-cols-4">
        <div class="pulse-metric">
          <div class="pulse-metric-value">Student Name</div>
          <p class="text-muted">Top skill and meta will render here.</p>
        </div>
        <div class="pulse-metric">
          <div class="pulse-metric-value">Last Assessment</div>
          <p class="text-muted">ISO date from backend.</p>
        </div>
        <div class="pulse-metric">
          <div class="pulse-metric-value">Avg Score</div>
          <p class="text-muted">0-100 scale.</p>
        </div>
        <div class="pulse-metric">
          <div class="pulse-metric-value">Top Skill</div>
          <p class="text-muted">Communication, etc.</p>
        </div>
      </div>
    </div>

    <div class="grid gap-6 lg:grid-cols-[2fr_1fr]">
      <div class="pulse-card">
        <div class="pulse-subheading">Current Skill Signature</div>
        <div class="h-[360px] border border-[color:var(--border-color)] rounded-xl flex items-center justify-center text-muted">
          Radar chart placeholder
        </div>
      </div>
      <div class="pulse-card space-y-3">
        <div class="pulse-subheading">Skill Cards</div>
        <p class="text-muted text-sm">Score & confidence cards will render here using reusable components.</p>
      </div>
    </div>
  </section>

  <section class="pulse-card drop-in-3 space-y-6">
    <div class="pulse-subheading">Evidence Highlights</div>
    <div class="grid gap-4 md:grid-cols-2">
      <div class="card-bordered">
        <div class="text-sm text-muted uppercase tracking-wide">Skill Group</div>
        <p class="text-muted text-sm mt-2">Evidence spans and rationales will populate here.</p>
      </div>
      <div class="card-bordered">
        <div class="text-sm text-muted uppercase tracking-wide">Skill Group</div>
        <p class="text-muted text-sm mt-2">Evidence spans and rationales will populate here.</p>
      </div>
    </div>
  </section>

  <section class="pulse-card drop-in-4 space-y-6">
    <div class="pulse-subheading">Assessment History</div>
    <div class="flex gap-4">
      <button class="btn-outline" type="button">Trend Lines</button>
      <button class="btn-outline" type="button">Export CSV</button>
      <button class="btn-outline" type="button">Export PDF</button>
    </div>
    <div class="h-[320px] rounded-xl border border-[color:var(--border-color)] flex items-center justify-center text-muted">
      Trend chart placeholder
    </div>
  </section>

  <section class="pulse-card drop-in-5 space-y-4">
    <div class="pulse-subheading">Assessment Ledger</div>
    <div class="overflow-x-auto">
      <table class="min-w-full text-left text-sm">
        <thead class="text-muted uppercase tracking-wider">
          <tr>
            <th class="py-2 pr-6">Assessment ID</th>
            <th class="py-2 pr-6">Date</th>
            <th class="py-2 pr-6">Class</th>
            <th class="py-2 pr-6">Model Version</th>
            <th class="py-2 pr-6">Score</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="py-3 pr-6 font-mono text-xs">—</td>
            <td class="py-3 pr-6">—</td>
            <td class="py-3 pr-6">—</td>
            <td class="py-3 pr-6">—</td>
            <td class="py-3 pr-6">—</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</div>
