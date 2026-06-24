#!/usr/bin/env python
"""SEED-V batch preprocessing entry point.

Usage examples::

    # Full batch (all 16 subjects × 3 sessions):
    python scripts/preprocess.py

    # Smoke test: process subject 1 session 1 only, skip DE validation:
    python scripts/preprocess.py --smoke

    # Custom subjects / sessions:
    python scripts/preprocess.py --subjects 1 2 3 --sessions 1

    # Skip DE features entirely (raw signal only):
    python scripts/preprocess.py --skip-de

    # Skip official DE validation (faster):
    python scripts/preprocess.py --no-validate
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the repo root is on sys.path so ``seed_v`` is importable.
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from seed_v.features import DeConfig
from seed_v.pipeline import run_pipeline
from seed_v.preprocess import PreprocessConfig


def main() -> None:
    ap = argparse.ArgumentParser(
        description="SEED-V batch preprocessing: raw .cnt -> preprocessed trials + DE features.",
    )
    ap.add_argument(
        "--smoke",
        action="store_true",
        help="Smoke test: process only subject 1 session 1, skip DE validation.",
    )
    ap.add_argument(
        "--subjects",
        type=int,
        nargs="*",
        default=None,
        help="Subject IDs to process (1-16). Default: all.",
    )
    ap.add_argument(
        "--sessions",
        type=int,
        nargs="*",
        default=None,
        help="Session IDs to process (1-3). Default: all.",
    )
    ap.add_argument(
        "--skip-de",
        action="store_true",
        help="Skip DE feature extraction (raw_signal only).",
    )
    ap.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip official DE feature comparison.",
    )
    ap.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output root directory (default: SEED_V_PROCESSED from .env).",
    )
    # Preprocessing parameters (override defaults).
    ap.add_argument("--l-freq", type=float, default=None, help="Band-pass lower Hz.")
    ap.add_argument("--h-freq", type=float, default=None, help="Band-pass upper Hz.")
    ap.add_argument("--notch", type=float, default=None, help="Notch freq Hz (0 to disable).")
    ap.add_argument("--sfreq", type=float, default=None, help="Target sampling rate Hz.")
    ap.add_argument("--reference", type=str, default=None, help="Re-reference method: car|none.")
    # DE parameters.
    ap.add_argument("--de-window", type=float, default=None, help="DE window length in seconds.")
    ap.add_argument("--de-step", type=float, default=None, help="DE step in seconds (0 = no overlap).")

    args = ap.parse_args()

    # Build config objects with overrides.
    pre_kw: dict = {}
    if args.l_freq is not None:
        pre_kw["l_freq"] = args.l_freq
    if args.h_freq is not None:
        pre_kw["h_freq"] = args.h_freq
    if args.notch is not None:
        pre_kw["notch_freq"] = args.notch if args.notch > 0 else None
    if args.sfreq is not None:
        pre_kw["target_sfreq"] = args.sfreq
    if args.reference is not None:
        pre_kw["reference"] = args.reference
    pre_cfg = PreprocessConfig(**pre_kw)

    de_kw: dict = {}
    if args.de_window is not None:
        de_kw["window_s"] = args.de_window
    if args.de_step is not None:
        de_kw["step_s"] = args.de_step if args.de_step > 0 else None
    de_cfg = DeConfig(**de_kw)

    subjects = args.subjects
    sessions = args.sessions
    if args.smoke:
        subjects = [1]
        sessions = [1]

    out_root = Path(args.output) if args.output else None

    manifest = run_pipeline(
        pre_cfg=pre_cfg,
        de_cfg=de_cfg,
        subjects=subjects,
        sessions=sessions,
        skip_de=args.skip_de,
        validate_de=(not args.no_validate and not args.smoke),
        out_root=out_root,
    )

    if manifest["n_failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
