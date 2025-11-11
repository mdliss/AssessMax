import { get } from 'svelte/store';
import authStore from '../stores/auth';
import { API_BASE_URL, API_TIMEOUT, CACHE_TTL_MS } from '../config';

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

interface RequestOptions<T> {
  method?: HttpMethod;
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined>;
  headers?: Record<string, string>;
  cacheKey?: string;
  ttl?: number;
  useCache?: boolean;
  fallback?: () => Promise<T> | T;
  signal?: AbortSignal;
}

interface CacheEntry {
  expiry: number;
  data: unknown;
}

const responseCache = new Map<string, CacheEntry>();

function buildUrl(path: string, params?: RequestOptions<unknown>['params']) {
  const url = /^https?:\/\//i.test(path)
    ? new URL(path)
    : new URL(path.replace(/^(\/)+/, ''), API_BASE_URL);

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value === undefined || value === null) return;
      url.searchParams.set(key, String(value));
    });
  }

  return url;
}

function getAuthHeaders(): Record<string, string> {
  const { token } = get(authStore);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function fromCache<T>(key: string): T | null {
  const cached = responseCache.get(key);
  if (!cached) return null;
  if (Date.now() > cached.expiry) {
    responseCache.delete(key);
    return null;
  }
  return cached.data as T;
}

function storeCache(key: string, data: unknown, ttl: number) {
  responseCache.set(key, { data, expiry: Date.now() + ttl });
}

export function clearCache(prefix?: string) {
  if (!prefix) {
    responseCache.clear();
    return;
  }
  [...responseCache.keys()].forEach((key) => {
    if (key.startsWith(prefix)) {
      responseCache.delete(key);
    }
  });
}

export async function apiRequest<T>(path: string, options: RequestOptions<T> = {}): Promise<T> {
  const {
    method = 'GET',
    body,
    params,
    headers = {},
    cacheKey,
    ttl = CACHE_TTL_MS,
    useCache = method === 'GET',
    fallback,
    signal
  } = options;

  const key = cacheKey ?? `${method}:${path}:${JSON.stringify(params ?? {})}`;
  if (useCache) {
    const hit = fromCache<T>(key);
    if (hit) return hit;
  }

  const url = buildUrl(path, params);

  const controller = !signal ? new AbortController() : null;
  const timeoutId = controller
    ? setTimeout(() => {
        controller.abort();
      }, API_TIMEOUT)
    : null;

  const requestHeaders: Record<string, string> = {
    ...getAuthHeaders(),
    ...headers
  };

  if (body !== undefined && body !== null && method !== 'GET') {
    requestHeaders['Content-Type'] = requestHeaders['Content-Type'] ?? 'application/json';
  }

  try {
    const response = await fetch(url, {
      method,
      headers: requestHeaders,
      body: body && method !== 'GET' ? JSON.stringify(body) : undefined,
      signal: signal ?? controller?.signal
    });

    if (!response.ok) {
      throw new Error(`API request failed with ${response.status}: ${response.statusText}`);
    }

    const data = (await response.json()) as T;

    if (useCache) {
      storeCache(key, data, ttl);
    }

    return data;
  } catch (error) {
    if (fallback) {
      const data = await fallback();
      if (useCache) {
        storeCache(key, data, ttl);
      }
      return data;
    }
    throw error;
  } finally {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  }
}

export async function apiGet<T>(path: string, options: Omit<RequestOptions<T>, 'method' | 'body'> = {}) {
  return apiRequest<T>(path, { ...options, method: 'GET' });
}

export async function apiPost<T>(path: string, body: unknown, options: Omit<RequestOptions<T>, 'method' | 'body'> = {}) {
  return apiRequest<T>(path, { ...options, method: 'POST', body });
}
