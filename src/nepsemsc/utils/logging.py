"""Phase logger: console + outputs/logs/phaseN.log (engineering rule 3)."""
from __future__ import annotations

import logging
from pathlib import Path

from nepsemsc.utils.paths import outputs_dir


def phase_logger(phase: int | str, name: str = "nepsemsc") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)sZ %(levelname)s %(name)s: %(message)s",
                            datefmt="%Y-%m-%dT%H:%M:%S")
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)
    logdir = outputs_dir("logs")
    logdir.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(logdir / f"phase{phase}.log")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.propagate = False
    return logger
