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
| Floorsheets 2021–2023 | Kaggle `viking303/nepse-historical-floorsheet` v14 (CC0, verified) | ADOPTED — 935 day files; bubble-era corpus |
| Floorsheets 2024 | `socrateai-official/nepse-open-data` (MIT, verified) — local archive 232 files | ADOPTED (SV1(b); nepalstock.com-direct is network-blocked) |
| OHLCV | Kaggle tier1 (100 scrips, 2012→2025-09) + tier2 `SamirWagle/Nepse-All-Scraper` gap-fill | tier1 Kaggle metadata declares MIT, but prices are “scraped from NEPSE Alpha” (upstream `UNCERTAIN`; see `reports/licence_review.md`); tier2 has no licence file and is gap-fill only |
| NEPSE index | `menaceXnadin` composite (1997→2026-11-06) | SECONDARY shading/benchmark only; licence `unstated_in_repo` |

The adopted corpus is **1,167 day files** (935 Kaggle + 232 socrateai; 2024
Kaggle cross-check only), **57,927,926 raw rows** → **57,892,630 deduplicated
rows**, covering **938/940** calendar sessions (2021-01-01→2024-12-31; gaps
2021-09-01 and 2023-11-27). The two documented source exceptions are the
2021-03-07→03-08 relabel and the 2023-02-16 `contract_no_defect`; both are in
`docs/analysis_deviations.md` and `reports/limitations.md`.

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

## Citation and licence

Code is MIT-licensed; see `CITATION.cff` and `LICENSE`. Input-data licences are
recorded per file in `data/metadata/provenance_manifest.csv` and reviewed in
`reports/licence_review.md`. The Kaggle-declared tier1 OHLCV licence is MIT,
but public redistribution of price-derived figures remains subject to the
unverified upstream NEPSE Alpha terms. No raw data is redistributed here.
