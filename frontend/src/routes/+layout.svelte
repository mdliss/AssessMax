<script lang="ts">
  import '../app.postcss';
  import { onMount } from 'svelte';
  import { initializeAuthFromStorage } from '$lib/stores/auth';

  onMount(() => {
    initializeAuthFromStorage();
  });
</script>

<slot />
