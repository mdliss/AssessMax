<script lang="ts">
  import { clearCache } from '$lib/api/client';

  let activeTab: 'uploads' | 'status' | 'history' = 'uploads';

  function setTab(tab: typeof activeTab) {
    activeTab = tab;
  }

  function refreshJobs() {
    clearCache('GET:/v1/jobs');
  }
</script>

<svelte:head>
  <title>Uploads & Jobs · PulseMax</title>
</svelte:head>

<div class="space-y-8">
  <section class="pulse-card drop-in-1 space-y-4">
    <div class="pulse-subheading">Pipeline Pulse</div>
    <div class="grid gap-4 md:grid-cols-4">
      <div class="pulse-metric">
        <div class="pulse-metric-value">—</div>
        <p class="text-muted">Jobs Today</p>
      </div>
      <div class="pulse-metric">
        <div class="pulse-metric-value">—</div>
        <p class="text-muted">Success Rate</p>
      </div>
      <div class="pulse-metric">
        <div class="pulse-metric-value">—</div>
        <p class="text-muted">Median Duration</p>
      </div>
      <div class="pulse-metric">
        <div class="pulse-metric-value">—</div>
        <p class="text-muted">Active Batches</p>
      </div>
    </div>
  </section>

  <section class="pulse-card drop-in-2 space-y-6">
    <div class="flex gap-3 flex-wrap">
      <button class={`btn-outline ${activeTab === 'uploads' ? 'bg-[color:var(--accent)] text-[color:var(--background)]' : ''}`} type="button" on:click={() => setTab('uploads')}>
        Upload Files
      </button>
      <button class={`btn-outline ${activeTab === 'status' ? 'bg-[color:var(--accent)] text-[color:var(--background)]' : ''}`} type="button" on:click={() => setTab('status')}>
        Job Status
      </button>
      <button class={`btn-outline ${activeTab === 'history' ? 'bg-[color:var(--accent)] text-[color:var(--background)]' : ''}`} type="button" on:click={() => setTab('history')}>
        Upload History
      </button>
    </div>

    {#if activeTab === 'uploads'}
      <div class="grid gap-6 lg:grid-cols-2">
        <div class="card-bordered space-y-4">
          <div class="pulse-subheading">Transcript Upload</div>
          <p class="text-muted text-sm">Supports JSONL, CSV, TXT up to 50MB. Metadata mirrors Streamlit form.</p>
          <button class="pulse-button" type="button">Choose Files</button>
        </div>
        <div class="card-bordered space-y-4">
          <div class="pulse-subheading">Artifact Upload</div>
          <p class="text-muted text-sm">PDF, DOCX, PNG, JPG with metadata (student, date, type, subject, description).</p>
          <button class="pulse-button" type="button">Choose Files</button>
        </div>
      </div>
    {:else if activeTab === 'status'}
      <div class="space-y-4">
        <div class="flex flex-wrap gap-3">
          <input class="input-text w-64" placeholder="Search job ID" />
          <select class="input-select w-48">
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="running">Running</option>
            <option value="succeeded">Succeeded</option>
            <option value="failed">Failed</option>
          </select>
          <button class="btn-outline" type="button" on:click={refreshJobs}>Refresh</button>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="text-muted uppercase tracking-wider">
              <tr>
                <th class="py-2 pr-6">Job ID</th>
                <th class="py-2 pr-6">Class</th>
                <th class="py-2 pr-6">Status</th>
                <th class="py-2 pr-6">Start</th>
                <th class="py-2 pr-6">End</th>
                <th class="py-2 pr-6">Error</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="py-3 pr-6 font-mono text-xs">—</td>
                <td class="py-3 pr-6">—</td>
                <td class="py-3 pr-6">—</td>
                <td class="py-3 pr-6">—</td>
                <td class="py-3 pr-6">—</td>
                <td class="py-3 pr-6">—</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    {:else}
      <div class="h-[320px] rounded-xl border border-[color:var(--border-color)] flex items-center justify-center text-muted">
        Upload history bar chart placeholder
      </div>
    {/if}
  </section>
</div>
