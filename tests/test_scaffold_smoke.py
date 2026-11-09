"""Scaffold smoke tests: config fingerprint, Kathmandu offset (DC4), DuckDB
roundtrip, seed policy integrity (DC14)."""
from pathlib import Path

from datetime import timedelta
import pytest


def test_config_loads_with_fingerprint():
    from nepsemsc.utils.config import load_config
    cfg = load_config()
    assert cfg["project"] == "nepse-floorsheet-microstructure"
    assert len(cfg["_fingerprint_sha256"]) == 64
    assert load_config()["_fingerprint_sha256"] == cfg["_fingerprint_sha256"]


def test_kathmandu_offset_is_5_45():
    from nepsemsc.utils.tz import now_ktm, verify_offset
    assert now_ktm().utcoffset() == timedelta(hours=5, minutes=45)
    assert verify_offset()


def test_seed_policy_shape():
    from nepsemsc.utils.seeds import IF_FOLD_SEEDS, PLACEBO_SEEDS, if_seed, placebo_seed
    assert len(PLACEBO_SEEDS) == 200
    assert len(set(PLACEBO_SEEDS)) == 200
    assert len(IF_FOLD_SEEDS) == 4
    assert if_seed(0) == IF_FOLD_SEEDS[0]
    assert placebo_seed(199) == PLACEBO_SEEDS[-1]
    with pytest.raises(ValueError):
        if_seed(4)


def test_duckdb_roundtrip(tmp_path):
    import duckdb
    df = pytest.importorskip("pandas").DataFrame({
        "symbol": ["NABIL"] * 4,
        "v": [1.0, 2.0, 3.0, 4.0],
    })
    con = duckdb.connect(str(tmp_path / "t.duckdb"))
    con.register("toy", df)
    con.execute("CREATE TABLE t AS SELECT * FROM toy")
    out = con.execute("SELECT SUM(v), COUNT(*) FROM t").fetchone()
    assert out == (10.0, 4)


def test_io_atomic_write(tmp_path):
    from nepsemsc.utils.io import atomic_write_text, sha256_file
    p = atomic_write_text(tmp_path / "a.txt", "hello")
    assert p.exists() and sha256_file(p) == sha256_file(tmp_path / "a.txt")
    assert not (tmp_path / "a.txt.tmp").exists()
