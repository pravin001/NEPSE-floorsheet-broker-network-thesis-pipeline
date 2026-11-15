# Print-ready thesis tables (v2.0.2 pre-write)

Generated: 2026-11-14T09:40:09Z

Every CSV in this directory is a **projection or transcription of a frozen
artefact**. No regression, test, re-fit, robustness check, simulation or
new estimate is performed here. Values are formatted for print; the
authoritative numeric sources remain under `outputs/tables/`.

## How to use

- Open the CSV for the table number you need. Column names are already
  print labels; replace `_` with spaces in the thesis tool if desired.
- Blank cells mean *not applicable*, not zero.
- Keep the footnotes from `table_manifest.csv` with the table. They define
  units, gates, and the frozen caveats.
- Do not edit a CSV by hand. Change the source or the generator and rerun
  `nepse-msc/bin/python scripts/make_print_tables.py`.
- `table_manifest.csv` records the SHA-256 of every source and output, the
  transform, the rounding rule and the status of each table.

## Table index

| table | title | rows | source status |
|---|---|---:|---|
| Table 1.1 | Pre-declared hypothesis grid and final classification | 10 | DERIVED_PROJECTION |
| Table 1.2 | Canonical headline preview | 10 | DERIVED_PROJECTION |
| Table 1.3 | Economic magnitude versus the declared cost floor | 3 | DERIVED_PROJECTION |
| Table 3.0 | Design summary | 14 | MANUAL_TRANSCRIPTION_FROM_FROZEN_PLAN |
| Table 3.1 | Pre-declaration and freeze timeline | 8 | MANUAL_TRANSCRIPTION_FROM_FROZEN_PLAN |
| Table 3.2 | Anchored walk-forward folds and out-of-sample counts | 4 | DERIVED_PROJECTION |
| Table 3.3 | Feature and outcome dictionary | 12 | VERBATIM_COPY_WITH_CSV_QUOTING_FIX |
| Table 3.4 | Estimator and inference matrix | 6 | MANUAL_TRANSCRIPTION_FROM_FROZEN_PLAN |
| Table 3.5 | Event-study and robustness protocol matrix | 10 | MANUAL_TRANSCRIPTION_FROM_FROZEN_PLAN |
| Table 4.0 | Stage-6 clean-rebuild steps and timings | 21 | DERIVED_PROJECTION |
| Table 4.1 | Source and licence matrix | 6 | MANUAL_TRANSCRIPTION_FROM_VERIFIED_SOURCE |
| Table 4.2 | Corpus quality audit summary | 16 | DOCUMENTED_CONSTANTS |
| Table 4.3 | Volume reconciliation summary | 7 | DERIVED_DESCRIPTIVE_SUMMARY |
| Table 4.4a | Universe selection ranking | 50 | DERIVED_PROJECTION |
| Table 4.4b | Universe exclusions | 23 | DERIVED_PROJECTION |
| Table 4.5a | Clean-rebuild drift summary | 6 | DERIVED_DESCRIPTIVE_SUMMARY |
| Table 4.5b | Clean-rebuild drift audit, artifact detail | 73 | DERIVED_PROJECTION |
| Table 5.1 | Sample, folds and effective N | 10 | DERIVED_PROJECTION |
| Table 5.2 | Main hypothesis grid | 10 | DERIVED_PROJECTION |
| Table 5.3 | Canonical final headline set | 10 | DERIVED_PROJECTION |
| Table 5.4 | Event-study inference | 12 | DERIVED_PROJECTION |
| Table 5.5 | Robustness battery survival | 46 | DERIVED_PROJECTION |
| Table 5.6 | Inference concordance across v2 checks | 10 | DERIVED_PROJECTION |
| Table 5.7a | Quantile tail estimates | 10 | DERIVED_PROJECTION |
| Table 5.7b | Trade-size heterogeneity, primary specification | 18 | DERIVED_PROJECTION |
| Table 5.7c | H7 specification-curve summary | 3 | DERIVED_PROJECTION |
| Table 5.7d | Subgroup heterogeneity grid | 40 | DERIVED_PROJECTION |
| Table 5.7e | Economic magnitude versus the cost floor | 3 | DERIVED_PROJECTION |

## Status vocabulary

| status | meaning |
|---|---|
| DERIVED_PROJECTION | Column/row projection or unit conversion of a frozen CSV. |
| DERIVED_DESCRIPTIVE_SUMMARY | Counts, medians or shares already present in a frozen table, regrouped for print. |
| DOCUMENTED_CONSTANTS | Counts transcribed from the Ch.4 handoff pack and experiment register; no audit re-run. |
| MANUAL_TRANSCRIPTION_FROM_FROZEN_PLAN | Design/protocol table transcribed from a frozen plan; no numeric estimate. |
| MANUAL_TRANSCRIPTION_FROM_VERIFIED_SOURCE | Licence matrix transcribed from the live, timestamped licence review. |
| VERBATIM_COPY_WITH_CSV_QUOTING_FIX | Content-identical copy with one malformed CSV field correctly quoted. |

## Known source quirk

`reports/chapter_assets/ch3_feature_dictionary.csv` is not valid CSV as
committed: line 4 has an unquoted comma in its final `notes` field. Its
chapter-map hash is audited, so the source is left untouched; the print
copy quotes that one field and changes nothing else.

