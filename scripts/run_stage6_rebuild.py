"""Stage-6 clean-rebuild driver (v2 plan V2-6).

Runs the documented pipeline from a clean derived-data state and records
per-step wall time.  The ONLY paths this driver may delete are
``data/processed/`` and ``data/duckdb/`` (raw archives are provenance anchors
and are never touched).

Usage:
    nepse-msc/bin/python scripts/run_stage6_rebuild.py --clean
    nepse-msc/bin/python scripts/run_stage6_rebuild.py          # resume/verify

Outputs:
    outputs/logs/v2_stage6_rebuild.log            full streamed log
    outputs/logs/v2_stage6_rebuild_timings.csv    one row per step
"""
from __future__ import annotations

import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "outputs" / "logs"
LOG_PATH = LOGS / "v2_stage6_rebuild.log"
TIMING_PATH = LOGS / "v2_stage6_rebuild_timings.csv"

# Documented pipeline order.  Every script reads only artifacts produced by an
# earlier step (or the raw archives / tracked metadata).
STEPS = [
    ("universe", "scripts/select_top10.py"),
    ("ingest", "scripts/ingest_corpus.py"),
    ("audit", "scripts/audit_corpus.py"),
    ("ohlcv", "scripts/build_ohlcv.py"),
    ("reconcile", "scripts/reconcile_volumes.py"),
    ("daily_features", "scripts/build_daily_features.py"),
    ("outcomes", "scripts/build_outcomes.py"),
    ("broker_persistence", "scripts/broker_persistence_table.py"),
    ("feature_summary", "scripts/summarize_features.py"),
    ("anomaly_scoring", "scripts/run_anomaly_scoring.py"),
    ("panel_regressions", "scripts/run_panel_regressions.py"),
    ("regime_split", "scripts/run_regime_split.py"),
    ("event_study", "scripts/run_event_study.py"),
    ("robustness", "scripts/run_robustness.py"),
    ("dashboard_cache", "scripts/build_dashboard_cache.py"),
    ("engine_validation", "scripts/validate_v2_engine.py"),
    ("v2_stage1", "scripts/run_v2_stage1.py"),
    ("v2_stage2", "scripts/run_v2_stage2.py"),
    ("v2_stage3", "scripts/run_v2_stage3.py"),
    ("v2_stage4", "scripts/run_v2_stage4.py"),
    ("final_headline_set", "scripts/build_v2_final_headline_set.py"),
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _tree_stats(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    files = [p for p in path.rglob("*") if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)


def _clean(handle) -> None:
    """Delete ONLY data/processed/ and data/duckdb/."""
    targets = [ROOT / "data" / "processed", ROOT / "data" / "duckdb"]
    raw = ROOT / "data" / "raw"
    raw_before = _tree_stats(raw)
    print(f"[clean] data/raw before: {raw_before[0]} files, {raw_before[1]} bytes",
          file=handle, flush=True)
    for target in targets:
        if target.exists():
            n, b = _tree_stats(target)
            print(f"[clean] removing {target.relative_to(ROOT)} "
                  f"({n} files, {b} bytes)", file=handle, flush=True)
            shutil.rmtree(target)
        else:
            print(f"[clean] {target.relative_to(ROOT)} already absent",
                  file=handle, flush=True)
    raw_after = _tree_stats(raw)
    print(f"[clean] data/raw after:  {raw_after[0]} files, {raw_after[1]} bytes",
          file=handle, flush=True)
    if raw_before != raw_after:
        raise SystemExit("RAW ARCHIVE CHANGED during clean — aborting")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true",
                        help="delete data/processed/ and data/duckdb/ first")
    args = parser.parse_args()

    if os.environ.get("NEPSEMS_SKIP_LOAD") == "1":
        raise SystemExit("NEPSEMS_SKIP_LOAD is set; a fresh rebuild must unset it")

    LOGS.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "w", encoding="utf-8") as handle:
        def log(msg: str) -> None:
            print(msg, file=handle, flush=True)
            print(msg, flush=True)

        log("# v2 Stage-6 clean rebuild")
        log(f"# started {_utc()}")
        log(f"# python {sys.version.split()[0]} | {platform.platform()}")
        log(f"# root {ROOT}")
        log(f"# clean={args.clean}")
        log(f"# lock sha256 {_sha256(ROOT / 'requirements-lock.txt')}")
        log("")

        if args.clean:
            _clean(handle)
        else:
            for rel in ("data/processed", "data/duckdb"):
                if _tree_stats(ROOT / rel)[0] > 0:
                    raise SystemExit(
                        f"{rel} is not empty; re-run with --clean for a clean rebuild")

        with open(TIMING_PATH, "w", encoding="utf-8") as tf:
            tf.write("step,script,start_utc,end_utc,duration_s,exit_code,sha256\n")
            tf.flush()

            for name, script in STEPS:
                path = ROOT / script
                if not path.is_file():
                    raise SystemExit(f"missing pipeline script: {script}")
                digest = _sha256(path)
                log("=" * 78)
                log(f"[{_utc()}] STEP {name}: {script}")
                log("=" * 78)
                start = time.time()
                started = _utc()
                proc = subprocess.Popen(
                    [sys.executable, script],
                    cwd=ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env={k: v for k, v in os.environ.items()
                         if k != "NEPSEMS_SKIP_LOAD"},
                )
                assert proc.stdout is not None
                for line in proc.stdout:
                    log(line.rstrip("\n"))
                code = proc.wait()
                duration = time.time() - start
                ended = _utc()
                with open(TIMING_PATH, "a", encoding="utf-8") as tf:
                    tf.write(f"{name},{script},{started},{ended},"
                             f"{duration:.3f},{code},{digest}\n")
                    tf.flush()
                log(f"[{ended}] STEP {name} exit={code} wall={duration:.1f}s")
                if code != 0:
                    raise SystemExit(f"pipeline step {name} failed (exit {code})")

        log("")
        log(f"# finished {_utc()}")
        log("# all steps completed with exit 0")


if __name__ == "__main__":
    main()
