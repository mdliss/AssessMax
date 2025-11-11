import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { derived, writable } from 'svelte/store';
import { ROUTES, STORAGE_KEYS } from '../config';

type AuthUser = {
  username: string;
  displayName?: string;
  roles?: string[];
};

export interface AuthState {
  token: string | null;
  user: AuthUser | null;
  initialized: boolean;
}

const defaultState: AuthState = {
  token: null,
  user: null,
  initialized: false
};

function loadInitialState(): AuthState {
  if (!browser) return { ...defaultState };

  const storedToken = localStorage.getItem(STORAGE_KEYS.token);
  const storedUser = localStorage.getItem(STORAGE_KEYS.user);

  return {
    token: storedToken,
    user: storedUser ? JSON.parse(storedUser) : null,
    initialized: true
  } satisfies AuthState;
}

function persist(state: AuthState) {
  if (!browser) return;

  if (state.token) {
    localStorage.setItem(STORAGE_KEYS.token, state.token);
  } else {
    localStorage.removeItem(STORAGE_KEYS.token);
  }

  if (state.user) {
    localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(state.user));
  } else {
    localStorage.removeItem(STORAGE_KEYS.user);
  }
}

const authStore = writable<AuthState>(loadInitialState());

if (browser) {
  // ensure initialized flag is set on first run
  authStore.update((state) => ({ ...state, initialized: true }));
}

export const isAuthenticated = derived(authStore, ($auth) => Boolean($auth.token));

export const authUser = derived(authStore, ($auth) => $auth.user);

export function setToken(token: string, user: AuthUser | null = null) {
  authStore.update((state) => {
    const nextState = { ...state, token, user: user ?? state.user } satisfies AuthState;
    persist(nextState);
    return nextState;
  });
}

export function clearAuth(redirect = true) {
  authStore.update(() => {
    const nextState = { ...defaultState, initialized: true } satisfies AuthState;
    persist(nextState);
    return nextState;
  });
  if (redirect && browser) {
    goto(ROUTES.login, { replaceState: true });
  }
}

export async function loginWithMockCredentials(username: string, password: string) {
  if (!username || !password) {
    throw new Error('Username and password are required');
  }

  const mockToken = `mock_token_${username}`;
  const user: AuthUser = {
    username,
    displayName: username,
    roles: ['educator']
  };

  setToken(mockToken, user);
  if (browser) {
    await goto(ROUTES.classOverview, { replaceState: true });
  }
}

export function initializeAuthFromStorage() {
  if (!browser) return;
  authStore.update((state) => {
    const stored = loadInitialState();
    return { ...state, ...stored, initialized: true } satisfies AuthState;
  });
}

export default authStore;
