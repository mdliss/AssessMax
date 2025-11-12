<script lang="ts">
  import { onMount } from 'svelte';
  import type { PageData } from './$types';
  import { clearCache } from '$lib/api/client';
  import {
    getLatestAssessment,
    getAssessmentHistory,
    getClassDashboard,
    type AssessmentResponse,
    type AssessmentHistoryResponse,
    type StudentSummary
  } from '$lib/api/assessments';
  import RadarChart from '$lib/components/RadarChart.svelte';

  export let data: PageData;

  const classIds = ['MS-7A', 'MS-7B', 'MS-8A'];

  let selectedClass =
    data.initialClassId && classIds.includes(data.initialClassId)
      ? data.initialClassId
      : classIds[0];

  let studentId = data.initialStudentId ?? '';
  let loading = false;
  let rosterLoading = false;
  let error: string | null = null;
  let rosterError: string | null = null;
  let assessment: AssessmentResponse | null = null;
  let history: AssessmentHistoryResponse | null = null;

  let classRosters: Record<string, StudentSummary[]> = {};
  $: availableStudents = classRosters[selectedClass] ?? [];
  $: selectedStudent = availableStudents.find((student) => student.student_id === studentId);

  const classLabels: Record<string, string> = {
    'MS-7A': 'MS-7A · Advisory A',
    'MS-7B': 'MS-7B · Advisory B',
    'MS-8A': 'MS-8A · Capstone'
  };

  $: skillScores =
    assessment?.skills.reduce((acc, skill) => {
      acc[skill.skill] = skill.score;
      return acc;
    }, {} as Record<string, number>) ?? {};

  $: averageScore = (() => {
    const values = Object.values(skillScores);
    if (values.length === 0) return null;
    const total = values.reduce((sum, value) => sum + value, 0);
    return (total / values.length).toFixed(1);
  })();

  $: topSkill = (() => {
    const entries = Object.entries(skillScores).sort((a, b) => b[1] - a[1]);
    if (entries.length === 0) return '';
    return entries[0][0].replace('_', ' ');
  })();

  onMount(async () => {
    await loadRosters();

    if (studentId) {
      const containing = findClassForStudent(studentId);
      if (containing) {
        selectedClass = containing;
      } else {
        rosterError = 'Student not found in rostered classes. Select a student from the list.';
      }
      await loadStudentData(studentId);
    } else {
      const fallback = nextAvailableStudent(selectedClass) ?? nextAvailableStudent();
      if (fallback) {
        await selectStudent(fallback.student_id, { updateUrl: true });
      }
    }
  });

  function findClassForStudent(id: string): string | null {
    for (const classId of classIds) {
      if ((classRosters[classId] ?? []).some((student) => student.student_id === id)) {
        return classId;
      }
    }
    return null;
  }

  function nextAvailableStudent(classId?: string): StudentSummary | null {
    if (classId && (classRosters[classId]?.length ?? 0) > 0) {
      return classRosters[classId][0];
    }
    for (const id of classIds) {
      if ((classRosters[id]?.length ?? 0) > 0) {
        return classRosters[id][0];
      }
    }
    return null;
  }

  async function loadRosters(force = false) {
    rosterLoading = true;
    rosterError = null;

    if (force) {
      clearCache('GET:/v1/classes');
    }

    const results = await Promise.allSettled(classIds.map((classId) => getClassDashboard(classId)));
    const updated: Record<string, StudentSummary[]> = {};

    results.forEach((result, index) => {
      const classId = classIds[index];
      if (result.status === 'fulfilled') {
        updated[classId] = result.value.students;
      } else {
        console.error(`Failed to load roster for ${classId}:`, result.reason);
        rosterError = 'Some class rosters could not be loaded.';
        updated[classId] = classRosters[classId] ?? [];
      }
    });

    classRosters = updated;
    rosterLoading = false;
  }

  async function loadStudentData(id: string = studentId) {
    if (!id) {
      assessment = null;
      history = null;
      return;
    }

    loading = true;
    error = null;

    try {
      const [latest, historyResponse] = await Promise.all([
        getLatestAssessment(id),
        getAssessmentHistory(id)
      ]);
      assessment = latest;
      history = historyResponse;
    } catch (err) {
      assessment = null;
      history = null;
      error =
        err instanceof Error
          ? err.message
          : 'Unable to load student data. Please verify the student ID.';
      console.error('Failed to load student data:', err);
    } finally {
      loading = false;
    }
  }

  function updateUrl(id: string, classId: string) {
    if (typeof window === 'undefined') return;
    const url = new URL(window.location.href);
    url.searchParams.set('id', id);
    url.searchParams.set('class', classId);
    window.history.replaceState({}, '', url.toString());
  }

  async function selectStudent(
    id: string,
    options: {
      updateUrl?: boolean;
    } = {}
  ) {
    const { updateUrl: shouldUpdateUrl = true } = options;
    if (!id) return;

    studentId = id;
    if (shouldUpdateUrl) {
      updateUrl(id, selectedClass);
    }

    await loadStudentData(id);
  }

  async function handleClassChange(event: Event) {
    const newClassId = (event.currentTarget as HTMLSelectElement).value;
    if (!classIds.includes(newClassId)) return;
    selectedClass = newClassId;

    if (!availableStudents.some((student) => student.student_id === studentId)) {
      const fallback = nextAvailableStudent(selectedClass);
      if (fallback) {
        await selectStudent(fallback.student_id);
      } else {
        assessment = null;
        history = null;
        error = 'No students found in the selected class.';
      }
    } else if (studentId) {
      updateUrl(studentId, selectedClass);
    }
  }

  function handleManualInput(value: string) {
    studentId = value.trim();
  }

  async function handleStudentSelect(event: Event) {
    const newId = (event.currentTarget as HTMLSelectElement).value;
    await selectStudent(newId);
  }

  async function handleRefresh() {
    if (studentId) {
      updateUrl(studentId, selectedClass);
    }
    clearCache('GET:/v1/assessments');
    await loadRosters(true);
    if (studentId) {
      const containing = findClassForStudent(studentId);
      if (containing) {
        selectedClass = containing;
      }
      await loadStudentData(studentId);
    } else {
      assessment = null;
      history = null;
    }
  }
</script>

<svelte:head>
  <title>Student Detail · AssessMax</title>
</svelte:head>

<div class="space-y-8">
  <section class="pulse-card drop-in-1 space-y-6">
    <div class="pulse-subheading">Student Identifier</div>
    <div class="grid gap-4 md:grid-cols-[2fr_1fr]">
      <label class="pulse-form-field">
        <span class="text-sm text-muted">Student UUID</span>
        <input
          class="input-text"
          value={studentId}
          placeholder="UUID"
          on:input={(event) => handleManualInput((event.currentTarget as HTMLInputElement).value)}
        />
      </label>
      <div class="flex gap-2">
        <button
          class="pulse-button"
          type="button"
          on:click={handleRefresh}
          disabled={loading || rosterLoading}
        >
          {#if loading || rosterLoading}
            Refreshing…
          {:else}
            Refresh Records
          {/if}
        </button>
      </div>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <label class="pulse-form-field">
        <span class="text-sm text-muted">Class</span>
        <select
          class="input-select"
          value={selectedClass}
          on:change={handleClassChange}
          disabled={rosterLoading}
        >
          {#each classIds as classId}
            <option value={classId}>{classLabels[classId] ?? classId}</option>
          {/each}
        </select>
      </label>
      <label class="pulse-form-field">
        <span class="text-sm text-muted">Student</span>
        <select
          class="input-select"
          value={studentId}
          on:change={handleStudentSelect}
          disabled={availableStudents.length === 0 || rosterLoading}
        >
          {#if availableStudents.length === 0}
            <option value="">No students available</option>
          {:else}
            {#each availableStudents as student}
              <option value={student.student_id}>
                {(student.name ?? 'Unnamed Student') + ' · ' + selectedClass}
              </option>
            {/each}
          {/if}
        </select>
      </label>
    </div>

    {#if rosterLoading}
      <div class="text-sm text-muted font-mono">Loading class rosters…</div>
    {:else}
      {#if rosterError}
        <div class="pulse-notification error" role="alert">{rosterError}</div>
      {/if}
      {#if selectedStudent}
        <div class="text-sm text-muted font-mono">
          Viewing {selectedStudent.name ?? 'Unnamed Student'} · {selectedClass}
        </div>
      {/if}
      {#if availableStudents.length > 0}
        <div class="text-sm text-muted flex flex-wrap gap-2 items-center">
          <span class="font-mono">Quick selections:</span>
          {#each availableStudents.slice(0, 6) as student}
            <button
              class="btn-ghost inline-flex items-center gap-1"
              type="button"
              on:click={() => selectStudent(student.student_id)}
            >
              {student.name ?? student.student_id.slice(0, 8)}
            </button>
          {/each}
        </div>
      {/if}
    {/if}

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
              {averageScore ?? '--'}
            </div>
            <p class="text-muted">Average Score</p>
          </div>
          <div class="pulse-metric">
            <div class="pulse-metric-value text-sm capitalize">
              {topSkill || '--'}
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
