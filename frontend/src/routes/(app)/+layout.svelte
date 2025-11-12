<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import authStore, { authUser, clearAuth } from '$lib/stores/auth';
  import { ROUTES } from '$lib/config';

  const navLinks = [
    { label: 'Class Overview', href: ROUTES.classOverview },
    { label: 'Student Detail', href: ROUTES.studentDetail },
    { label: 'Trends', href: ROUTES.trends },
    { label: 'Uploads & Jobs', href: ROUTES.uploadsJobs }
  ];

  let authed = false;
  let initialized = false;

  onMount(() => {
    const unsubscribe = authStore.subscribe(($auth) => {
      authed = Boolean($auth.token);
      initialized = $auth.initialized;
      if ($auth.initialized && !$auth.token) {
        goto(ROUTES.login, { replaceState: true });
      }
    });

    return () => unsubscribe();
  });

  $: currentPath = $page.url.pathname;
  const userStore = authUser;
</script>

{#if initialized && authed}
  <div class="pulse-layout">
    <aside class="pulse-sidebar">
      <div class="sidebar-logo">ASSESSMAX</div>
      <div class="pulse-divider"></div>
      <div class="pulse-sidebar-section">
        <div class="pulse-sidebar-heading">Navigation</div>
        <nav class="pulse-nav">
          {#each navLinks as link}
            <a
              class={`pulse-nav-item ${currentPath === link.href ? 'is-active' : ''}`}
              href={link.href}
            >
              {link.label}
            </a>
          {/each}
        </nav>
      </div>

      <div class="pulse-divider"></div>
      {#if $userStore}
        <div class="pulse-sidebar-section">
          <div class="pulse-sidebar-heading">Educator</div>
          <div class="pulse-user-card">
            <div class="pulse-user-name">{$userStore.displayName ?? $userStore.username}</div>
            <div class="pulse-user-roles">Roles · {($userStore.roles ?? ['educator']).join(', ')}</div>
          </div>
        </div>
      {/if}
      <button class="pulse-button w-full mt-auto" on:click={() => clearAuth(true)}>Logout</button>
    </aside>
    <main class="pulse-main">
      <slot />
    </main>
  </div>
{:else}
  <div class="pulse-page" data-state="loading">
    <div class="pulse-card drop-in">
      <div class="pulse-subheading">Loading Session</div>
      <div class="pulse-metric-value">Checking authentication…</div>
      <p class="text-muted">Hold tight while we verify your educator credentials.</p>
    </div>
  </div>
{/if}
