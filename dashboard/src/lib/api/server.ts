import { cookies, headers } from "next/headers";

import { ApiError } from "./client";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";

/**
 * Server-only fetch that goes through the app's own origin so
 * `next.config.mjs` rewrites apply (including the active-dataset wrapping).
 *
 * Node's `fetch` rejects relative URLs, so we rebuild the absolute origin
 * from request headers. We also forward the user's cookies verbatim — that
 * lets the rewrite's `has: cookie active_dataset=<id>` condition match the
 * user's actual selection instead of falling back to the default dataset.
 *
 * Only call this from Server Components / Route Handlers / Server Actions.
 */
export async function apiFetchServer<T>(path: string, init?: RequestInit): Promise<T> {
  const [h, cookieStore] = await Promise.all([headers(), cookies()]);

  const proto = h.get("x-forwarded-proto") ?? "http";
  const host = h.get("x-forwarded-host") ?? h.get("host") ?? "localhost:3000";
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

  const res = await fetch(`${proto}://${host}${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(cookieHeader ? { cookie: cookieHeader } : {}),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    throw new ApiError(res.status, `API ${res.status}: ${path}`, path);
  }

  const text = await res.text();
  return (text ? JSON.parse(text) : null) as T;
}
