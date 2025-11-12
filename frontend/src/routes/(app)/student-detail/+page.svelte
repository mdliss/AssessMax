<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import type { PageData } from './$types';
  import { ROUTES } from '$lib/config';
  import { clearCache } from '$lib/api/client';
  import { getLatestAssessment, getAssessmentHistory, type AssessmentResponse, type AssessmentHistoryResponse } from '$lib/api/assessments';
  import RadarChart from '$lib/components/RadarChart.svelte';

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
  let assessment: AssessmentResponse | null = null;
  let history: AssessmentHistoryResponse | null = null;

  $: skillScores = assessment?.skills.reduce((acc, skill) => {
    acc[skill.skill] = skill.score;
    return acc;
  }, {} as Record<string, number>) ?? {};

  onMount(() => {
    if (studentId) {
      loadStudentData();
    }
  });

  async function loadStudentData() {
    if (!studentId) return;

    loading = true;
    error = null;
    try {
      [assessment, history] = await Promise.all([
        getLatestAssessment(studentId),
        getAssessmentHistory(studentId)
      ]);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unable to load student data';
      console.error('Failed to load student data:', err);
    } finally {
      loading = false;
    }
  }

  async function handleRefresh() {
    clearCache('GET:/v1/students');
    clearCache('GET:/v1/assessments');
    await loadStudentData();
  }

  function selectStudent(id: string) {
    studentId = id;
    goto(`${ROUTES.studentDetail}?id=${id}`, { replaceState: true });
    loadStudentData();
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
      <div class="pulse-subheading">Student Overview</div>
      {#if assessment}
        <div class="grid gap-4 md:grid-cols-4">
          <div class="pulse-metric">
            <div class="pulse-metric-value text-sm">Class {assessment.class_id}</div>
            <p class="text-muted">Student ID: {studentId.slice(0, 8)}...</p>
          </div>
          <div class="pulse-metric">
            <div class="pulse-metric-value">{new Date(assessment.assessed_on).toLocaleDateString()}</div>
            <p class="text-muted">Last Assessment</p>
          </div>
          <div class="pulse-metric">
            <div class="pulse-metric-value">
              {(Object.values(skillScores).reduce((a, b) => a + b, 0) / Object.values(skillScores).length).toFixed(1)}
            </div>
            <p class="text-muted">Average Score</p>
          </div>
          <div class="pulse-metric">
            <div class="pulse-metric-value text-sm capitalize">
              {Object.entries(skillScores).sort((a, b) => b[1] - a[1])[0]?.[0].replace('_', ' ')}
            </div>
            <p class="text-muted">Top Skill</p>
          </div>
        </div>
      {:else if loading}
        <div class="text-center py-6 text-muted">Loading student data...</div>
      {:else}
        <div class="text-center py-6 text-muted">No assessment data available. Enter a valid student ID.</div>
      {/if}
    </div>

    <div class="grid gap-6 lg:grid-cols-[2fr_1fr]">
      <div class="pulse-card">
        <div class="pulse-subheading">Current Skill Signature</div>
        {#if Object.keys(skillScores).length > 0}
          <RadarChart data={skillScores} title="Student Skills" />
        {:else}
          <div class="h-[360px] border border-[color:var(--border-color)] rounded-xl flex items-center justify-center text-muted">
            {loading ? 'Loading...' : 'No skill data available'}
          </div>
        {/if}
      </div>
      <div class="pulse-card space-y-3">
        <div class="pulse-subheading">Skill Scores</div>
        {#if assessment}
          <div class="space-y-3">
            {#each assessment.skills as skill}
              <div class="space-y-1">
                <div class="flex items-center justify-between">
                  <span class="text-sm capitalize">{skill.skill.replace('_', ' ')}</span>
                  <span class="text-sm font-mono" style="color: var(--accent)">{skill.score.toFixed(1)}/100</span>
                </div>
                <div class="text-xs text-muted">Confidence: {(skill.confidence * 100).toFixed(0)}%</div>
              </div>
            {/each}
          </div>
        {:else}
          <p class="text-muted text-sm">Scores will appear when data is loaded.</p>
        {/if}
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
