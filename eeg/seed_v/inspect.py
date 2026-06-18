"""Pretty-print SEED-V dataset metadata to stdout.

Run ``python -m seed-v`` (from the repository root) to invoke
:func:`print_dataset_info`.
"""

from __future__ import annotations

from . import config
from .constants import AUX_CHANNELS, LABELS, LABEL_NAMES, N_EEG_CHANNELS, SAMPLE_RATE
from .dataset import (
    load_channels,
    load_labels,
    load_participants,
    load_scores,
    load_stimuli_order,
    load_trial_timestamps,
)


def _header(title: str) -> None:
    bar = "=" * 70
    print(f"\n{bar}\n{title}\n{bar}")


def print_dataset_info() -> None:
    print(f"SEED-V dataset\nRaw dir : {config.RAW_DIR}")
    print(f"Proc dir: {config.PROCESSED_DIR}")

    # --- 1. Channels -------------------------------------------------------
    channels = load_channels()
    _header(f"1. Channels ({N_EEG_CHANNELS} EEG + {len(AUX_CHANNELS)} auxiliary)")
    names = [ch.name for ch in channels]
    # Wrap channel names ~12 per line for readability.
    per_line = 12
    for i in range(0, len(names), per_line):
        print("  " + "  ".join(f"{n:<5}" for n in names[i:i + per_line]))
    print(f"\n  EEG channels ({N_EEG_CHANNELS}): 10-20 system, see channel_62_pos.locs for (x, y).")
    print(f"  Auxiliary channels dropped before analysis: {AUX_CHANNELS}")
    print("    M1/M2 = left/right mastoid references; VEO/HEO = vertical/horizontal EOG.")

    # --- 2. Labels ---------------------------------------------------------
    labels = load_labels()
    _header("2. Emotion labels")
    for name, code in labels.items():
        print(f"  {code} : {name}")

    # --- 3. Stimuli order --------------------------------------------------
    stimuli = load_stimuli_order()
    _header("3. Stimuli order per session (15 trials = 3 blocks x 5 emotions)")
    for session, emotions in stimuli.items():
        print(f"\n  Session {session}:")
        # Group into blocks of 5 for readability.
        for block_idx in range(0, len(emotions), 5):
            block = emotions[block_idx:block_idx + 5]
            print(f"    block {block_idx // 5 + 1}: " + " -> ".join(block))

    # --- 4. Trial timestamps ----------------------------------------------
    timestamps = load_trial_timestamps()
    _header("4. Trial start/end timestamps (seconds, sampled at "
            f"{SAMPLE_RATE} Hz)")
    for session, trials in timestamps.items():
        print(f"\n  Session {session} ({len(trials)} trials):")
        print(f"    {'trial':>5} | {'start (s)':>9} | {'end (s)':>8} | "
              f"{'duration (s)':>12} | {'samples':>9}")
        for i, (start, end) in enumerate(trials, start=1):
            dur = end - start
            samples = dur * SAMPLE_RATE
            print(f"    {i:>5} | {start:>9} | {end:>8} | {dur:>12} | {samples:>9}")

    # --- 5. Scores ---------------------------------------------------------
    scores = load_scores()
    _header("5. Experiment scores (participant feedback)")
    print(f"  Subjects : {scores['subject'].nunique()}")
    print(f"  Sessions : {scores['session'].nunique()}")
    print(f"  Rows     : {len(scores)} (subject x session)")
    trial_cols = [c for c in scores.columns if c.startswith("trial_")]
    per_row_mean = scores[trial_cols].mean(axis=1)
    print(f"\n  Trial-score statistics (scale 1-5):")
    print(f"    mean   : {per_row_mean.mean():.3f}")
    print(f"    min    : {scores[trial_cols].min().min():.1f}")
    print(f"    max    : {scores[trial_cols].max().max():.1f}")
    print(f"\n  Sample rows (first subject, all 3 sessions):")
    sample = scores[scores["subject"] == scores["subject"].min()].copy()
    sample[trial_cols] = sample[trial_cols].astype(int)
    print(sample.to_string(index=False))

    # --- Bonus: participants ----------------------------------------------
    try:
        participants = load_participants()
        _header("Bonus: Participants")
        print(f"  N = {len(participants)}  "
              f"(sex: {dict(participants['sex'].value_counts())}, "
              f"age {participants['age'].min()}-{participants['age'].max()})")
    except Exception as exc:  # noqa: BLE001 - non-critical
        print(f"  (participants info unavailable: {exc})")

    print()


if __name__ == "__main__":
    print_dataset_info()
