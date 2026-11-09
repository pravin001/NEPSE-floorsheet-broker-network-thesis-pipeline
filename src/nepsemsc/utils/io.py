"""Atomic writes + hashing (never leave a half-written artefact)."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import hashlib


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def atomic_write_bytes(path: str | Path, data: bytes) -> Path:
    p = Path(path)
    tmp = p.with_suffix(p.suffix + ".tmp")
    ensure_dir(tmp.parent)
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, p)
    return p


def atomic_write_text(path: str | Path, text: str) -> Path:
    return atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path: str | Path, obj, indent: int = 2) -> Path:
    return atomic_write_text(path, json.dumps(obj, indent=indent, default=str))


def atomic_write_df(df, path: str | Path, index: bool = False) -> Path:
    """Write a DataFrame (csv or parquet by suffix) atomically."""
    p = Path(path)
    tmp = p.with_suffix(p.suffix + ".tmp")
    ensure_dir(tmp.parent)
    if p.suffix == ".parquet":
        df.to_parquet(tmp, index=index)
    elif p.suffix == ".csv":
        df.to_csv(tmp, index=index)
    else:
        raise ValueError(f"unsupported suffix: {p.suffix}")
    os.replace(tmp, p)
    return p


def copy_file_atomic(src: str | Path, dst: str | Path) -> Path:
    """Copy a file via a tmp path then rename (for staged raw files)."""
    src, dst = Path(src), Path(dst)
    dst = ensure_dir(dst.parent)
    tmp = dst.with_suffix(dst.suffix + ".tmp")
    shutil.copyfile(src, tmp)
    os.replace(tmp, dst)
    return dst
