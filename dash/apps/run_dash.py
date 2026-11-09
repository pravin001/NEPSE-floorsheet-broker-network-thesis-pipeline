"""Phase 6 dashboard launcher stub (app is BUILT in Phase 6).

Reads ONLY versioned extracts from dash/extracts/ (dataset_version +
config_hash + experiment_id per row). No scraping, no fitting in callbacks.
"""
from __future__ import annotations


def build_app():
    raise NotImplementedError(
        "Dash dashboard is a Phase 6 deliverable (2026-11-20/21). "
        "If it fails to build: label NOT BUILT in the status report (brief)."
    )


if __name__ == "__main__":
    raise SystemExit(build_app.__doc__)
