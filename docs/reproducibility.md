# Reproducibility guide (living draft — finalized at Phase 7 freeze)

## Environment

```bash
cd ~/research/nepse-floorsheet-microstructure
make bootstrap && make install && make lock     # venv `nepse-msc`, py3.11.16 (uv-managed)
```
Pins reproduced in `requirements-lock.txt` (committed after first install).

## Data

1. NABIL 2024-12 sample (Phase 1): `make smoke` (uses LOCAL socrateai
   archive at the sibling project path; sha256 verified per source file).
2. Full top-10 × window (Phase 2): backfill/download via the socrateai index
   + quality audit + OHLCV reconciliation (script noted in AGENTS.md).

## Tests

```bash
make test-fast          # unit + leakage + SE-spec suite
make test               # + nbmake notebook execution (DC19)
```

## Notebooks

Blocks execute top-to-bottom via nbmake; stale-state cheating is a test failure.

## Seeds

`src/nepsemsc/utils/seeds.py` (DC14). Isolation Forest per fold, placebos,
network layout. Pre-declared 2026-11-08 in `docs/analysis_plan.md` §8.

## Git

Every experiment row in `docs/experiment_register.md` names the artefact +
config sha256; manifests in `data/metadata/` + `outputs/manifests/` are
tracked in git.
