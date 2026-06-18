/**
 * The dataset is the core domain concept of this dashboard (replaces the
 * template's "user" semantic). Today there is exactly one dataset: SEED-V.
 *
 * Each dataset declares an `apiSegment` that the request proxy injects into
 * the forwarded path — see `next.config.mjs` rewrites. The `id` is the value
 * stored in the `active_dataset` preference cookie.
 */

// Keep in sync with `datasets` below. A tuple literal is required so the
// `DatasetId` union narrows to literal ids rather than `string`.
export const DATASET_IDS = ["seed-v"] as const;
export type DatasetId = (typeof DATASET_IDS)[number];

export type Dataset = {
  /** Stable identifier; also the `active_dataset` cookie value. */
  id: DatasetId;
  /** Display name. */
  name: string;
  /** Short human description shown in the switcher. */
  description: string;
  /** Path segment injected into `/api/<segment>/...` by the proxy. */
  apiSegment: string;
};

export const datasets: Dataset[] = [
  {
    id: "seed-v",
    name: "SEED-V",
    description: "5-class emotion EEG dataset (16 subjects × 3 sessions)",
    apiSegment: "seed-v",
  },
];

export const defaultDataset = datasets[0];

export function getDatasetById(id: string | null | undefined): Dataset {
  return datasets.find((d) => d.id === id) ?? defaultDataset;
}
