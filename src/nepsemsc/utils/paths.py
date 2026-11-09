import os
from pathlib import Path


def repo_root() -> Path:
    """Repository root, independent of cwd (src/nepsemsc/utils/paths.py → parents[4])."""
    here = Path(__file__).resolve()
    # util=0, nepsemsc=1, src=2, repo=3 → parents[3]
    for parent in (here.parents[3],):
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("repo root not found; run tests from inside the repository")


def data_dir(sub: str) -> Path:
    return repo_root() / "data" / sub


def outputs_dir(sub: str) -> Path:
    return repo_root() / "outputs" / sub


os.environ.setdefault("PYTHONHASHSEED", "0")
