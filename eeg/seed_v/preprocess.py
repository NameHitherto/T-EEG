"""Standard SEED-V EEG preprocessing pipeline.

This module converts raw ``.cnt`` recordings into model-ready trial segments
``(62 channels x T samples)`` by applying, **in this order on the continuous
signal** (so trial boundaries never see filter artifacts):

    1. read + channel-normalize  (reuses :func:`seed_v.cnt.load_raw_normalized`)
    2. re-reference              (CAR by default)
    3. notch filter              (50 Hz power line)
    4. band-pass filter          (1-50 Hz)
    5. downsample                (1000 -> 200 Hz)
    6. segment into 15 trials    (on the processed continuous signal)

No per-sample standardization is applied here: global/batch statistics belong
to the training script (computed on the train split only) to avoid data leakage.

All parameters are bundled in :class:`PreprocessConfig` for reproducibility.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import mne
import numpy as np

from . import config
from .constants import (
    DEFAULT_H_FREQ,
    DEFAULT_L_FREQ,
    DEFAULT_NOTCH_FREQ,
    DEFAULT_REFERENCE,
    DEFAULT_TARGET_SFREQ,
    LABELS,
    N_TRIALS_PER_SESSION,
)
from .cnt import load_raw_normalized
from .dataset import load_stimuli_order, load_trial_timestamps


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PreprocessConfig:
    """All preprocessing parameters. Defaults follow the SEED-V / BCMI convention.

    Attributes
    ----------
    l_freq, h_freq:
        Band-pass cut-offs (Hz).
    notch_freq:
        Power-line notch frequency; ``None`` disables the notch filter.
    target_sfreq:
        Resample target (Hz). Nyquist = target_sfreq/2 must exceed ``h_freq``.
    reference:
        ``'car'`` (common average reference), ``'none'`` (keep as-is), or
        ``'mastoid'`` (re-referenced to the average of M1/M2 — but M1/M2 are
        dropped at load time, so this falls back to ``'none'`` with a warning).
    """

    l_freq: float = DEFAULT_L_FREQ
    h_freq: float = DEFAULT_H_FREQ
    notch_freq: float | None = DEFAULT_NOTCH_FREQ
    target_sfreq: float = DEFAULT_TARGET_SFREQ
    reference: str = DEFAULT_REFERENCE

    def validate(self) -> None:
        """Sanity-check parameters; raise ``ValueError`` if inconsistent."""
        if self.l_freq <= 0 or self.h_freq <= self.l_freq:
            raise ValueError(
                f"Invalid band-pass [{self.l_freq}, {self.h_freq}] Hz: need 0 < l < h."
            )
        if self.target_sfreq <= 0:
            raise ValueError(f"target_sfreq must be > 0, got {self.target_sfreq}.")
        nyquist = self.target_sfreq / 2.0
        if self.h_freq >= nyquist:
            raise ValueError(
                f"h_freq={self.h_freq} Hz must be < Nyquist={nyquist} Hz "
                f"(target_sfreq={self.target_sfreq})."
            )
        if self.reference not in ("car", "none", "mastoid"):
            raise ValueError(f"reference must be 'car'|'none'|'mastoid', got {self.reference!r}.")

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TrialSegment:
    """One preprocessed trial (variable length).

    ``data`` has shape ``(62, T_i)`` float32 — filtered + resampled, unstandardized.
    """

    index: int               # 0-based trial index within the session (0..14)
    label_code: int          # canonical emotion code (Disgust=0 ... Happy=4)
    start_s: int             # trial start, original seconds (timestamp)
    end_s: int               # trial end, original seconds (timestamp)
    data: np.ndarray         # shape (62, T_i), float32


@dataclass(frozen=True)
class PreprocessedRecording:
    """A preprocessed, trial-segmented ``.cnt`` recording."""

    filename: str
    subject: int
    session: int
    sfreq: float             # post-resample sampling frequency
    ch_names: tuple[str, ...]
    trials: tuple[TrialSegment, ...]
    config: PreprocessConfig


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def preprocess_cnt(filename: str, cfg: PreprocessConfig | None = None) -> PreprocessedRecording:
    """Load + preprocess a single ``.cnt`` recording and segment it into trials.

    See module docstring for the processing order. The ``filename`` may be a
    bare name (resolved under ``EEG_RAW_DIR``) or an absolute path.
    """
    cfg = cfg or PreprocessConfig()
    cfg.validate()

    # 1. Read + channel-normalize (no filtering yet).
    raw, subject, session, ch_names = load_raw_normalized(filename)

    # 2. Re-reference.
    if cfg.reference == "car":
        raw.set_eeg_reference("average", projection=False, verbose="WARNING")
    elif cfg.reference == "mastoid":
        # M1/M2 were dropped at load time; CAR is the safe fallback.
        print(
            f"[seed_v.preprocess] WARNING: reference='mastoid' requested but M1/M2 "
            f"are dropped at load; falling back to no re-referencing."
        )

    # 3. Notch filter (power line).
    if cfg.notch_freq is not None:
        raw.notch_filter(
            freqs=cfg.notch_freq,
            method="fir",
            fir_design="firwin",
            verbose="WARNING",
        )

    # 4. Band-pass filter (zero-phase FIR).
    raw.filter(
        cfg.l_freq,
        cfg.h_freq,
        method="fir",
        fir_design="firwin",
        verbose="WARNING",
    )

    # 5. Downsample (mne applies anti-aliasing internally).
    raw.resample(cfg.target_sfreq, verbose="WARNING")
    sfreq = float(raw.info["sfreq"])

    # 6. Segment into 15 trials on the processed continuous signal.
    timestamps = load_trial_timestamps()[session]
    stimuli = load_stimuli_order()[session]
    if len(timestamps) != N_TRIALS_PER_SESSION or len(stimuli) != N_TRIALS_PER_SESSION:
        raise ValueError(
            f"session {session}: expected {N_TRIALS_PER_SESSION} trials, got "
            f"{len(timestamps)} timestamps / {len(stimuli)} stimuli."
        )

    data = raw.get_data()
    trials: list[TrialSegment] = []
    for i, (start_s, end_s) in enumerate(timestamps):
        # Time is in seconds; convert to samples at the post-resample rate.
        i0 = int(round(start_s * sfreq))
        i1 = int(round(end_s * sfreq))
        segment = np.ascontiguousarray(data[:, i0:i1], dtype=np.float32)
        trials.append(
            TrialSegment(
                index=i,
                label_code=LABELS[stimuli[i]],
                start_s=int(start_s),
                end_s=int(end_s),
                data=segment,
            )
        )

    return PreprocessedRecording(
        filename=filename if isinstance(filename, str) else str(filename),
        subject=subject,
        session=session,
        sfreq=sfreq,
        ch_names=ch_names,
        trials=tuple(trials),
        config=cfg,
    )


__all__ = [
    "PreprocessConfig",
    "TrialSegment",
    "PreprocessedRecording",
    "preprocess_cnt",
]
