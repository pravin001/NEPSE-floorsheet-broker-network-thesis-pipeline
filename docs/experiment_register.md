# Experiment register (R4/DC19) — every thesis number traces to EXACTLY one row

Statuses: EXECUTED / PARTIALLY EXECUTED / NOT EXECUTED / BLOCKED / FAILED (+ reason).
Numbers quoted in the thesis must cite an experiment_id. Config hash = sha256 of
configs/project.yaml = `29a43e8c12c26260fea5cfbb0349b9a003696bcf60972e9a25ade8c91acff459`.

| id | date | phase/notebook | experiment | input data (anchor) | output artefact | status | key finding |
|---|---|---|---|---|---|---|---|
| EXP-0000 | 2026-11-08 | scaffold | repo scaffold + venv `nepse-msc` (py3.11.16 via uv) + full pytest suite | none | git initial commit; requirements-lock.txt (142 pins) | EXECUTED | 38 unit tests green; 1 nbmake notebook test green |
| EXP-0001a | 2026-11-08 | scripts/extract_sample_month.py | NABIL 2024-12 sample extract from LOCAL socrateai archive (SV1(b) adoption; 20 daily files, sha256 each) + provenance rows | kronos tier3 archive (read-only) | data/raw/floorsheet/NABIL/2024-12.csv · data/metadata/provenance_manifest.csv | EXECUTED | 13,099 rows [REAL]; schema validation PASS; missing broker ids 0/13,099 |
| EXP-0001b | 2026-11-08 | scripts/init_duckdb_load_sample.py | DuckDB init + `floorsheet_raw` load + brief's specified daily-counts query (step 6) | EXP-0001a | data/duckdb/nepse.duckdb | EXECUTED | ~587–839 trades/day, 48–66 unique buyers/sellers on NABIL 2024-12 [REAL] |
| EXP-0001c | 2026-11-08 | scripts/write_sample_hhi_table.py | daily buyer/seller HHI + self_loop_volume_ratio + EoD concentration + top-3 shares via DuckDB SQL (Module-1 SQL first live run) | EXP-0001b | outputs/tables/sample_hhi_selfloop.csv | EXECUTED | buyer_hhi mean 0.056 (min 0.032, max 0.153); one standout day 2024-12-18 self_loop_volume_ratio 33.65% vs month mean ~2.4% [REAL — no interpretation at this stage] |
| EXP-0001d | 2026-11-08 | notebooks/00_smoke_test.ipynb | executable smoke notebook (jupyter nbconvert executed; nbmake test) | EXP-0001a..c | notebooks/00_smoke_test.ipynb (executed outputs embedded) | EXECUTED | versions: py3.11.16, duckdb 2.0.0, pandas 3.1.1, numpy 2.4.6, networkx 3.6.1, sklearn 1.9.1, linearmodels 7.1, statsmodels 0.15.0, plotly 7.1.0; DC4 offset verified 5:45 |
