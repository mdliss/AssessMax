<script lang="ts">
  import { goto } from '$app/navigation';
  import { get } from 'svelte/store';
  import { isAuthenticated, loginWithMockCredentials } from '$lib/stores/auth';
  import { ROUTES } from '$lib/config';
  import { onMount } from 'svelte';

  let username = '';
  let password = '';
  let error: string | null = null;
  let loading = false;

  onMount(() => {
    if (get(isAuthenticated)) {
      goto(ROUTES.classOverview, { replaceState: true });
    }
  });

  const demoCredentials = [
    { label: 'Username', value: 'Any non-empty string' },
    { label: 'Password', value: 'Any non-empty string' }
  ];

  async function handleSubmit() {
    error = null;
    loading = true;
    try {
      await loginWithMockCredentials(username.trim(), password.trim());
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unable to login';
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>PulseMax Educator Login</title>
</svelte:head>

<div class="pulse-page">
  <div class="max-w-xl w-full space-y-8">
    <div class="pulse-card drop-in-1">
      <div class="pulse-subheading">Authentication</div>
      <div class="pulse-metric-value">Welcome Back</div>
      <p class="text-muted">Enter your credentials to access the PulseMax command center.</p>
    </div>

    <form
      class="pulse-card drop-in-2 space-y-6"
      on:submit|preventDefault={handleSubmit}
      aria-label="Educator login form"
    >
      <div class="pulse-subheading">Credentials</div>
      <div class="space-y-4">
        <label class="pulse-form-field">
          <span class="text-sm text-muted">Username</span>
          <input
            class="input-text bg-[color:var(--card-bg)]"
            bind:value={username}
            required
            autocomplete="username"
          />
        </label>
        <label class="pulse-form-field">
          <span class="text-sm text-muted">Password</span>
          <input
            class="input-text bg-[color:var(--card-bg)]"
            type="password"
            bind:value={password}
            required
            autocomplete="current-password"
          />
        </label>
      </div>

      {#if error}
        <div class="pulse-notification error animate-shake" role="alert">{error}</div>
      {/if}

      <button class="pulse-button w-full" type="submit" disabled={loading}>
        {#if loading}
          <span class="loading inline-flex h-4 w-4 rounded-full border-2 border-[var(--background)] border-t-transparent"></span>
          Authenticating…
        {:else}
          Login
        {/if}
      </button>
    </form>

    <div class="pulse-card drop-in-3">
      <div class="pulse-subheading">Demo Credentials (Development Mode)</div>
      <ul class="mt-3 space-y-2">
        {#each demoCredentials as cred}
          <li class="flex justify-between text-sm text-muted">
            <span class="font-mono text-[var(--foreground)]">{cred.label}</span>
            <span>{cred.value}</span>
          </li>
        {/each}
      </ul>
    </div>
  </div>
</div>
