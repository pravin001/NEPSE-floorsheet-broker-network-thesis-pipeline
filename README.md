# NEPSE Floorsheet Microstructure — MSc Thesis Pipeline

**Thesis:** *Broker Networks, Concentration, and Market Integrity in a Frontier
Exchange: Evidence from NEPSE Floorsheets.*
Pilot study for a PhD proposal on frontier-market broker-network surveillance.

**Epistemic frame (binding):** this is a **predictive** test, not causal
identification. Anomalous network topology is claimed to *predict* next-day
returns/volatility — consistent with, but not proof of, manipulation. Forbidden
phrasing: "confirmed manipulation", "wash trading" (→ "self-loop volume").

## Quickstart

```bash
cd ~/research/nepse-floorsheet-microstructure
make bootstrap          # uv venv nepse-msc, python 3.11
make install            # deps + editable install
make test-fast          # pytest (must be green — R10 gate)
make smoke              # extract NABIL 2024-12 sample + DuckDB init
make nb00               # execute notebooks/00_smoke_test.ipynb
```

## Data provenance

| Tier | Source | Status |
|---|---|---|
| Floorsheets | `socrateai-official/nepse-open-data` (MIT, verified) — local archive 650 files, 2024-01→2026-11 | ADOPTED (SV1(b); nepalstock.com-direct is network-blocked) |
| OHLCV | Kaggle `rohankasichhwa/nepse-daily-stock-data-2012-2025` (local, 101 files) | licence pending user UI check |
| Prices proxy | `SamirWagle/Nepse-All-Scraper` | no licence file — analytic use with attribution |

2021–2023 floorsheets (bubble regime): **not evidenced yet** — bounded Phase-2
search, fork decision logged in `docs/block_log.md`.

## Layout

- `src/nepsemsc/` — pipeline code (`data`, `network`, `ml`, `evaluation`, `utils`)
- `configs/project.yaml` — pre-declared constants, SHA-256 fingerprinted
- `docs/analysis_plan.md` — frozen analysis plan (DC20, written pre-results)
- `docs/experiment_register.md` — every thesis number traces to a row (R4)
- `tests/` — leakage, placebo, walk-forward, SE-specification etc. ( executable)
- `outputs/` — tables, figures, manifests, logs · `dash/` — Phase 6 dashboard

## Status

See `AGENTS.md` (fresh-session resume point) and
`docs/experiment_register.md`. Phase 1 executed 2026-11-08.
