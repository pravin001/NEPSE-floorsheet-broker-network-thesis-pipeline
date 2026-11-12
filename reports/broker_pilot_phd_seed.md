# Broker-level monthly panel and network snapshots (Stage 4 · PhD seed)

**Stage 4 of the v2.0 A++ upgrade** · pre-declaration:
`docs/analysis_plan_v2_extension.md` §V2-4 (written before any v2 result).
Runner of record: `scripts/run_v2_stage4.py` · log:
`outputs/logs/v2_stage4.log` · experiment EXP-0011c · deviations #22–#23.

This is a **descriptive** artifact. It performs no inference and tests no
hypothesis. It exists because the brief asks for a broker-level pilot that a
PhD-scale project could extend; R11 (descriptive network statistics only)
applies throughout.

Companion Stage-4 reports: `reports/specification_curve_h7.md`,
`reports/economic_magnitude_analysis.md`,
`reports/heterogeneity_event_study.md`.

---

## 0 · Construction and gates

| item | value |
|---|---|
| source table | `floorsheet_dedup` (57,892,602 post-SV7 rows) |
| valid trades entering the panel | **57,892,602** (all rows; no price/volume filter beyond the corpus SV7 drop) |
| months | **48** (2021-01 → 2024-12) |
| canonical brokers | **91** |
| broker-month rows | **3,026** |
| active brokers per month | min **50**, median **51**, max **90** |
| value unit | integer paisa; `total_value_npr = (buy + sell) / 100`, i.e. buy+sell = **2× market turnover** |
| concentration | exact integer HHI `Σ bvol² / (Σ bvol)²` per (broker, month) buyer side |
| graph | undirected pair graph from aggregated buyer–seller value; self-loops excluded from the graph but retained in flows |
| centrality | betweenness = **unweighted** topology; eigenvector = **weighted by value** |
| determinism | centrality rounded to 12 dp; spring positions rounded to 8 dp; edges sorted before drawing |

**Source-format defect and canonicalisation.** Broker IDs arrive in two forms
across source vintages: canonical two-digit strings (`58`, `01`) and
float-rendered strings (`58.0`, `1.0`). The corpus contains **275,590 dotted-ID
rows on 15 days** (2021-07/08/09/10/11/12 and 2023-12). Left uncorrected, the
same broker becomes two graph nodes: 2023-12 showed **166 active nodes** before
canonicalisation and **83** after (`Xs.0 → zero-padded integer`). The macro is
in `src/nepsemsc/broker/monthly_panel.py`; a Python mirror and a DuckDB test pin
the mapping. The defect touches **37 of 7,126 OOS panel rows (0.52%)**; the
leave-affected-rows-out sensitivity is in §6.

**Coverage eras.** 2021–2023 months have ~51 active brokers (the Kaggle
vintage); 2024 months have 86–90 (the socrateai vintage). Both rendered
snapshots (2021-10 and 2023-06) are inside the Kaggle era, so the snapshots are
internally comparable; 2024 network levels are **not** comparable to 2021–23
levels because the source vintage changes. This is a provenance limitation, not
a market-structure finding.

---

## 1 · Concentration and breadth

| statistic | value |
|---|---|
| cross-stock HHI, median broker-month | **0.0170** |
| HHI p99 | 0.2516 |
| HHI maximum | 1.0000 |
| broker-months with HHI = 1 | **4** |
| broker-months with HHI > 0.5 | 9 |
| stocks traded per broker-month, median | **222** |
| breadth p10 / p90 | 170.5 / 289.0 |
| top-5 broker share of total value | **22.35%** |
| top-10 broker share of total value | **36.46%** |
| monthly total value, median | NPR 137.9 bn (buy+sell) |

The typical broker-month is diversified across ~222 scrips with a low
cross-stock HHI. The HHI=1 cases are brokers active in a single stock in that
month — mechanical, not a market-power estimate. The top-5/top-10 shares use
buy+sell value; double counting cancels in the share, so these are valid
concentration shares of gross broker flow.

---

## 2 · Core–periphery structure

**Declared definition.** Monthly core = top decile of betweenness (ceil 10%,
tie-break total value then broker ID) **and** at least 6 top-decile months in
the trailing up-to-12 calendar months.

| statistic | value |
|---|---|
| core brokers (ever) | **11** |
| core broker-months | **219** |
| leaders (core months) | 58 (43), 34 (41), 45 (40), 49 (38), 44 (18), 57 (15), 42 (13), 38 (8), 17/28/41 (1 each) |
| transitions: core → core | **183** |
| transitions: core → periphery | **28** |
| transitions: periphery → core | **36** |
| active-set entries / exits | 41 / 1 |

The four dominant brokers (58, 34, 45, 49) hold core status in 38–43 of 48
months. The remaining core slots rotate around a small set of large,
persistently active brokers.

### 2.1 Complete-graph degeneracy (important)

In **18 of 48 months** the monthly broker graph is **exactly complete**: every
active broker traded with every other, so betweenness is identically zero.
Across the whole panel, **1,071 of 3,026 broker-months (35.4%)** have zero
betweenness, and **63 core broker-months** carry zero betweenness. In those
months the declared top-decile rule falls back to the value tie-break, so the
“core” label partly reflects value rank rather than topology.

The declared rule is **retained** (changing it after inspection would be a
post-hoc definition). A sensitivity runs the same persistence rule on two
alternative rank variables:

| rank variable | core brokers | core broker-months | Jaccard vs declared | only there | only declared |
|---|---:|---:|---:|---:|---:|
| betweenness (declared) | 11 | 219 | 1.000 | 0 | 0 |
| eigenvector centrality | 9 | 244 | **0.837** | 33 | 8 |
| total value | 10 | 244 | **0.882** | 27 | 2 |

The three definitions agree on most core broker-months (Jaccard .84–.88), but
they are not interchangeable. Any thesis claim about “core brokers” must state
which ranking variable produced it. The descriptive conclusion is robust in
membership, not in exact month counts.

---

## 3 · Top-50 persistence

| subset | transitions | mean Jaccard |
|---|---:|---:|
| all transitions | 47 | 0.9669 |
| months with ≤60 active | 31 | **1.0000** |
| months with >60 active | 17 | **0.9084** |
| >80 active | — | 0.9303 |

The top-50 set is essentially frozen while the active set is ~51 brokers. When
the source vintage expands the active set (2023-08 onward, and 2021-07/08),
Jaccard falls to .85–.96. This is consistent with the fixed top-50 being a
stable large-broker club and the additional 2024 brokers entering below it, but
the source-vintage change confounds any stronger interpretation.

---

## 4 · Snapshots

| month | nodes | edges | core nodes | file |
|---|---:|---:|---:|---|
| 2021-10 (bubble peak) | 51 | 1,275 | 4 | `outputs/figures/broker_network_bubble.png` |
| 2023-06 (normal) | 52 | 1,318 | 5 | `outputs/figures/broker_network_normal.png` |

Both months are near-complete graphs (51 nodes → 1,275 possible edges; 52 →
1,326), which is why the snapshots look like a dense hairball. The figures are
rendered on the top-100 brokers by value (declared cap; never binding here) with
a spring layout seeded `20211006`. The node colour marks core status; edge width
scales with `sqrt(value)`.

The visual message is **density**, not a sparse hub-and-spoke topology. That is
the honest description of this market at monthly aggregation: the top-12 scrips
are traded by almost every active broker.

---

## 5 · What the panel does and does not support

Supported descriptively:

- Broker-level value, breadth, concentration, net position and centrality for
  91 brokers over 48 months.
- Core membership and transition counts under an explicitly declared rule.
- Top-50 persistence and its dependence on the active-set size.
- Two internally comparable monthly snapshots inside the Kaggle era.

Not supported:

- **Causal claims** about broker centrality and prices. No instrument, no
  identification, no event timing at broker level.
- **Broker identity**: IDs are numeric codes; the corpus contains no names,
  licence types or ownership.
- **Intraday sequence**: floorsheet rows are not in execution order (the contract_no
  defect on 2023-02-16 is the extreme case), so no intraday sequence statistic
  is computed here.
- **Cross-source network levels**: 2024 has a different active set and source;
  level comparisons across the 2023/2024 boundary are confounded.
- **True core-periphery estimation**: monthly aggregation and complete graphs
  make betweenness a weak discriminator for most of 2021–22.

---

## 6 · Defect sensitivity for the frozen OLS grid

The 275,590 dotted-ID rows affect 37 OOS rows (0.52%) on four dates:
2021-11-28, 2021-12-27, 2023-12-13, 2023-12-18 (folds 0 and 2). Re-fitting the
10-test DK grid without those rows:

| test | full β (bp) | excl. affected β (bp) | Δβ | p full | p excl. | sign same |
|---|---:|---:|---:|---:|---:|---|
| H1 | −1.557 | −1.613 | −3.6% | .4306 | .4150 | yes |
| H2 | −1.491 | −1.522 | −2.1% | .5753 | .5639 | yes |
| H3 | +0.957 | +1.016 | +6.2% | .7501 | .7367 | yes |
| H4 | +7.510 | +7.445 | −0.9% | .0275 | .0298 | yes |
| H5 | −1.856 | −1.854 | +0.1% | .4875 | .4894 | yes |
| H6 | −10.939 | −10.902 | +0.3% | .0197 | .0202 | yes |
| H7 | +3.952 | +4.054 | +2.6% | .0274 | .0240 | yes |
| H8 | −4.471 | −4.260 | +4.7% | .0459 | **.0563** | yes |
| H9 | +1.817 | +1.768 | −2.7% | .4587 | .4710 | yes |
| H10 | +9.492 | +9.485 | −0.1% | .0138 | .0141 | yes |

All signs are unchanged; no headline flips. The only material movement is H8
losing raw 5% significance (p .0563). The defect is therefore a **caveat, not a
threat** to the frozen results, and the broker panel’s canonicalisation is the
corrected descriptive layer.

---

## 7 · PhD-seed framing (questions, not claims)

1. **Network formation.** Does the dense, near-complete monthly graph reflect
   genuine bilateral trading relationships or simply the small top-12 universe?
   A PhD extension would use the full 530-symbol corpus and a sparse
   graph-estimation method (e.g. graphical lasso on broker-pair flows).
2. **Core stability and liquidity provision.** Are the 4 persistent core
   brokers (58, 34, 45, 49) market makers, or simply the largest retail
   aggregators? The corpus cannot distinguish; a licensed broker-level dataset
   could.
3. **Source-vintage discontinuity.** The 2024 active-set expansion is a
   provenance event. Any structural-break design must treat it as a measurement
   change, not a market entry wave.
4. **Centrality and price impact.** The current panel can correlate centrality
   with next-month returns descriptively. Identification would require
   exogenous broker-level shocks (e.g. licensing changes, outages), which this
   corpus does not contain.

---

## 8 · Pointers

| artifact | content |
|---|---|
| `outputs/tables/broker_level_panel.csv` | 3,026 broker-month rows × 27 columns |
| `outputs/tables/broker_top50_persistence.csv` | 47 month transitions with Jaccard, overlap, active count |
| `outputs/tables/broker_core_transitions.csv` | month-by-month core↔periphery transition matrix |
| `outputs/tables/broker_panel_summary.csv` | headline descriptive summary |
| `outputs/tables/broker_snapshot_summary.csv` | node/edge/core counts for the two rendered months |
| `outputs/tables/broker_core_definition_sensitivity.csv` | betweenness vs eigenvector vs value core comparison |
| `outputs/tables/broker_id_defect_sensitivity.csv` | leave-affected-rows-out OLS sensitivity |
| `outputs/figures/broker_network_bubble.png` · `_normal.png` | declared snapshots |
| `src/nepsemsc/broker/monthly_panel.py` | construction, canonicalisation, centrality, core flags |
| `outputs/logs/v2_stage4.log` | runner log with gates and timings |
