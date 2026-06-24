"""Canonical SEED-V constants — file-independent ground truth and defaults.

These mirror the official SEED-V specification and are used both as fallback
values and as validation targets for the parsed metadata.
"""

from __future__ import annotations

# Five-class emotion labels used by SEED-V (name -> integer code).
LABELS: dict[str, int] = {
    "Disgust": 0,
    "Fear": 1,
    "Sad": 2,
    "Neutral": 3,
    "Happy": 4,
}

# Reverse mapping (integer code -> name).
LABEL_NAMES: dict[int, str] = {code: name for name, code in LABELS.items()}

# Non-EEG auxiliary channels present in the .cnt recordings.
#   M1/M2 : left/right mastoid (reference electrodes)
#   VEO/HEO: vertical / horizontal electrooculogram (eye movement)
AUX_CHANNELS: list[str] = ["M1", "M2", "VEO", "HEO"]

N_EEG_CHANNELS: int = 62          # 10-20 system EEG channels used for analysis
SAMPLE_RATE: int = 1000           # Hz, Neuroscan device
N_SESSIONS: int = 3               # sessions per subject (stimuli-material based)
N_TRIALS_PER_SESSION: int = 15    # 3 blocks x 5 emotions
N_SUBJECTS: int = 16              # participants
N_EMOTIONS: int = 5

# ---------------------------------------------------------------------------
# Frequency bands for DE feature extraction (SEED-V / BCMI lab standard)
# ---------------------------------------------------------------------------
FREQ_BANDS: dict[str, tuple[float, float]] = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 14.0),
    "beta": (14.0, 31.0),
    "gamma": (31.0, 50.0),
}
N_FREQ_BANDS: int = len(FREQ_BANDS)  # 5

# ---------------------------------------------------------------------------
# Preprocessing defaults (SEED-V / BCMI lab convention)
# ---------------------------------------------------------------------------
DEFAULT_L_FREQ: float = 1.0       # bandpass lower bound Hz
DEFAULT_H_FREQ: float = 50.0      # bandpass upper bound Hz (covers gamma 31-50)
DEFAULT_NOTCH_FREQ: float = 50.0  # China power-line frequency
DEFAULT_TARGET_SFREQ: float = 200.0  # downsample target (Nyquist=100 covers gamma)
DEFAULT_REFERENCE: str = "car"    # common average reference

# ---------------------------------------------------------------------------
# Special files: repaired .cnt recordings (prioritized over original)
# ---------------------------------------------------------------------------
REPAIRED_FILES: dict[str, str] = {
    "7_1": "7_1_20180411_repaired.cnt",  # subject 7 session 1 has a repaired version
}
