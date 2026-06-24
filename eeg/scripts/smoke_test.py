"""Smoke test: process subject 1 session 1 only and verify output."""
import sys, os
# scripts/ is inside the eeg repo root; add parent dir (eeg/) to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seed_v.preprocess import PreprocessConfig, preprocess_cnt
from seed_v.features import DeConfig, extract_de, compare_with_official
from seed_v.constants import N_EEG_CHANNELS, N_TRIALS_PER_SESSION, LABELS
import numpy as np

print("=== SMOKE TEST: subject 1, session 1 ===\n")

# 1. Preprocess
cfg = PreprocessConfig()
print(f"Config: {cfg}")
rec = preprocess_cnt("1_1_20180804.cnt", cfg)
print(f"Subject: {rec.subject}, Session: {rec.session}, sfreq: {rec.sfreq}")
print(f"Channels: {len(rec.ch_names)} ({rec.ch_names[:3]}...{rec.ch_names[-3:]})")
print(f"Trials: {len(rec.trials)}")
assert len(rec.trials) == N_TRIALS_PER_SESSION, f"Expected 15 trials, got {len(rec.trials)}"

for t in rec.trials:
    print(f"  trial {t.index:2d}: label={t.label_code} ({[k for k,v in LABELS.items() if v==t.label_code][0]:>8s}) "
          f"  dur={t.end_s - t.start_s:4d}s  samples={t.data.shape[1]}  shape={t.data.shape}")
    assert t.data.shape[0] == N_EEG_CHANNELS, f"Expected 62 channels, got {t.data.shape[0]}"
    assert t.data.dtype == np.float32

# Check sfreq
assert abs(rec.sfreq - 200.0) < 0.1, f"Expected sfreq ~200, got {rec.sfreq}"

# Check trial durations match (allow ±1 sample)
for t in rec.trials:
    expected_samples = int(round((t.end_s - t.start_s) * rec.sfreq))
    actual_samples = t.data.shape[1]
    diff = abs(expected_samples - actual_samples)
    assert diff <= 1, f"Trial {t.index}: expected ~{expected_samples} samples, got {actual_samples}"

print("\n--- All trial assertions passed ---")

# 2. DE extraction on first trial
de_cfg = DeConfig()
de0 = extract_de(rec.trials[0].data, rec.sfreq, de_cfg)
print(f"\nDE trial 0: shape={de0.shape}, dtype={de0.dtype}")
assert de0.shape[1] == N_EEG_CHANNELS
assert de_cfg.window_s == 4.0
# Expected windows: trial 0 is 72s at 200Hz, 4s window -> 18 windows (matches official)
trial_dur = rec.trials[0].end_s - rec.trials[0].start_s
expected_windows = int(trial_dur // de_cfg.window_s)
print(f"  Trial 0 duration: {trial_dur}s, expected ~{expected_windows} windows, got {de0.shape[0]}")
print(f"  DE range: [{de0.min():.3f}, {de0.max():.3f}], mean={de0.mean():.3f}")

# 3. Compare with official DE
print("\n--- Official DE comparison ---")
comp = compare_with_official(rec, de_cfg)
print(f"Mean Pearson r: {comp.get('mean_pearson_r')}")
if comp.get("per_trial"):
    for pt in comp["per_trial"][:3]:
        if "pearson_r" in pt:
            print(f"  trial {pt['trial']}: r={pt['pearson_r']}, mae={pt['mae']}, "
                  f"windows_official={pt['n_windows_official']}, windows_ours={pt['n_windows_ours']}")

print("\n=== SMOKE TEST COMPLETE ===")
