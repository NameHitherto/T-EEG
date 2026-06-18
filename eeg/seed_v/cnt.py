"""Signal-level loader for SEED-V ``.cnt`` recordings.

While :mod:`seed_v.dataset` parses the dataset's *metadata* (channels, labels,
trial timestamps, scores), this module loads the actual EEG signal of a single
``.cnt`` recording, normalizes it to the canonical 62-channel order, and
segments the continuous signal into the 15 per-session trials — exactly the
pipeline documented in the official SEED-V notebook
``EEG_raw/Load_cnt_file_with_mne.ipynb``.

No filtering is applied: the notebook explicitly leaves that to downstream
code, and so does this loader.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import mne
import numpy as np

from . import config
from .constants import (
    AUX_CHANNELS,
    LABELS,
    N_EEG_CHANNELS,
    N_TRIALS_PER_SESSION,
    SAMPLE_RATE,
)
from .dataset import load_channels, load_stimuli_order, load_trial_timestamps


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Trial:
    """One segmented trial of a recording.

    ``data`` has shape ``(n_channels, n_samples)`` and is **not** filtered or
    resampled — its length is ``(end_s - start_s) * sfreq`` samples.
    """

    index: int                # 0-based trial index within the session (0..14)
    label: str                # emotion name from the session's stimuli order
    label_code: int           # canonical integer code (Disgust=0 … Happy=4)
    start_s: int              # trial start, seconds
    end_s: int                # trial end, seconds
    data: np.ndarray          # shape (62, T_i), float32, unfiltered


@dataclass(frozen=True)
class CntRecording:
    """A parsed, channel-normalized, trial-segmented ``.cnt`` recording."""

    filename: str             # e.g. "6_3_20180802.cnt"
    subject: int              # 1..16
    session: int              # 1..3 (stimuli-material order)
    sfreq: float              # sampling frequency, Hz
    ch_names: tuple[str, ...]  # 62 names in canonical order
    trials: tuple[Trial, ...]  # 15 trials


# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------
def parse_cnt_filename(filename: str) -> tuple[int, int]:
    """Return ``(subject, session)`` parsed from a ``.cnt`` filename.

    SEED-V ``.cnt`` files are named ``{subject}_{session}_{date}[_repaired].cnt``
    where the middle number is the stimuli-material session (1/2/3), which
    selects the matching trial-timestamp set. The date and any ``_repaired``
    suffix are ignored for indexing.
    """
    stem = Path(filename).stem
    parts = stem.split("_")
    if len(parts) < 3:
        raise ValueError(
            f"Unexpected .cnt filename {filename!r}: expected "
            f"'{{subject}}_{{session}}_{{date}}.cnt'."
        )
    try:
        subject = int(parts[0])
        session = int(parts[1])
    except ValueError as exc:
        raise ValueError(
            f"Could not parse subject/session from {filename!r}: {exc}."
        ) from exc
    return subject, session


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def load_cnt_recording(filename: str) -> CntRecording:
    """Load a SEED-V ``.cnt`` file and return a structured, trial-segmented recording.

    The ``filename`` may be a bare name (resolved under ``EEG_RAW_DIR``) or an
    absolute path. The pipeline mirrors the official notebook: read with mne,
    drop the 4 auxiliary channels (M1/M2/VEO/HEO), normalize to the canonical
    62-channel order, and slice the continuous signal into the 15 trials defined
    by ``trial_start_end_timestamp.txt`` for the recording's session. No
    filtering is applied.
    """
    # 1. Resolve path.
    path = Path(filename)
    if not path.is_absolute() and not path.parent.parts:
        path = config.EEG_RAW_DIR / path
    if not path.exists():
        raise FileNotFoundError(f".cnt file not found: {path}")

    # 2. Parse subject / session.
    subject, session = parse_cnt_filename(path.name)

    # 3. Read with mne (preload so get_data() needs no further I/O).
    raw = mne.io.read_raw_cnt(str(path), preload=True, verbose="WARNING")

    # 4. Drop auxiliary channels (mastoid refs + EOG).
    present_aux = [ch for ch in AUX_CHANNELS if ch in raw.ch_names]
    if present_aux:
        raw.drop_channels(present_aux)

    # 5. Channel normalization to the canonical 62-name order.
    canonical = [ch.name for ch in load_channels()]
    if len(raw.ch_names) != N_EEG_CHANNELS:
        raise ValueError(
            f"{path.name}: expected {N_EEG_CHANNELS} EEG channels after "
            f"dropping aux, found {len(raw.ch_names)}."
        )
    raw_lower = [n.lower() for n in raw.ch_names]
    canon_lower = [n.lower() for n in canonical]
    if set(raw_lower) != set(canon_lower):
        missing = sorted(set(canon_lower) - set(raw_lower))
        extra = sorted(set(raw_lower) - set(canon_lower))
        raise ValueError(
            f"{path.name}: channel set does not match the canonical 62. "
            f"missing={missing}, unexpected={extra}."
        )
    # Reorder to canonical order if the order differs (case-insensitive).
    if raw_lower != canon_lower:
        name_to_canonical = dict(zip(canon_lower, canonical))
        raw.reorder([name_to_canonical[n] for n in raw_lower])

    ch_names = tuple(canonical)

    # 6. Sanity-check sampling rate (mne's value is authoritative for slicing).
    sfreq = float(raw.info["sfreq"])
    if abs(sfreq - SAMPLE_RATE) > 1e-3:
        print(
            f"[seed_v.cnt] WARNING: {path.name} sfreq={sfreq} Hz differs from "
            f"canonical {SAMPLE_RATE} Hz; using mne's value for slicing."
        )

    # 7. Slice into the 15 trials defined for this session.
    timestamps = load_trial_timestamps()[session]
    stimuli = load_stimuli_order()[session]
    if len(timestamps) != N_TRIALS_PER_SESSION or len(stimuli) != N_TRIALS_PER_SESSION:
        raise ValueError(
            f"{path.name}: session {session} has {len(timestamps)} timestamps "
            f"and {len(stimuli)} stimuli; expected {N_TRIALS_PER_SESSION}."
        )

    data = raw.get_data()
    trials: list[Trial] = []
    for i, (start_s, end_s) in enumerate(timestamps):
        label = stimuli[i]
        segment = data[:, int(round(start_s * sfreq)): int(round(end_s * sfreq))]
        trials.append(
            Trial(
                index=i,
                label=label,
                label_code=LABELS[label],
                start_s=int(start_s),
                end_s=int(end_s),
                data=np.ascontiguousarray(segment, dtype=np.float32),
            )
        )

    # 8. Assemble.
    return CntRecording(
        filename=path.name,
        subject=subject,
        session=session,
        sfreq=sfreq,
        ch_names=ch_names,
        trials=tuple(trials),
    )


__all__ = [
    "CntRecording",
    "Trial",
    "load_cnt_recording",
    "parse_cnt_filename",
]
