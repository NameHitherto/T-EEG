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
