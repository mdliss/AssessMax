<script lang="ts">
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { ROUTES } from '$lib/config';
  import { isAuthenticated } from '$lib/stores/auth';

  onMount(() => {
    const destination = get(isAuthenticated) ? ROUTES.classOverview : ROUTES.login;
    goto(destination, { replaceState: true });
  });
</script>

<div class="pulse-page" aria-busy="true">
  <div class="pulse-card drop-in-1">
    <div class="pulse-subheading">Routing</div>
    <div class="pulse-metric-value">Redirecting…</div>
    <p class="text-muted">Preparing the PulseMax workspace.</p>
  </div>
</div>
