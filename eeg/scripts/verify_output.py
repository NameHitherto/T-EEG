"""Final verification: load processed npz files and verify structure."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from pathlib import Path
from seed_v import config
from seed_v.constants import LABELS, N_EEG_CHANNELS, N_TRIALS_PER_SESSION, N_FREQ_BANDS

proc = config.PROCESSED_DIR
raw_dir = proc / "raw_signal"
de_dir = proc / "de_features"

print("=== FINAL VERIFICATION ===\n")

# Check file counts
raw_files = sorted(raw_dir.glob("*.npz"))
de_files = sorted(de_dir.glob("*.npz"))
print(f"raw_signal files: {len(raw_files)}")
print(f"de_features files: {len(de_files)}")
assert len(raw_files) == 48, f"Expected 48 raw files, got {len(raw_files)}"
assert len(de_files) == 48, f"Expected 48 DE files, got {len(de_files)}"

# Verify a few files in detail
for sub, ses in [(1, 1), (7, 1), (16, 3)]:
    name = f"sub{sub:02d}_ses{ses}.npz"
    print(f"\n--- {name} ---")

    # Raw signal
    raw = np.load(raw_dir / name, allow_pickle=True)
    data = raw["data"]
    labels = raw["labels"]
    sfreq = float(raw["sfreq"])
    ch_names = raw["ch_names"]
    durations = raw["trial_durations_s"]
    print(f"  raw: n_trials={len(data)}, sfreq={sfreq}, n_channels={data[0].shape[0]}")
    print(f"  labels: {labels}")
    print(f"  durations (s): {durations}")
    assert len(data) == N_TRIALS_PER_SESSION
    assert data[0].shape[0] == N_EEG_CHANNELS
    assert abs(sfreq - 200.0) < 0.1
    # Labels should be 0-4
    assert all(0 <= l <= 4 for l in labels)

    # DE features
    de = np.load(de_dir / name, allow_pickle=True)
    de_data = de["data"]
    de_labels = de["labels"]
    de_window = float(de["window_s"])
    print(f"  de: n_trials={len(de_data)}, shape per trial={de_data[0].shape}, window_s={de_window}")
    assert len(de_data) == N_TRIALS_PER_SESSION
    assert de_data[0].shape[1] == N_EEG_CHANNELS
    assert de_data[0].shape[2] == N_FREQ_BANDS
    assert abs(de_window - 4.0) < 0.01
    # Labels match
    assert np.array_equal(labels, de_labels)

# Verify label distribution: each emotion appears exactly 9 times per session
all_labels = []
for sub in range(1, 17):
    for ses in range(1, 4):
        raw = np.load(raw_dir / f"sub{sub:02d}_ses{ses}.npz", allow_pickle=True)
        all_labels.extend(raw["labels"].tolist())

from collections import Counter
label_counts = Counter(all_labels)
print(f"\nLabel distribution across all 48 sessions (720 trials):")
for code in range(5):
    name = [k for k, v in LABELS.items() if v == code][0]
    print(f"  {code} ({name:>8s}): {label_counts[code]}")
assert all(label_counts[c] == 144 for c in range(5)), "Expected 144 trials per emotion (16*3*3)"
print(f"\nTotal trials: {len(all_labels)} (expected 720)")

# Verify subject 7 session 1 (the repaired file) has proper 62 channels
s7 = np.load(raw_dir / "sub07_ses1.npz", allow_pickle=True)
print(f"\nSubject 7 ses1 (repaired): {s7['data'][0].shape} — 62 channels confirmed")

print("\n=== ALL CHECKS PASSED ===")
