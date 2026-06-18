"""Structured loaders for SEED-V metadata.

Each loader reads a real file shipped with the dataset and returns typed,
validated data. Parsers cross-check their results against :mod:`seed_v.constants`
so that a corrupted / renamed file fails loudly instead of silently producing
wrong experiment metadata.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass

import pandas as pd

from . import config
from .constants import (
    AUX_CHANNELS,
    LABELS,
    N_EEG_CHANNELS,
    N_SESSIONS,
    N_TRIALS_PER_SESSION,
)


# ---------------------------------------------------------------------------
# 1. Channels
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ChannelInfo:
    """A single EEG electrode position in the 10-20 system."""

    name: str
    x: float
    y: float


def load_channels() -> list[ChannelInfo]:
    """Return the 62 EEG channels with their 2-D scalp coordinates.

    Parses ``channel_62_pos.locs`` (columns: index, x, y, name) and validates
    the channel count and ordering against ``Channel Order.xlsx``.
    """
    channels: list[ChannelInfo] = []
    with open(config.CHANNELS_LOCS, encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) < 4:
                continue
            name = parts[-1]
            x = float(parts[-3])
            y = float(parts[-2])
            channels.append(ChannelInfo(name=name, x=x, y=y))

    if len(channels) != N_EEG_CHANNELS:
        raise ValueError(
            f"Expected {N_EEG_CHANNELS} EEG channels in "
            f"{config.CHANNELS_LOCS}, found {len(channels)}."
        )

    # Cross-check ordering against Channel Order.xlsx (case-insensitive).
    order = pd.read_excel(config.CHANNEL_ORDER_XLSX, sheet_name="Sheet1", header=None)
    order_names = [str(n).strip() for n in order[0].dropna().tolist()]
    if len(order_names) != N_EEG_CHANNELS:
        raise ValueError(
            f"Expected {N_EEG_CHANNELS} names in Channel Order.xlsx, "
            f"found {len(order_names)}."
        )
    parsed_lower = [c.name.lower() for c in channels]
    order_lower = [n.lower() for n in order_names]
    if parsed_lower != order_lower:
        raise ValueError(
            "Channel ordering in channel_62_pos.locs does not match "
            "Channel Order.xlsx."
        )

    return channels


# ---------------------------------------------------------------------------
# 2. Labels
# ---------------------------------------------------------------------------
def load_labels() -> dict[str, int]:
    """Parse the emotion label table and validate against the canonical spec."""
    df = pd.read_excel(config.LABEL_ORDER_XLSX, header=None)
    label_col = df[1]
    code_col = df[2]

    parsed: dict[str, int] = {}
    for name, code in zip(label_col, code_col):
        # The stimuli-order block below also fills these columns with strings,
        # so only accept rows whose code is a genuine number.
        if not isinstance(name, str) or not name.strip():
            continue
        if isinstance(code, bool) or not pd.api.types.is_number(code):
            continue
        parsed[name.strip()] = int(code)

    if parsed != LABELS:
        raise ValueError(
            f"Parsed labels {parsed} do not match canonical spec {LABELS}."
        )
    return parsed


# ---------------------------------------------------------------------------
# 3. Stimuli order per session
# ---------------------------------------------------------------------------
def load_stimuli_order() -> dict[int, list[str]]:
    """Return ``{session_number: [15 emotion names in presentation order]}``."""
    df = pd.read_excel(config.LABEL_ORDER_XLSX, header=None)
    order: dict[int, list[str]] = {}

    for _, row in df.iterrows():
        session_cell = row[1]
        if not isinstance(session_cell, str) or "Session" not in session_cell:
            continue
        match = re.search(r"Session\s*(\d+)", session_cell)
        if not match:
            continue
        session_no = int(match.group(1))
        emotions = [str(v).strip() for v in row.iloc[2:2 + N_TRIALS_PER_SESSION]]
        emotions = [e for e in emotions if e and e.lower() != "nan"]
        if len(emotions) != N_TRIALS_PER_SESSION:
            raise ValueError(
                f"Session {session_no}: expected {N_TRIALS_PER_SESSION} "
                f"stimuli, found {len(emotions)} ({emotions})."
            )
        # Validate every entry is a known label.
        unknown = [e for e in emotions if e not in LABELS]
        if unknown:
            raise ValueError(
                f"Session {session_no}: unknown emotion(s) {unknown}."
            )
        order[session_no] = emotions

    if len(order) != N_SESSIONS:
        raise ValueError(
            f"Expected {N_SESSIONS} sessions, found {len(order)} ({sorted(order)})."
        )
    return dict(sorted(order.items()))


# ---------------------------------------------------------------------------
# 4. Trial start/end timestamps
# ---------------------------------------------------------------------------
def load_trial_timestamps() -> dict[int, list[tuple[int, int]]]:
    """Return ``{session_number: [(start_s, end_s), ...]}`` (15 trials each).

    Timestamps are in seconds at :data:`seed_v.constants.SAMPLE_RATE` Hz.
    """
    text = config.TRIAL_TS_TXT.read_text(encoding="utf-8")

    timestamps: dict[int, list[tuple[int, int]]] = {}
    current_session: int | None = None
    starts: list[int] | None = None
    ends: list[int] | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        session_match = re.match(r"Session\s*(\d+)\s*:", stripped)
        if session_match:
            # Flush previous session.
            if current_session is not None and starts is not None and ends is not None:
                timestamps[current_session] = _pair_trials(current_session, starts, ends)
            current_session = int(session_match.group(1))
            starts = None
            ends = None
            continue
        if stripped.lower().startswith("start_second"):
            starts = list(ast.literal_eval(stripped.split(":", 1)[1].strip()))
        elif stripped.lower().startswith("end_second"):
            ends = list(ast.literal_eval(stripped.split(":", 1)[1].strip()))

    # Flush the last session.
    if current_session is not None and starts is not None and ends is not None:
        timestamps[current_session] = _pair_trials(current_session, starts, ends)

    if len(timestamps) != N_SESSIONS:
        raise ValueError(
            f"Expected {N_SESSIONS} sessions of trial timestamps, "
            f"found {len(timestamps)}."
        )
    return dict(sorted(timestamps.items()))


def _pair_trials(session: int, starts: list[int], ends: list[int]) -> list[tuple[int, int]]:
    if len(starts) != N_TRIALS_PER_SESSION or len(ends) != N_TRIALS_PER_SESSION:
        raise ValueError(
            f"Session {session}: expected {N_TRIALS_PER_SESSION} start/end "
            f"values, got {len(starts)}/{len(ends)}."
        )
    return [(int(s), int(e)) for s, e in zip(starts, ends)]


# ---------------------------------------------------------------------------
# 5. Scores
# ---------------------------------------------------------------------------
_TRIAL_COLS = [f"trial_{i + 1}" for i in range(N_TRIALS_PER_SESSION)]


def load_scores() -> pd.DataFrame:
    """Return participant feedback scores as a tidy DataFrame.

    Columns: ``subject`` (forward-filled), ``session``, then ``trial_1..trial_15``.

    The raw ``Scores.xlsx`` stores 16 subjects x 3 sessions = 48 rows. The first
    subject column is only set on the first row of each subject and is forward-
    filled here. Trial scores are the 15 per-clip ratings (the leading
    ``Score`` column in the source file is kept apart as ``reported_score``
    since the dataset does not document it unambiguously).
    """
    raw = pd.read_excel(config.SCORES_XLSX, header=0)
    raw.columns = [str(c).strip() for c in raw.columns]

    subject = raw.iloc[:, 0].ffill().astype(int)
    session = raw.iloc[:, 1].astype(int)
    # Columns 2..16 are the 15 per-clip feedback scores (the source file's
    # generic "Score" header labels that block rather than a single value).
    trial_scores = raw.iloc[:, 2:2 + N_TRIALS_PER_SESSION]
    if trial_scores.shape[1] != N_TRIALS_PER_SESSION:
        raise ValueError(
            f"Expected {N_TRIALS_PER_SESSION} trial score columns, "
            f"found {trial_scores.shape[1]}."
        )

    df = pd.concat([subject, session], axis=1)
    df.columns = ["subject", "session"]
    trial_scores.columns = _TRIAL_COLS
    df = pd.concat([df, trial_scores], axis=1)
    return df


# ---------------------------------------------------------------------------
# Bonus: participants info (kept light, used by the inspection summary).
# ---------------------------------------------------------------------------
def load_participants() -> pd.DataFrame:
    """Return subject sex and age from ``Participants_info.xlsx``."""
    df = pd.read_excel(config.PARTICIPANTS_XLSX, header=0)
    df.columns = [str(c).strip().lower() for c in df.columns]
    rename = {"name": "subject", "sex": "sex", "age": "age"}
    df = df.rename(columns=rename)
    if "subject" in df.columns:
        df["subject"] = df["subject"].astype(int)
    return df


__all__ = [
    "AUX_CHANNELS",
    "ChannelInfo",
    "load_channels",
    "load_labels",
    "load_stimuli_order",
    "load_trial_timestamps",
    "load_scores",
    "load_participants",
]
