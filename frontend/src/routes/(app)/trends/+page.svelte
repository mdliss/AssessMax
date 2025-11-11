<script lang="ts">
  import type { PageData } from './$types';
  import { clearCache } from '$lib/api/client';

  export let data: PageData;

  type Mode = 'class' | 'student';
  let mode: Mode = (data.initialMode as Mode) ?? 'class';
  let windowWeeks: 4 | 8 | 12 = 8;
  let smoothing: 'none' | 'simple' | 'ema' = 'simple';
  let classId = 'MS-7A';
  let studentId = '';

  function handleRefresh() {
    clearCache('GET:/v1/trends');
    // TODO: invoke API call and update charts/data
  }
</script>

<svelte:head>
  <title>Trends · PulseMax</title>
</svelte:head>

<div class="space-y-8">
  <section class="pulse-card drop-in-1 space-y-6">
    <div class="pulse-subheading">Trend Controls</div>
    <div class="flex flex-wrap gap-4">
      <label class="pulse-form-field w-48">
        <span class="text-sm text-muted">Window (weeks)</span>
        <select class="input-select" bind:value={windowWeeks}>
          <option value={4}>4 weeks</option>
          <option value={8}>8 weeks</option>
          <option value={12}>12 weeks</option>
        </select>
      </label>
      <label class="pulse-form-field w-56">
        <span class="text-sm text-muted">View Mode</span>
        <select class="input-select" bind:value={mode}>
          <option value="class">Class</option>
          <option value="student">Student</option>
        </select>
      </label>
      <label class="pulse-form-field w-56">
        <span class="text-sm text-muted">Smoothing</span>
        <select class="input-select" bind:value={smoothing}>
          <option value="none">None</option>
          <option value="simple">Simple Moving Avg</option>
          <option value="ema">Exponentially Weighted</option>
        </select>
      </label>
      <button class="pulse-button" type="button" on:click={handleRefresh}>
        Refresh Trends
      </button>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      {#if mode === 'class'}
        <label class="pulse-form-field">
          <span class="text-muted text-sm">Class Identifier</span>
          <input class="input-text" bind:value={classId} />
        </label>
      {:else}
        <label class="pulse-form-field">
          <span class="text-muted text-sm">Student UUID</span>
          <input class="input-text" bind:value={studentId} />
        </label>
      {/if}
    </div>

    <div class="pulse-notification">
      Demo mode activates when backend trends are unavailable. Synthetic series will match Streamlit output.
    </div>
  </section>

  <section class="pulse-card drop-in-2 space-y-6">
    <div class="pulse-subheading">Momentum Metrics</div>
    <div class="grid gap-4 md:grid-cols-4">
      <div class="pulse-metric">
        <div class="pulse-metric-value">—</div>
        <p class="text-muted">Momentum Score</p>
      </div>
      <div class="pulse-metric">
        <div class="pulse-metric-value">—</div>
        <p class="text-muted">Trajectory</p>
      </div>
      <div class="pulse-metric">
        <div class="pulse-metric-value">—</div>
        <p class="text-muted">Stability</p>
      </div>
      <div class="pulse-metric">
        <div class="pulse-metric-value">—</div>
        <p class="text-muted">Last Updated</p>
      </div>
    </div>
  </section>

  <section class="pulse-card drop-in-3 space-y-6">
    <div class="pulse-subheading">Trend Visualizations</div>
    <div class="h-[360px] rounded-xl border border-[color:var(--border-color)] flex items-center justify-center text-muted">
      Multi-series line chart placeholder
    </div>
    <div class="grid gap-4 lg:grid-cols-3">
      <div class="card-bordered h-64 flex items-center justify-center text-muted">Skill tab placeholder</div>
      <div class="card-bordered h-64 flex items-center justify-center text-muted">Skill tab placeholder</div>
      <div class="card-bordered h-64 flex items-center justify-center text-muted">Skill tab placeholder</div>
    </div>
  </section>
</div>
