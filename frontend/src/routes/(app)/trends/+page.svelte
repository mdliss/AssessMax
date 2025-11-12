<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import type { PageData } from './$types';
  import { clearCache } from '$lib/api/client';
  import {
    getAssessmentHistory,
    getClassDashboard,
    type AssessmentHistoryResponse
  } from '$lib/api/assessments';
  import { Chart } from 'chart.js/auto';

  export let data: PageData;

  type Mode = 'class' | 'student';
  type WindowSize = 4 | 8 | 12;
  type Smoothing = 'none' | 'simple' | 'ema';

  type SimpleStudent = {
    student_id: string;
    name: string | null;
  };

  type SkillKey = typeof SKILLS[number];

  interface TrendMetrics {
    momentumScore: number | null;
    trajectory: string;
    stability: number | null;
    lastUpdated: string | null;
  }

  interface SkillSnapshot {
    skill: SkillKey;
    label: string;
    latest: number | null;
    change: number | null;
  }

  interface TrendComputation {
    labels: string[];
    displayLabels: string[];
    datasets: Array<Array<number | null>>;
    metrics: TrendMetrics;
    snapshots: SkillSnapshot[];
  }

  const SKILLS = ['empathy', 'adaptability', 'collaboration', 'communication', 'self_regulation'] as const;

  const SKILL_LABELS: Record<SkillKey, string> = {
    empathy: 'Empathy',
    adaptability: 'Adaptability',
    collaboration: 'Collaboration',
    communication: 'Communication',
    self_regulation: 'Self Regulation'
  };

  const SKILL_COLORS: Record<SkillKey, string> = {
    empathy: '#14b8a6',
    adaptability: '#3B82F6',
    collaboration: '#10B981',
    communication: '#F59E0B',
    self_regulation: '#A855F7'
  };

  const CLASS_OPTIONS = [
    { id: 'MS-7A', label: 'MS-7A · Advisory A' },
    { id: 'MS-7B', label: 'MS-7B · Advisory B' },
    { id: 'MS-8A', label: 'MS-8A · Capstone' }
  ] as const;

  const DATE_FORMAT = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' });
  const LONG_DATE_FORMAT = new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });

  let mode: Mode = (data.initialMode as Mode) ?? 'class';
  let windowWeeks: WindowSize = 8;
  let smoothing: Smoothing = 'simple';
  let selectedClass = data.initialClassId ?? CLASS_OPTIONS[0].id;
  let selectedStudentId = data.initialStudentId ?? '';

  let classStudentsMap: Record<string, SimpleStudent[]> = {};
  let classHistoriesMap: Record<string, AssessmentHistoryResponse[]> = {};
  const studentHistoryCache = new Map<string, AssessmentHistoryResponse>();

  if (data.classStudents?.length) {
    classStudentsMap[selectedClass] = data.classStudents;
  }
  if (data.classHistories?.length) {
    classHistoriesMap[selectedClass] = data.classHistories;
  }
  if (data.selectedStudentHistory) {
    studentHistoryCache.set(data.selectedStudentHistory.student_id, data.selectedStudentHistory);
  }

  let classStudents: SimpleStudent[] = classStudentsMap[selectedClass] ?? [];
  let classHistories: AssessmentHistoryResponse[] = classHistoriesMap[selectedClass] ?? [];
  let selectedStudentHistory: AssessmentHistoryResponse | null =
    studentHistoryCache.get(selectedStudentId) ?? data.selectedStudentHistory ?? null;

  let loading = false;
  let pendingRequests = 0;
  let fetchError: string | null = data.loadErrors?.length ? data.loadErrors[0] : null;
  let additionalErrors: string[] = data.loadErrors?.slice(1) ?? [];

  let chartCanvas: HTMLCanvasElement;
  let chartInstance: Chart<'line'> | null = null;

  let trendComputation: TrendComputation = computeTrendData(
    mode,
    classHistories,
    selectedStudentHistory,
    windowWeeks,
    smoothing
  );
  let metrics: TrendMetrics = trendComputation.metrics;
  let skillSnapshots: SkillSnapshot[] = trendComputation.snapshots;

  // Debug logging
  console.log('[Trends Debug] Initial data:', {
    mode,
    classHistoriesCount: classHistories.length,
    selectedStudentHistory: selectedStudentHistory ? 'present' : 'null',
    computationLabelsCount: trendComputation.labels.length,
    loadErrors: data.loadErrors
  });

  const ACTIVE_MESSAGE = 'Fetching latest trend data…';

  function beginLoading() {
    pendingRequests += 1;
    loading = true;
  }

  function endLoading() {
    pendingRequests = Math.max(0, pendingRequests - 1);
    loading = pendingRequests > 0;
  }

  async function ensureClassData(classId: string, options: { force?: boolean } = {}) {
    const { force = false } = options;
    if (!force && classStudentsMap[classId] && classHistoriesMap[classId]) {
      if (classId === selectedClass) {
        classStudents = classStudentsMap[classId];
        classHistories = classHistoriesMap[classId];
      }
      return;
    }

    beginLoading();
    if (force) {
      clearCache('GET:/v1/classes');
      clearCache('GET:/v1/assessments');
    }

    try {
      const dashboard = await getClassDashboard(classId);
      const roster: SimpleStudent[] = dashboard.students
        .map((student) => ({
          student_id: student.student_id,
          name: student.name
        }))
        .sort((a, b) => (a.name ?? '').localeCompare(b.name ?? ''));

      classStudentsMap[classId] = roster;
      if (classId === selectedClass) {
        classStudents = roster;
      }

      if (roster.length === 0) {
        classHistoriesMap[classId] = [];
        if (classId === selectedClass) {
          classHistories = [];
        }
        return;
      }

      const historyResults = await Promise.all(
        roster.map(async (student) => {
          try {
            const history = await getAssessmentHistory(student.student_id);
            studentHistoryCache.set(student.student_id, history);
            return history;
          } catch (err) {
            const message =
              err instanceof Error
                ? err.message
                : `Unable to load history for ${student.name ?? student.student_id}`;
            additionalErrors = [...additionalErrors, message];
            return null;
          }
        })
      );

      const histories = historyResults.filter(
        (history): history is AssessmentHistoryResponse => history !== null
      );
      classHistoriesMap[classId] = histories;
      if (classId === selectedClass) {
        classHistories = histories;
      }
      fetchError = null;
    } catch (err) {
      fetchError =
        err instanceof Error ? err.message : `Unable to load class data for ${classId}.`;
    } finally {
      endLoading();
    }
  }

  async function ensureStudentHistory(studentId: string, options: { force?: boolean } = {}) {
    const { force = false } = options;
    if (!studentId) {
      selectedStudentHistory = null;
      return;
    }

    if (!force && studentHistoryCache.has(studentId)) {
      selectedStudentHistory = studentHistoryCache.get(studentId) ?? null;
      return;
    }

    beginLoading();
    if (force) {
      clearCache('GET:/v1/assessments');
    }

    try {
      const history = await getAssessmentHistory(studentId);
      studentHistoryCache.set(studentId, history);
      selectedStudentHistory = history;
      fetchError = null;
    } catch (err) {
      selectedStudentHistory = null;
      fetchError =
        err instanceof Error ? err.message : `Unable to load student history for ${studentId}.`;
    } finally {
      endLoading();
    }
  }

  async function handleModeChange(event: Event) {
    const value = (event.currentTarget as HTMLSelectElement).value as Mode;
    if (value === mode) return;

    mode = value;
    if (mode === 'class') {
      await ensureClassData(selectedClass);
    } else if (mode === 'student') {
      if (!classStudentsMap[selectedClass]) {
        await ensureClassData(selectedClass);
      }
      if (!selectedStudentId && classStudents.length > 0) {
        selectedStudentId = classStudents[0].student_id;
      }
      if (selectedStudentId) {
        await ensureStudentHistory(selectedStudentId);
      }
    }
  }

  async function handleClassChange(event: Event) {
    const value = (event.currentTarget as HTMLSelectElement).value;
    if (value === selectedClass) return;

    selectedClass = value;
    await ensureClassData(selectedClass);

    if (mode === 'student') {
      if (!classStudents.some((student) => student.student_id === selectedStudentId)) {
        selectedStudentId = classStudents[0]?.student_id ?? '';
      }
      if (selectedStudentId) {
        await ensureStudentHistory(selectedStudentId);
      }
    }
  }

  async function handleStudentChange(event: Event) {
    const value = (event.currentTarget as HTMLSelectElement).value;
    selectedStudentId = value;
    await ensureStudentHistory(selectedStudentId);
  }

  function handleWindowChange(event: Event) {
    const value = Number((event.currentTarget as HTMLSelectElement).value) as WindowSize;
    windowWeeks = value;
  }

  function handleSmoothingChange(event: Event) {
    smoothing = (event.currentTarget as HTMLSelectElement).value as Smoothing;
  }

  async function handleRefresh() {
    await ensureClassData(selectedClass, { force: true });
    if (mode === 'student' && selectedStudentId) {
      await ensureStudentHistory(selectedStudentId, { force: true });
    }
  }

  function computeTrendData(
    currentMode: Mode,
    histories: AssessmentHistoryResponse[],
    studentHistory: AssessmentHistoryResponse | null,
    windowSize: WindowSize,
    smoothingMode: Smoothing
  ): TrendComputation {
    if (currentMode === 'class') {
      return computeClassTrend(histories, windowSize, smoothingMode);
    }
    return computeStudentTrend(studentHistory, windowSize, smoothingMode);
  }

  function computeClassTrend(
    histories: AssessmentHistoryResponse[],
    windowSize: WindowSize,
    smoothingMode: Smoothing
  ): TrendComputation {
    if (!histories.length) {
      return emptyTrend();
    }

    const buckets = new Map<
      string,
      Record<SkillKey, { sum: number; count: number }>
    >();

    histories.forEach((history) => {
      filterAssessments(history.assessments, windowSize).forEach((assessment) => {
        const dateKey = assessment.assessed_on;
        if (!buckets.has(dateKey)) {
          buckets.set(dateKey, {} as Record<SkillKey, { sum: number; count: number }>);
        }
        const bucket = buckets.get(dateKey)!;
        assessment.skills.forEach((skillEntry) => {
          const skill = skillEntry.skill as SkillKey;
          if (!bucket[skill]) {
            bucket[skill] = { sum: 0, count: 0 };
          }
          bucket[skill].sum += skillEntry.score;
          bucket[skill].count += 1;
        });
      });
    });

    if (buckets.size === 0) {
      return emptyTrend();
    }

    const labels = Array.from(buckets.keys()).sort(
      (a, b) => new Date(a).getTime() - new Date(b).getTime()
    );

    const datasets = SKILLS.map((skill) => {
      const series = labels.map((label) => {
        const bucket = buckets.get(label);
        if (!bucket || !bucket[skill] || bucket[skill].count === 0) {
          return null;
        }
        const value = bucket[skill].sum / bucket[skill].count;
        return Number(value.toFixed(2));
      });
      return applySmoothing(series, smoothingMode);
    });

    return finalizeTrend(labels, datasets);
  }

  function computeStudentTrend(
    history: AssessmentHistoryResponse | null,
    windowSize: WindowSize,
    smoothingMode: Smoothing
  ): TrendComputation {
    if (!history) {
      return emptyTrend();
    }

    const assessments = filterAssessments(history.assessments, windowSize);
    if (!assessments.length) {
      return emptyTrend();
    }

    const labels = assessments.map((assessment) => assessment.assessed_on);
    const datasets = SKILLS.map((skill) => {
      const series = assessments.map((assessment) => {
        const entry = assessment.skills.find((item) => item.skill === skill);
        return entry ? Number(entry.score.toFixed(2)) : null;
      });
      return applySmoothing(series, smoothingMode);
    });

    return finalizeTrend(labels, datasets);
  }

  function filterAssessments(
    assessments: AssessmentHistoryResponse['assessments'],
    windowSize: WindowSize
  ) {
    const sorted = [...assessments].sort(
      (a, b) => new Date(a.assessed_on).getTime() - new Date(b.assessed_on).getTime()
    );

    if (!sorted.length) {
      return [];
    }

    const lastDate = new Date(sorted[sorted.length - 1].assessed_on);
    const cutoff = new Date(lastDate);
    cutoff.setDate(cutoff.getDate() - windowSize * 7);

    return sorted.filter((assessment) => new Date(assessment.assessed_on) >= cutoff);
  }

  function applySmoothing(
    series: Array<number | null>,
    smoothingMode: Smoothing
  ): Array<number | null> {
    if (smoothingMode === 'none') {
      return series;
    }
    if (smoothingMode === 'simple') {
      return simpleMovingAverage(series);
    }
    return exponentialMovingAverage(series);
  }

  function simpleMovingAverage(
    series: Array<number | null>,
    windowLength = 3
  ): Array<number | null> {
    return series.map((_, index) => {
      const start = Math.max(0, index - windowLength + 1);
      const window = series.slice(start, index + 1).filter((value): value is number => value !== null);
      if (window.length === 0) {
        return null;
      }
      const avg = window.reduce((sum, value) => sum + value, 0) / window.length;
      return Number(avg.toFixed(2));
    });
  }

  function exponentialMovingAverage(
    series: Array<number | null>,
    alpha = 0.3
  ): Array<number | null> {
    let previous: number | null = null;
    return series.map((value) => {
      if (value === null) {
        return previous;
      }
      previous = previous === null ? value : alpha * value + (1 - alpha) * previous;
      return Number(previous.toFixed(2));
    });
  }

  function finalizeTrend(
    labels: string[],
    datasets: Array<Array<number | null>>
  ): TrendComputation {
    const displayLabels = labels.map((label) => DATE_FORMAT.format(new Date(label)));
    const metrics = computeMetrics(labels, datasets);
    const snapshots = computeSnapshots(datasets);

    return {
      labels,
      displayLabels,
      datasets,
      metrics,
      snapshots
    };
  }

  function computeMetrics(
    labels: string[],
    datasets: Array<Array<number | null>>
  ): TrendMetrics {
    const averages = labels.map((_, index) => {
      const values = datasets
        .map((series) => series[index])
        .filter((value): value is number => value !== null);
      if (!values.length) {
        return null;
      }
      const average = values.reduce((sum, value) => sum + value, 0) / values.length;
      return Number(average.toFixed(2));
    });

    const valid = averages.filter((value): value is number => value !== null);
    const first = valid[0] ?? null;
    const last = valid[valid.length - 1] ?? null;
    const momentum =
      first !== null && last !== null ? Number((last - first).toFixed(1)) : null;
    const stability =
      valid.length > 1
        ? Number((Math.max(...valid) - Math.min(...valid)).toFixed(1))
        : null;
    const trajectory =
      momentum === null
        ? 'No data'
        : momentum > 1.5
        ? 'Improving'
        : momentum < -1.5
        ? 'Declining'
        : 'Stable';
    const lastUpdated = labels.length ? labels[labels.length - 1] : null;

    return { momentumScore: momentum, trajectory, stability, lastUpdated };
  }

  function computeSnapshots(datasets: Array<Array<number | null>>): SkillSnapshot[] {
    return SKILLS.map((skill, index) => {
      const series = datasets[index];
      const first = series.find((value): value is number => value !== null) ?? null;
      const last =
        [...series].reverse().find((value): value is number => value !== null) ?? null;
      const change =
        first !== null && last !== null ? Number((last - first).toFixed(1)) : null;
      return {
        skill,
        label: SKILL_LABELS[skill],
        latest: last,
        change
      };
    });
  }

  function emptyTrend(): TrendComputation {
    return {
      labels: [],
      displayLabels: [],
      datasets: SKILLS.map(() => []),
      metrics: {
        momentumScore: null,
        trajectory: 'No data',
        stability: null,
        lastUpdated: null
      },
      snapshots: SKILLS.map((skill) => ({
        skill,
        label: SKILL_LABELS[skill],
        latest: null,
        change: null
      }))
    };
  }

  function refreshChart(computation: TrendComputation) {
    console.log('[Trends Debug] refreshChart called:', {
      hasCanvas: !!chartCanvas,
      labelsCount: computation.labels.length,
      datasetsCount: computation.datasets.length
    });

    if (!chartCanvas) {
      console.log('[Trends Debug] No canvas element yet');
      if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
      }
      return;
    }

    if (!computation.labels.length) {
      console.log('[Trends Debug] No data to display');
      if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
      }
      return;
    }

    const context = chartCanvas.getContext('2d');
    if (!context) return;

    const datasets = SKILLS.map((skill, index) => ({
      label: SKILL_LABELS[skill],
      data: computation.datasets[index],
      borderColor: SKILL_COLORS[skill],
      pointBackgroundColor: SKILL_COLORS[skill],
      pointRadius: 2,
      pointHoverRadius: 4,
      tension: smoothing === 'none' ? 0.1 : 0.25,
      borderWidth: 2,
      spanGaps: true
    }));

    if (chartInstance) {
      chartInstance.destroy();
    }

    console.log('[Trends Debug] Creating chart with data:', {
      labels: computation.displayLabels,
      datasetsLength: datasets.length,
      firstDataset: datasets[0]?.data.slice(0, 5)
    });

    chartInstance = new Chart(context, {
      type: 'line',
      data: {
        labels: computation.displayLabels,
        datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: '#b3b3b3'
            }
          }
        },
        interaction: {
          intersect: false,
          mode: 'index'
        },
        scales: {
          x: {
            ticks: {
              color: '#b3b3b3'
            },
            grid: {
              color: 'rgba(179, 179, 179, 0.08)'
            }
          },
          y: {
            min: 0,
            max: 100,
            ticks: {
              color: '#b3b3b3'
            },
            grid: {
              color: 'rgba(179, 179, 179, 0.08)'
            }
          }
        }
      }
    });
  }

  function formatMetric(value: number | null, decimals = 1) {
    return value !== null ? value.toFixed(decimals) : '—';
  }

  function formatSnapshotValue(value: number | null) {
    return value !== null ? value.toFixed(1) : '—';
  }

  function formatSnapshotChange(value: number | null) {
    if (value === null) return 'Δ 0.0';
    const sign = value > 0 ? '+' : '';
    return `Δ ${sign}${value.toFixed(1)}`;
  }

  function formatLastUpdated(value: string | null) {
    return value ? LONG_DATE_FORMAT.format(new Date(value)) : '—';
  }

  $: trendComputation = computeTrendData(
    mode,
    classHistories,
    selectedStudentHistory,
    windowWeeks,
    smoothing
  );
  $: metrics = trendComputation.metrics;
  $: skillSnapshots = trendComputation.snapshots;
  $: refreshChart(trendComputation);

  onMount(async () => {
    if (!classHistoriesMap[selectedClass]) {
      await ensureClassData(selectedClass);
    }
    if (mode === 'student') {
      if (!selectedStudentId && classStudents.length > 0) {
        selectedStudentId = classStudents[0].student_id;
      }
      if (selectedStudentId) {
        await ensureStudentHistory(selectedStudentId);
      }
    }
  });

  onDestroy(() => {
    if (chartInstance) {
      chartInstance.destroy();
      chartInstance = null;
    }
  });
</script>

<svelte:head>
  <title>Trends · AssessMax</title>
</svelte:head>

<div class="space-y-8">
  <section class="pulse-card drop-in-1 space-y-6">
    <div class="pulse-subheading">Trend Controls</div>
    <div class="flex flex-wrap gap-4">
      <label class="pulse-form-field w-44">
        <span class="text-sm text-muted">Window (weeks)</span>
        <select class="input-select" value={windowWeeks} on:change={handleWindowChange}>
          <option value="4">4 weeks</option>
          <option value="8">8 weeks</option>
          <option value="12">12 weeks</option>
        </select>
      </label>
      <label class="pulse-form-field w-44">
        <span class="text-sm text-muted">View Mode</span>
        <select class="input-select" value={mode} on:change={handleModeChange}>
          <option value="class">Class</option>
          <option value="student">Student</option>
        </select>
      </label>
      <label class="pulse-form-field w-48">
        <span class="text-sm text-muted">Smoothing</span>
        <select class="input-select" value={smoothing} on:change={handleSmoothingChange}>
          <option value="none">None</option>
          <option value="simple">Simple Moving Avg</option>
          <option value="ema">Exponentially Weighted</option>
        </select>
      </label>
      <label class="pulse-form-field w-56">
        <span class="text-sm text-muted">Class</span>
        <select class="input-select" value={selectedClass} on:change={handleClassChange}>
          {#each CLASS_OPTIONS as option}
            <option value={option.id}>{option.label}</option>
          {/each}
        </select>
      </label>
      {#if mode === 'student'}
        <label class="pulse-form-field w-64">
          <span class="text-sm text-muted">Student</span>
          <select
            class="input-select"
            value={selectedStudentId}
            on:change={handleStudentChange}
            disabled={classStudents.length === 0}
          >
            {#if classStudents.length === 0}
              <option value="">No students available</option>
            {:else}
              {#each classStudents as student}
                <option value={student.student_id}>
                  {student.name ?? student.student_id.slice(0, 8)}
                </option>
              {/each}
            {/if}
          </select>
        </label>
      {/if}
      <button class="pulse-button" type="button" on:click={handleRefresh} disabled={loading}>
        {#if loading}
          Refreshing…
        {:else}
          Refresh Trends
        {/if}
      </button>
    </div>

    {#if loading}
      <div class="text-sm text-muted font-mono">{ACTIVE_MESSAGE}</div>
    {/if}
    {#if fetchError}
      <div class="pulse-notification error" role="alert">{fetchError}</div>
    {/if}
    {#if additionalErrors.length > 0}
      <div class="pulse-notification space-y-1">
        {#each additionalErrors as error, index (index)}
          <div class="text-sm">{error}</div>
        {/each}
      </div>
    {/if}
  </section>

  <section class="pulse-card drop-in-2 space-y-6">
    <div class="pulse-subheading">Momentum Metrics</div>
    <div class="grid gap-4 md:grid-cols-4">
      <div class="pulse-metric">
        <div class="pulse-metric-value">{formatMetric(metrics.momentumScore)}</div>
        <p class="text-muted">Momentum Score</p>
      </div>
      <div class="pulse-metric">
        <div class="pulse-metric-value text-sm">{metrics.trajectory}</div>
        <p class="text-muted">Trajectory</p>
      </div>
      <div class="pulse-metric">
        <div class="pulse-metric-value">{formatMetric(metrics.stability)}</div>
        <p class="text-muted">Stability Range</p>
      </div>
      <div class="pulse-metric">
        <div class="pulse-metric-value text-xs">{formatLastUpdated(metrics.lastUpdated)}</div>
        <p class="text-muted">Last Updated</p>
      </div>
    </div>
  </section>

  <section class="pulse-card drop-in-3 space-y-6">
    <div class="pulse-subheading">Trend Visualizations</div>
    <div class="h-[360px] rounded-xl border border-[color:var(--border-color)] bg-[color:var(--background)]/60 flex items-center justify-center">
      {#if trendComputation.labels.length === 0}
        <div class="text-muted text-sm">
          {#if loading}
            Loading trend data…
          {:else}
            No trend data available for the selected filters.
          {/if}
        </div>
      {:else}
        <canvas bind:this={chartCanvas} class="w-full h-full"></canvas>
      {/if}
    </div>
    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
      {#each skillSnapshots as snapshot}
        <div class="card-bordered space-y-2">
          <div class="text-sm text-muted uppercase tracking-wide">{snapshot.label}</div>
          <div class="text-2xl font-semibold" style={`color: ${SKILL_COLORS[snapshot.skill]}`}>
            {formatSnapshotValue(snapshot.latest)}
          </div>
          <div class="text-xs text-muted">{formatSnapshotChange(snapshot.change)}</div>
        </div>
      {/each}
    </div>
  </section>
</div>
