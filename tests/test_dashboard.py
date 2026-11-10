"""Phase-6 dashboard smoke tests (extracts-only contract)."""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import dash  # noqa: E402


def _import_app():
    import dashboard_app            # noqa: F401 (module-level create_app)
    return dashboard_app


def test_all_four_pages_register():
    dash.page_registry.clear()
    app_mod = _import_app()         # create_app() ran at import
    assert app_mod is not None
    names = sorted(p["name"] for p in dash.page_registry.values())
    assert len(dash.page_registry) == 4, names
    paths = sorted(p["path"] for p in dash.page_registry.values())
    assert paths == ["/", "/anomaly", "/features", "/inference"], paths


def test_layout_builds_without_duckdb(monkeypatch):
    """The extracts-only contract: building any layout must NOT need DuckDB.
    Simulate a broken DB module and require every page layout to still render."""
    dash.page_registry.clear()
    _import_app()
    import builtins
    real_import = builtins.__import__

    def no_duckdb(name, *a, **k):
        if name == "duckdb":
            raise RuntimeError("runtime DuckDB is forbidden in the app")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", no_duckdb)
    for page in dash.page_registry.values():
        layout = page["layout"]() if callable(page["layout"]) \
            else page["layout"]
        assert layout is not None


def test_cache_builder_outputs_exist():
    cache = ROOT / "data/processed/dashboard_cache"
    for f in ("top12_daily_features.csv", "anomaly_test_rows.csv",
              "extract_monthly_summary.csv", "calendar.csv"):
        assert (cache / f).is_file(), f


def test_app_serves_pages_over_http():
    """Boot the dev server in a thread; every page answers HTTP 200."""
    import threading
    import urllib.request

    dash.page_registry.clear()
    app_mod = _import_app()
    srv = threading.Thread(
        target=lambda: app_mod.app.run(host="127.0.0.1", port=8051,
                                       debug=False),
        daemon=True)
    srv.start()
    deadline = time.time() + 30
    last_err = None
    while time.time() < deadline:
        try:
            urllib.request.urlopen("http://127.0.0.1:8051/", timeout=2)
            break
        except Exception as exc:        # noqa: BLE001 (server not up yet)
            last_err = exc
            time.sleep(0.5)
    else:
        raise AssertionError(f"server never came up: {last_err}")
    for path in ("/", "/features", "/anomaly", "/inference"):
        with urllib.request.urlopen(f"http://127.0.0.1:8051{path}",
                                    timeout=10) as resp:
            assert resp.status == 200, path
