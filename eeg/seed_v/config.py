"""Runtime configuration for the SEED-V package.

Loads environment variables from the repository-root ``.env`` and exposes the
local dataset paths and the pointers to each SEED-V metadata file.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Repository root = parent of this package's directory (``eeg/``).
REPO_ROOT = Path(__file__).resolve().parents[1]

# Load .env silently; missing values fall back to the explicit checks below.
load_dotenv(REPO_ROOT / ".env")


def _get_env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if not value:
        raise RuntimeError(
            f"Environment variable {name!r} is not set. "
            f"Please define it in {REPO_ROOT / '.env'}."
        )
    return value


# --- Top-level paths ---------------------------------------------------------
RAW_DIR = Path(_get_env("SEED_V_RAW"))
PROCESSED_DIR = Path(_get_env("SEED_V_PROCESSED"))
API_PORT = int(os.environ.get("API_PORT", "13400"))

# --- SEED-V metadata files (inside RAW_DIR) ---------------------------------
CHANNELS_LOCS = RAW_DIR / "channel_62_pos.locs"
CHANNEL_ORDER_XLSX = RAW_DIR / "Channel Order.xlsx"
LABEL_ORDER_XLSX = RAW_DIR / "emotion_label_and_stimuli_order.xlsx"
TRIAL_TS_TXT = RAW_DIR / "trial_start_end_timestamp.txt"
SCORES_XLSX = RAW_DIR / "Scores.xlsx"
STIMULATION_XLSX = RAW_DIR / "SEED-V_stimulation.xlsx"
PARTICIPANTS_XLSX = RAW_DIR / "Participants_info.xlsx"
README_TXT = RAW_DIR / "Read me.txt"

# Sub-directories of the raw dataset.
EEG_RAW_DIR = RAW_DIR / "EEG_raw"
EEG_DE_FEATURES_DIR = RAW_DIR / "EEG_DE_features"
EYE_MOVEMENT_FEATURES_DIR = RAW_DIR / "Eye_movement_features"
EYE_RAW_DIR = RAW_DIR / "Eye_raw"
