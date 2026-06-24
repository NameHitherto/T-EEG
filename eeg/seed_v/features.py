"""Differential Entropy (DE) feature extraction for SEED-V.

Computes per-channel, per-frequency-band DE features from preprocessed trial
segments using a sliding-window approach. The five canonical bands are:

    delta (1-4 Hz), theta (4-8 Hz), alpha (8-14 Hz), beta (14-31 Hz), gamma (31-50 Hz)

DE for a zero-mean Gaussian signal with variance σ² is:

    DE = 0.5 * ln(2πeσ²)

This is the standard definition used in the SEED / SEED-V / BCMI-lab papers.
The constant term (0.5·ln(2πe)) is preserved so that our values can be directly
compared with the official ``EEG_DE_features/*.npz`` files for validation.

Official DE features are stored as ``(n_windows, 310)`` where 310 = 62 channels
× 5 bands (channels vary fastest, i.e. ``[ch0_delta, ch0_theta, ..., ch0_gamma,
ch1_delta, ...]``).  This module provides both the per-trial ``(T_seg, 62, 5)``
3-D format and a flattened ``(T_seg, 310)`` format matching the official layout.
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import config
from .constants import FREQ_BANDS, LABELS, N_EEG_CHANNELS, N_FREQ_BANDS, SAMPLE_RATE
from .preprocess import PreprocessedRecording, TrialSegment


# ---------------------------------------------------------------------------
# DE computation
# ---------------------------------------------------------------------------
def _band_de(signal: np.ndarray) -> float:
    """DE = 0.5 * ln(2πe * var) for a 1-D signal segment.

    ``signal`` is a 1-D float array (one channel in one band, one window).
    """
    var = np.var(signal, ddof=0)  # population variance (matches official)
    # Guard against log(0) — extremely rare but possible for zeroed-out segments.
    if var < 1e-12:
        var = 1e-12
    return 0.5 * np.log(2.0 * np.pi * np.e * var)


# ---------------------------------------------------------------------------
# Trial-level extraction
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DeConfig:
    """Parameters for DE extraction.

    Attributes
    ----------
    window_s:
        Window length in seconds. Default 4.0 matches the official SEED-V DE
        features (e.g. 72 s trial -> 18 windows).
    step_s:
        Step between successive windows in seconds; ``None`` means no overlap.
    band_l_freq, band_h_freq:
        Band-pass limits applied *per band* before DE computation.
        These should match or be contained within the preprocessing band-pass.
    """

    window_s: float = 4.0
    step_s: float | None = None  # None => no overlap
    band_l_freq: float = 1.0
    band_h_freq: float = 50.0

    @property
    def effective_step_s(self) -> float:
        return self.step_s if self.step_s is not None else self.window_s


def extract_de(
    trial_data: np.ndarray,
    sfreq: float,
    de_cfg: DeConfig | None = None,
) -> np.ndarray:
    """Extract DE features from one trial.

    Parameters
    ----------
    trial_data:
        Shape ``(62, T)`` — one preprocessed trial (already band-pass filtered).
    sfreq:
        Sampling frequency of the trial (post-resample).
    de_cfg:
        Extraction parameters.

    Returns
    -------
    de_3d:
        Shape ``(n_windows, 62, 5)`` float32.
        Axis 2 order: delta, theta, alpha, beta, gamma.
    """
    de_cfg = de_cfg or DeConfig()
    n_channels, n_samples = trial_data.shape
    if n_channels != N_EEG_CHANNELS:
        raise ValueError(f"Expected {N_EEG_CHANNELS} channels, got {n_channels}.")

    window_n = int(round(de_cfg.window_s * sfreq))
    step_n = int(round(de_cfg.effective_step_s * sfreq))
    if window_n <= 0 or step_n <= 0:
        raise ValueError("Window/step too small for the given sfreq.")

    # Collect band-pass filtered signals per band.
    # trial_data is already preprocessed (1-50 Hz), so we only need to
    # narrow-band filter within that range for each frequency band.
    band_signals: list[np.ndarray] = []
    band_names = list(FREQ_BANDS.keys())
    for band_name in band_names:
        l, h = FREQ_BANDS[band_name]
        # Clip to the available range after preprocessing.
        l = max(l, de_cfg.band_l_freq)
        h = min(h, de_cfg.band_h_freq)
        if l >= h:
            # Band is entirely outside the preprocessed range — fill with zeros.
            band_signals.append(np.zeros_like(trial_data))
            continue
        # Use scipy.signal to band-pass filter each channel (MNE-free for array data).
        # We use mne.filter.filter_data for consistency with the preprocessing pipeline.
        from mne.filter import filter_data

        filtered = filter_data(
            trial_data.astype(np.float64),
            sfreq=sfreq,
            l_freq=l,
            h_freq=h,
            method="fir",
            fir_design="firwin",
            verbose="WARNING",
        )
        band_signals.append(filtered.astype(np.float64))

    # Sliding window DE extraction.
    windows: list[np.ndarray] = []
    for start in range(0, n_samples - window_n + 1, step_n):
        end = start + window_n
        # de_matrix: (62, 5)
        de_matrix = np.empty((n_channels, N_FREQ_BANDS), dtype=np.float32)
        for ch in range(n_channels):
            for b, band_sig in enumerate(band_signals):
                de_matrix[ch, b] = _band_de(band_sig[ch, start:end])
        windows.append(de_matrix)

    if not windows:
        # Trial shorter than one window — produce a single window from the full trial.
        de_matrix = np.empty((n_channels, N_FREQ_BANDS), dtype=np.float32)
        for ch in range(n_channels):
            for b, band_sig in enumerate(band_signals):
                de_matrix[ch, b] = _band_de(band_sig[ch, :])
        windows.append(de_matrix)

    return np.stack(windows, axis=0)  # (n_windows, 62, 5)


def extract_de_flat(
    trial_data: np.ndarray,
    sfreq: float,
    de_cfg: DeConfig | None = None,
) -> np.ndarray:
    """Extract DE features in the official flat layout ``(n_windows, 310)``.

    Column order: ch0_delta, ch0_theta, ch0_alpha, ch0_beta, ch0_gamma,
                  ch1_delta, ... — matching the official ``EEG_DE_features/*.npz``.
    """
    de_3d = extract_de(trial_data, sfreq, de_cfg)  # (W, 62, 5)
    # Reshape: (W, 62, 5) -> (W, 62*5) where channel varies fastest within
    # each 5-band group — this matches the official layout.
    return de_3d.reshape(de_3d.shape[0], -1)


# ---------------------------------------------------------------------------
# Official DE comparison (validation)
# ---------------------------------------------------------------------------
def compare_with_official(
    recording: PreprocessedRecording,
    de_cfg: DeConfig | None = None,
) -> dict:
    """Compare self-extracted DE features against the official SEED-V DE features.

    Loads the official ``{subject}_123.npz``, maps each trial, and computes
    per-trial Pearson correlation and mean absolute error between the two.

    Returns
    -------
    summary:
        Dict with per-trial stats and an overall summary suitable for
        inclusion in ``manifest.json``.
    """
    de_cfg = de_cfg or DeConfig()
    official_path = config.EEG_DE_FEATURES_DIR / f"{recording.subject}_123.npz"
    if not official_path.exists():
        return {"error": f"Official DE file not found: {official_path}"}

    # Load official DE.
    npz = np.load(official_path, allow_pickle=True)
    off_data = pickle.loads(npz["data"])
    off_label = pickle.loads(npz["label"])

    # Official key index: 0..14 = session 1, 15..29 = session 2, 30..44 = session 3.
    session_offset = (recording.session - 1) * N_FREQ_BANDS  # 0, 15, 30
    # Note: N_FREQ_BANDS=5, but the offset is 15 per session (N_TRIALS_PER_SESSION).
    session_offset = (recording.session - 1) * 15

    per_trial: list[dict] = []
    for i, trial in enumerate(recording.trials):
        off_key = session_offset + i
        if off_key not in off_data:
            per_trial.append({"trial": i, "error": f"official key {off_key} not found"})
            continue

        off_de = off_data[off_key]  # shape (n_windows_official, 310)
        our_de = extract_de_flat(trial.data, recording.sfreq, de_cfg)

        # Align window counts — official may differ slightly in window params.
        n_compare = min(off_de.shape[0], our_de.shape[0])
        if n_compare == 0:
            per_trial.append({"trial": i, "error": "no overlapping windows"})
            continue

        off_flat = off_de[:n_compare].ravel()
        our_flat = our_de[:n_compare].ravel()

        # Pearson correlation.
        if np.std(off_flat) < 1e-12 or np.std(our_flat) < 1e-12:
            corr = 0.0
        else:
            corr = float(np.corrcoef(off_flat, our_flat)[0, 1])
        mae = float(np.mean(np.abs(off_flat - our_flat)))

        per_trial.append({
            "trial": i,
            "n_windows_official": off_de.shape[0],
            "n_windows_ours": our_de.shape[0],
            "n_compared": n_compare,
            "pearson_r": round(corr, 4),
            "mae": round(mae, 4),
        })

    corrs = [t["pearson_r"] for t in per_trial if "pearson_r" in t]
    return {
        "subject": recording.subject,
        "session": recording.session,
        "de_config": {"window_s": de_cfg.window_s, "step_s": de_cfg.effective_step_s},
        "per_trial": per_trial,
        "mean_pearson_r": round(float(np.mean(corrs)), 4) if corrs else None,
    }


__all__ = [
    "DeConfig",
    "extract_de",
    "extract_de_flat",
    "compare_with_official",
]
