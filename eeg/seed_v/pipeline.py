"""End-to-end batch preprocessing pipeline for SEED-V.

Processes every subject × session recording into two formats under
``SEED_V_PROCESSED``:

    raw_signal/sub{XX}_ses{Y}.npz   — preprocessed trial waveforms (62 x T_i)
    de_features/sub{XX}_ses{Y}.npz  — DE feature matrices per trial

Plus a ``manifest.json`` (config snapshot + per-file stats + official-DE
comparison) and an ``index.csv`` manifest of all outputs.

Reproducibility: the full :class:`PreprocessConfig` and :class:`DeConfig` are
written to ``manifest.json``; re-running with the same config reproduces the
output byte-for-byte (float32 arrays).
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import config
from .constants import N_SESSIONS, N_SUBJECTS, N_TRIALS_PER_SESSION, REPAIRED_FILES
from .features import DeConfig, extract_de
from .preprocess import PreprocessConfig, preprocess_cnt


# ---------------------------------------------------------------------------
# File naming & discovery
# ---------------------------------------------------------------------------
def _npz_name(subject: int, session: int) -> str:
    return f"sub{subject:02d}_ses{session}.npz"


def find_cnt_files(subjects: list[int] | None = None,
                   sessions: list[int] | None = None) -> list[str]:
    """Return the list of ``.cnt`` basenames to process.

    For recordings that have a ``_repaired`` version, the repaired file is used.
    """
    subjects = subjects or list(range(1, N_SUBJECTS + 1))
    sessions = sessions or list(range(1, N_SESSIONS + 1))

    files: list[str] = []
    # Index all existing .cnt files for quick lookup.
    all_cnts = {p.name: p for p in config.EEG_RAW_DIR.glob("*.cnt")}

    for subj in subjects:
        for ses in sessions:
            # Prefer the repaired version if present.
            repaired_key = f"{subj}_{ses}"
            if repaired_key in REPAIRED_FILES and REPAIRED_FILES[repaired_key] in all_cnts:
                files.append(REPAIRED_FILES[repaired_key])
                continue
            # Find the matching non-repaired file: {subj}_{ses}_*.cnt
            prefix = f"{subj}_{ses}_"
            candidates = [
                name for name in all_cnts
                if name.startswith(prefix) and not name.endswith("_repaired.cnt")
            ]
            if not candidates:
                raise FileNotFoundError(
                    f"No .cnt file found for subject {subj} session {ses} "
                    f"with prefix {prefix!r} in {config.EEG_RAW_DIR}."
                )
            if len(candidates) > 1:
                raise RuntimeError(
                    f"Ambiguous .cnt files for subject {subj} session {ses}: {candidates}."
                )
            files.append(candidates[0])
    return files


# ---------------------------------------------------------------------------
# Single-recording serialization
# ---------------------------------------------------------------------------
def save_raw_signal(rec, out_dir: Path) -> Path:
    """Save preprocessed trial waveforms (variable length) to ``.npz``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / _npz_name(rec.subject, rec.session)

    # Variable-length trials stored as an object array of (62, T_i) float32.
    trial_arrays = [trial.data for trial in rec.trials]
    data_obj = np.empty(len(trial_arrays), dtype=object)
    for j, arr in enumerate(trial_arrays):
        data_obj[j] = arr

    labels = np.array([trial.label_code for trial in rec.trials], dtype=np.int8)
    durations = np.array(
        [trial.end_s - trial.start_s for trial in rec.trials],
        dtype=np.float32,
    )

    np.savez(
        out_path,
        data=data_obj,
        labels=labels,
        sfreq=np.float32(rec.sfreq),
        ch_names=np.array(rec.ch_names, dtype="<U8"),
        trial_durations_s=durations,
        subject=np.int16(rec.subject),
        session=np.int16(rec.session),
        filename=np.array(rec.filename, dtype="<U64"),
    )
    return out_path


def save_de_features(rec, out_dir: Path, de_cfg: DeConfig) -> Path:
    """Save DE feature matrices per trial to ``.npz``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / _npz_name(rec.subject, rec.session)

    trial_de: list[np.ndarray] = []
    for trial in rec.trials:
        de = extract_de(trial.data, rec.sfreq, de_cfg)  # (W, 62, 5)
        trial_de.append(de.astype(np.float32))

    data_obj = np.empty(len(trial_de), dtype=object)
    for j, arr in enumerate(trial_de):
        data_obj[j] = arr

    labels = np.array([trial.label_code for trial in rec.trials], dtype=np.int8)

    np.savez(
        out_path,
        data=data_obj,
        labels=labels,
        sfreq=np.float32(rec.sfreq),
        window_s=np.float32(de_cfg.window_s),
        step_s=np.float32(de_cfg.effective_step_s),
        n_windows=np.array([d.shape[0] for d in trial_de], dtype=np.int32),
        subject=np.int16(rec.subject),
        session=np.int16(rec.session),
    )
    return out_path


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------
def run_pipeline(
    pre_cfg: PreprocessConfig | None = None,
    de_cfg: DeConfig | None = None,
    subjects: list[int] | None = None,
    sessions: list[int] | None = None,
    skip_de: bool = False,
    validate_de: bool = True,
    out_root: Path | None = None,
    verbose: bool = True,
) -> dict:
    """Process all requested recordings and write outputs + manifest.

    Parameters
    ----------
    validate_de:
        If True, compute self-extracted vs. official-DE correlation for each
        recording and record it in the manifest.
    skip_de:
        If True, skip DE feature extraction entirely (raw_signal only).

    Returns
    -------
    manifest:
        The full manifest dict (also written to ``manifest.json``).
    """
    pre_cfg = pre_cfg or PreprocessConfig()
    de_cfg = de_cfg or DeConfig()
    out_root = Path(out_root) if out_root else config.PROCESSED_DIR
    raw_dir = out_root / "raw_signal"
    de_dir = out_root / "de_features"

    cnt_files = find_cnt_files(subjects, sessions)
    if verbose:
        print(f"[pipeline] {len(cnt_files)} recordings to process -> {out_root}")

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "preprocess_config": pre_cfg.to_dict(),
        "de_config": asdict(de_cfg),
        "n_recordings": len(cnt_files),
        "files": [],
        "errors": [],
        "de_validation": [],
    }

    index_rows: list[dict] = []
    t0 = time.time()

    for k, cnt_file in enumerate(cnt_files, 1):
        label = f"[{k}/{len(cnt_files)}]"
        try:
            if verbose:
                print(f"{label} processing {cnt_file} ...", flush=True)
            rec = preprocess_cnt(cnt_file, pre_cfg)

            raw_path = save_raw_signal(rec, raw_dir)
            if not skip_de:
                save_de_features(rec, de_dir, de_cfg)

            file_entry = {
                "filename": cnt_file,
                "subject": rec.subject,
                "session": rec.session,
                "n_trials": len(rec.trials),
                "sfreq": rec.sfreq,
                "trial_durations_s": [int(t.end_s - t.start_s) for t in rec.trials],
                "raw_signal": raw_path.name,
            }
            manifest["files"].append(file_entry)

            index_rows.append({
                "subject": rec.subject,
                "session": rec.session,
                "cnt_file": cnt_file,
                "raw_signal": raw_path.name,
                "de_features": (_npz_name(rec.subject, rec.session) if not skip_de else ""),
                "n_trials": len(rec.trials),
                "labels": ",".join(str(t.label_code) for t in rec.trials),
            })

            # DE validation against official features.
            if validate_de and not skip_de:
                from .features import compare_with_official
                try:
                    comparison = compare_with_official(rec, de_cfg)
                    manifest["de_validation"].append(comparison)
                    if verbose and comparison.get("mean_pearson_r") is not None:
                        print(
                            f"          DE vs official: mean r = "
                            f"{comparison['mean_pearson_r']}"
                        )
                except Exception as exc:  # noqa: BLE001
                    manifest["de_validation"].append(
                        {"subject": rec.subject, "session": rec.session, "error": str(exc)}
                    )

        except Exception as exc:  # noqa: BLE001 — isolate single-file failures
            manifest["errors"].append({"filename": cnt_file, "error": str(exc)})
            if verbose:
                print(f"{label} ERROR: {exc}")

    manifest["elapsed_seconds"] = round(time.time() - t0, 2)
    manifest["n_succeeded"] = len(manifest["files"])
    manifest["n_failed"] = len(manifest["errors"])

    # Write manifest + index.
    (out_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    index_path = out_root / "index.csv"
    with open(index_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "subject", "session", "cnt_file", "raw_signal", "de_features",
            "n_trials", "labels",
        ])
        writer.writeheader()
        writer.writerows(index_rows)

    if verbose:
        print(
            f"[pipeline] done: {manifest['n_succeeded']} ok, "
            f"{manifest['n_failed']} failed, {manifest['elapsed_seconds']}s."
        )
        if manifest["errors"]:
            print("[pipeline] errors:", manifest["errors"])

    return manifest


__all__ = [
    "find_cnt_files",
    "save_raw_signal",
    "save_de_features",
    "run_pipeline",
]
