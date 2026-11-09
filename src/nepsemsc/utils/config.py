"""Config loading with SHA-256 fingerprint (provenance-grade)."""
from __future__ import annotations

from pathlib import Path

import yaml

from nepsemsc.utils.io import sha256_text
from nepsemsc.utils.paths import repo_root


def config_path(name: str = "project.yaml") -> Path:
    return repo_root() / "configs" / name


def load_config(name: str = "project.yaml") -> dict:
    """Load a yaml config and attach its sha256 fingerprint under '_fingerprint'
    (changes to a config are therefore detectable in every downstream manifest)."""
    p = config_path(name)
    raw = p.read_text()
    cfg = yaml.safe_load(raw)
    if not isinstance(cfg, dict):
        raise ValueError(f"config {p} did not parse to a dict")
    cfg = dict(cfg)
    cfg["_fingerprint_sha256"] = sha256_text(raw)
    cfg["_path"] = str(p)
    return cfg
