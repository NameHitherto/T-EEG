import { apiFetchServer } from "@/lib/api/server";
import type { SeedVInfo } from "@/types/seed-v";

/**
 * Fetch the active dataset's `/info`. The active-dataset segment is injected
 * by the request proxy, so this stays dataset-agnostic on the wire:
 * `apiFetchServer("/info")` → `<BACKEND>/api/<active-dataset-segment>/info`.
 *
 * Server-only (Server Component data fetching). For Client Components, use
 * `apiFetch` from `@/lib/api/client` with the same path.
 *
 * The response type is SEED-V-specific today (the only dataset); add sibling
 * modules when more datasets land.
 */
export function getDatasetInfo(): Promise<SeedVInfo> {
  return apiFetchServer<SeedVInfo>("/info");
}
