/**
 * Types for the SEED-V dataset `/info` endpoint.
 * Shape verified against the live `GET /api/seed-v/info` response.
 */

export type SeedVDatasetSummary = {
  n_subjects: number;
  n_sessions: number;
  n_trials_per_session: number;
  n_eeg_channels: number;
  aux_channels: string[];
  sample_rate: number;
  n_emotions: number;
};

export type SeedVPaths = {
  raw_dir: string;
  processed_dir: string;
};

/**
 * One EEG electrode.
 * Coordinates are polar as served by the backend:
 *   `x` = angle in degrees (0° = anterior/front, 90° = right, 180° = posterior/back, -90° = left)
 *   `y` = normalized radius from the vertex (0 = center, ~0.51 = rim)
 */
export type SeedVChannel = {
  name: string;
  x: number;
  y: number;
};

export type SeedVTrialTimestamp = {
  trial: number;
  start_s: number;
  end_s: number;
  duration_s: number;
  samples: number;
};

/** Keyed by session id ("1" | "2" | "3"). */
export type SeedVSessionTrials = Record<string, SeedVTrialTimestamp[]>;

export type SeedVScores = {
  n_subjects: number;
  n_sessions: number;
  n_rows: number;
  trial_mean: number;
  trial_min: number;
  trial_max: number;
};

export type SeedVParticipants = {
  n: number;
  sex_counts: { F: number; M: number };
  age_min: number;
  age_max: number;
};

export type SeedVInfo = {
  dataset: SeedVDatasetSummary;
  paths: SeedVPaths;
  channels: SeedVChannel[];
  labels: Record<string, number>;
  label_names: Record<string, string>;
  stimuli_order: Record<string, string[]>;
  trial_timestamps: SeedVSessionTrials;
  scores: SeedVScores;
  participants: SeedVParticipants;
};
