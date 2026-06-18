"""FastAPI app exposing SEED-V dataset metadata as HTTP endpoints.

Run with::

    uvicorn api.main:app --reload --port 13400

The dataset metadata is static, so it is parsed once at startup (via a lifespan
handler) and cached in module state — request handlers never touch disk. The
``/api/seed-v/info`` payload is the structured equivalent of
``python -m seed_v`` (see :mod:`seed_v.inspect`).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from seed_v import config
from seed_v import constants as C
from seed_v.dataset import (
    load_channels,
    load_labels,
    load_participants,
    load_scores,
    load_stimuli_order,
    load_trial_timestamps,
)

# Parsed metadata, populated once at startup by ``lifespan``.
_info: dict[str, Any] = {}


def _build_dataset_info() -> dict[str, Any]:
    """Parse all SEED-V metadata files and return the structured info dict.

    Mirrors the sections printed by :func:`seed_v.inspect.print_dataset_info` so
    the JSON output is the machine-readable counterpart of that summary.
    """
    # --- Dataset-level constants -----------------------------------------
    dataset = {
        "n_subjects": C.N_SUBJECTS,
        "n_sessions": C.N_SESSIONS,
        "n_trials_per_session": C.N_TRIALS_PER_SESSION,
        "n_eeg_channels": C.N_EEG_CHANNELS,
        "aux_channels": C.AUX_CHANNELS,
        "sample_rate": C.SAMPLE_RATE,
        "n_emotions": C.N_EMOTIONS,
    }

    paths = {
        "raw_dir": str(config.RAW_DIR),
        "processed_dir": str(config.PROCESSED_DIR),
    }

    # --- Channels --------------------------------------------------------
    channels = [
        {"name": ch.name, "x": ch.x, "y": ch.y} for ch in load_channels()
    ]

    # --- Labels ----------------------------------------------------------
    labels = load_labels()
    label_names = {code: name for name, code in labels.items()}

    # --- Stimuli order per session --------------------------------------
    stimuli_order = {
        str(session): emotions
        for session, emotions in load_stimuli_order().items()
    }

    # --- Trial timestamps ------------------------------------------------
    trial_timestamps: dict[str, list[dict[str, int]]] = {}
    for session, trials in load_trial_timestamps().items():
        rows = []
        for i, (start, end) in enumerate(trials, start=1):
            duration = end - start
            rows.append(
                {
                    "trial": i,
                    "start_s": start,
                    "end_s": end,
                    "duration_s": duration,
                    "samples": duration * C.SAMPLE_RATE,
                }
            )
        trial_timestamps[str(session)] = rows

    # --- Scores summary --------------------------------------------------
    scores_df = load_scores()
    trial_cols = [f"trial_{i + 1}" for i in range(C.N_TRIALS_PER_SESSION)]
    per_row_mean = scores_df[trial_cols].mean(axis=1)
    scores = {
        "n_subjects": int(scores_df["subject"].nunique()),
        "n_sessions": int(scores_df["session"].nunique()),
        "n_rows": int(len(scores_df)),
        "trial_mean": float(per_row_mean.mean()),
        "trial_min": float(scores_df[trial_cols].min().min()),
        "trial_max": float(scores_df[trial_cols].max().max()),
    }

    # --- Participants (non-critical) ------------------------------------
    participants: dict[str, Any]
    try:
        pdf = load_participants()
        participants = {
            "n": int(len(pdf)),
            "sex_counts": {str(k): int(v) for k, v in pdf["sex"].value_counts().items()},
            "age_min": int(pdf["age"].min()),
            "age_max": int(pdf["age"].max()),
        }
    except Exception as exc:  # noqa: BLE001 - non-critical, matches inspect.py
        participants = {"error": f"participants info unavailable: {exc}"}

    return {
        "dataset": dataset,
        "paths": paths,
        "channels": channels,
        "labels": labels,
        "label_names": {str(k): v for k, v in label_names.items()},
        "stimuli_order": stimuli_order,
        "trial_timestamps": trial_timestamps,
        "scores": scores,
        "participants": participants,
    }


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Parse the static dataset metadata once and cache it for all requests.
    _info.update(_build_dataset_info())
    yield
    _info.clear()


app = FastAPI(title="T-EEG API", lifespan=lifespan)


@app.get("/api/seed-v/info")
def get_seed_v_info() -> dict[str, Any]:
    """Return the full SEED-V dataset metadata as structured JSON."""
    return _info
