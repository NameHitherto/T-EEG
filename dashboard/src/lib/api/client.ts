/**
 * Central API client. The active dataset segment is injected by the request
 * proxy (next.config.mjs rewrites), so callers stay dataset-agnostic:
 *
 *   apiFetch("/signals")
 *     → fetches `/api/signals`
 *     → proxy rewrites to `<BACKEND>/api/<active-dataset-segment>/signals`
 *
 * Isomorphic: usable from both Server Components and Client Components —
 * next.config.mjs rewrites apply to in-process server fetches too.
 *
 * Per spec.md §6, never pull large EEG signal arrays through this as a single
 * JSON payload — use paginated / chunked / streaming endpoints instead.
 */

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public path: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });

  if (!res.ok) {
    throw new ApiError(res.status, `API ${res.status}: ${path}`, path);
  }

  const text = await res.text();
  return (text ? JSON.parse(text) : null) as T;
}
