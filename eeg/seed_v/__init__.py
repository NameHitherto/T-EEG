"""SEED-V dataset core package.

Provides parsing and inspection of the SEED-V EEG emotion-recognition dataset's
metadata (channels, labels, stimuli order, trial timestamps, scores) and loading
of raw ``.cnt`` signal recordings.

Run ``python -m seed-v`` from the repository root to print a summary.
"""

from .cnt import CntRecording, Trial, load_cnt_recording

__version__ = "0.1.0"

__all__ = [
    "CntRecording",
    "Trial",
    "load_cnt_recording",
    "__version__",
]
