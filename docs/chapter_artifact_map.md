# Chapter → artefact crosswalk (v2.1.0 handoff)

**Version note.** v2.1.0 corrects the `reciprocity_volume` metric and
rebuilds every downstream artifact. The v1 claims that used to point at
the live `hypothesis_grid_results.csv` and `event_study_summary.csv` now
point at the byte-frozen v2.0.2 copies in
`outputs/tables/superseded_v2_0_2/`. Live results carry
`claim_version = v2`. The correction record is
`reports/reciprocity_correction.md`; the tag `v2.0.2-prewrite` is not
moved.

**Status.** Verified crosswalk replacing the Stage-5 placeholder map.
Every row is audited by `scripts/audit_chapter_map.py`;
`tests/test_chapter_map_integrity.py` fails the build if a path, hash,
provenance-manifest row, or EXP key drifts.

**Defect record.** The Stage-5 map named six conceptual files that were
never produced (`main_regression.csv`, `placebo_distribution.csv`,
`regime_split.csv`, `event_study_car.csv`, `robustness_matrix.csv`,
`broker_persistence.csv`). This was latent documentation drift, not a v2
regression; the Stage-6 register audit did not cover the chapter surface.
Diagnosis and audit-coverage gap: `docs/analysis_deviations.md` #31.

**Reading the table.** `claim_version` distinguishes frozen v1 claims
(`v1`) from v2 governance/robustness claims (`v2`). A v1 number remains
citable even when v2 reclassifies the hypothesis: H7's v1 p=.0274 is a
v1 claim, while its `NULL_FRAGILE` label is a v2 claim. `status` is
`VERIFIED`, `VERIFIED_V1_IMMUTABLE`, or `SCAFFOLD` (structural handoff
asset with no numeric claim). Hashes are SHA-256 at generation; the audit
also requires the latest hash-bearing provenance-manifest row to match.

| chapter | section | claim_id | artifact_path | exp_id | sha256 | claim_version | status |
|---|---|---|---|---|---|---|---|
| Ch.1 Introduction | 1.1 | CH1-1.1-SCOPE | `README.md` | EXP-0002b,EXP-0012 | `cf0532aafaa72345cf5f107646206e357c22231741f22ae958367caeff377cc9` | v2 | VERIFIED |
| Ch.1 Introduction | 1.1 | CH1-1.1-LIMITS | `reports/limitations.md` | EXP-0012 | `8793f4a70c491b27bf120c90970500c903eaa5e5ce46a1b102b6298b344be280` | v2 | VERIFIED |
| Ch.1 Introduction | 1.2 | CH1-1.2-HYPOTHESES | `docs/analysis_plan.md` | EXP-0004b | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.1 Introduction | 1.3 | CH1-1.3-HEADLINE | `outputs/tables/v2_final_headline_set.csv` | EXP-0012 | `049b83315d07a84fa6df9433dc9d1470ae23854c993b751344529d0faf3a53cd` | v2 | VERIFIED |
| Ch.1 Introduction | 1.4 | CH1-1.4-COST | `outputs/tables/economic_magnitude.csv` | EXP-0011f | `2390fa2fa83bf689838f904b05b3e325cf7ca06ee784abc91df41863264a4a70` | v2 | VERIFIED |
| Ch.1 Introduction | 1.5 | CH1-1.5-CONTRIBUTION | `reports/economic_magnitude_analysis.md` | EXP-0011f | `ea746e8ff99d42d6f49c5ccfdd596e7aad65a6efade294b5d558a85136d31168` | v2 | VERIFIED |
| Ch.2 Literature | 2.1 | CH2-2.1-MATRIX | `reports/chapter_assets/ch2_literature_matrix.csv` | EXP-0014 | `f1287a5c1347bd196ab70b13b9237e7154b84f86342c41bcdb75f1afe5dbd0c6` | v2 | SCAFFOLD |
| Ch.2 Literature | 2.2 | CH2-2.2-GAP | `reports/chapter_assets/ch2_research_gap.md` | EXP-0014 | `8b25e3999a845f74a074a669f8c48de69159425bba566195311c3b2718f02f20` | v2 | SCAFFOLD |
| Ch.2 Literature | 2.3 | CH2-2.3-COMPARE | `reports/chapter_assets/ch2_comparison_table.csv` | EXP-0014 | `6f33ba765e746366852f7308b91a5d245a2ee36695f33f5446dc446b5e0e3f6a` | v2 | SCAFFOLD |
| Ch.2 Literature | 2.4 | CH2-2.4-HYPOMAP | `docs/analysis_plan.md` | EXP-0004b | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.2 Literature | 2.4 | CH2-2.4-FRONTIER | `reports/limitations.md` | EXP-0012 | `8793f4a70c491b27bf120c90970500c903eaa5e5ce46a1b102b6298b344be280` | v2 | VERIFIED |
| Ch.3 Methodology | 3.1 | CH3-3.1-DESIGN | `docs/analysis_plan.md` | EXP-0004b | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.3 Methodology | 3.2 | CH3-3.2-PREDECL | `docs/analysis_plan_v2_extension.md` | EXP-0008a | `5599c5a33d3801cc28143716db40ea186d70dc8a1d8b02e8016b4aff5f9d9d98` | v2 | VERIFIED |
| Ch.3 Methodology | 3.2 | CH3-3.2-FREEZE | `configs/v2_freeze/freeze_manifest.csv` | EXP-0013 | `386273a2976f24b4a2da4f13ea5cbea5f918711d734f8292f249273308cc890b` | v2 | VERIFIED |
| Ch.3 Methodology | 3.3 | CH3-3.3-WALKFORWARD | `reports/chapter_assets/ch3_walk_forward_diagram.md` | EXP-0004a | `4e3a2ff918a6a304369732dc9805ecf428d75adb3e0f017cdf049800a980d66f` | v2 | SCAFFOLD |
| Ch.3 Methodology | 3.3 | CH3-3.3-WALKFORWARD-PLAN | `docs/analysis_plan.md` | EXP-0004a | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.3 Methodology | 3.4 | CH3-3.4-FEATURES | `reports/chapter_assets/ch3_feature_dictionary.csv` | EXP-0003a | `e9a618997af38d891dabc0ed326031e4712526ba706bc0ca568f0816579173d0` | v2 | SCAFFOLD |
| Ch.3 Methodology | 3.5 | CH3-3.5-ESTIMATION | `docs/analysis_plan.md` | EXP-0004b | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.3 Methodology | 3.6 | CH3-3.6-ROBUSTNESS | `docs/analysis_plan.md` | EXP-0005a | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.3 Methodology | 3.6 | CH3-3.6-EVENT | `docs/analysis_plan.md` | EXP-0004e | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.1 | CH4-4.1-PIPELINE | `reports/chapter_assets/ch4_pipeline_diagram.md` | EXP-0013 | `b043e3a066aee065c07c56f2b408505d3deeba3832b51e5279d0f7348428093f` | v2 | SCAFFOLD |
| Ch.4 Data Engineering | 4.1 | CH4-4.1-DRIVER | `scripts/run_stage6_rebuild.py` | EXP-0013 | `01748ac61512065392375bdf441fe7ccb507d18b1c4430cdc17c9cd71f562a3a` | v2 | VERIFIED |
| Ch.4 Data Engineering | 4.2 | CH4-4.2-PROVENANCE | `data/metadata/corpus_files_sha256.csv` | EXP-0002b | `e78df58d539b59e4e8e8636437a8870ffb3a727a9095c7c00d9e0931cffbedac` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.2 | CH4-4.2-LICENCE | `docs/ai_use_policy.md` | EXP-0002d | `8685a8f2a4b517b437e7fd9c57e865bdcb720d1e46fd5540919eaac272aba129` | v2 | VERIFIED |
| Ch.4 Data Engineering | 4.3 | CH4-4.3-CORPUS-AUDIT | `notebooks/01_data_quality_audit.ipynb` | EXP-0002f | `4fb7abe2b9aa2a176e00a58c5cb043e6236629a558e00e4ccc068e864165bb56` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.3 | CH4-4.3-DUP | `outputs/tables/corpus_duplicate_keys.csv` | EXP-0002c | `d5e30913fab94cf90cefb27f61cc23b047312c1f750b445ae609a84983cf3cc7` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.3 | CH4-4.3-MISSING | `outputs/tables/corpus_missing_broker_ids.csv` | EXP-0002c | `dc1415424aa3095f0af1ef712ec63cc4932c7c21b4e65847ef85b7adff37e7b0` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.3 | CH4-4.3-COVERAGE | `outputs/tables/corpus_symbol_coverage.csv` | EXP-0002c | `f2a27b676a93aca7baea460e1fba2999e21d2035cc7fb6d31dc0bd4e7e2b07d5` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.3 | CH4-4.3-DAILY | `outputs/tables/corpus_daily_summary.csv` | EXP-0002c | `170d03924dbec371f89c0fb031cbb2cb0fabab9a847cf18b9d3bbb9b141a9e2e` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.4 | CH4-4.4-VOLUME | `outputs/tables/volume_reconciliation.csv` | EXP-0002e | `112b99c246e1308551cce6178667458774aeabd8c7e41d057dd7f47d697f0251` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.5 | CH4-4.5-UNIVERSE | `outputs/tables/universe_selected_top10.csv` | EXP-0002a | `5f1ff249050a72a9c1cd23575d47163fbce9a64ec66812dd9c033a8a8b06b21a` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.5 | CH4-4.5-EXCLUSIONS | `outputs/tables/universe_exclusions.csv` | EXP-0002a | `ac547acc53717642273edba603dc47d8f68b1c973fe3a0d16290706a7365f6fc` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.6 | CH4-4.6-DRIFT | `outputs/tables/v2_clean_rebuild_audit.csv` | EXP-0013 | `e7c913a8c8401a55bde3c7fe31f71667e9a4047b40f6ee9165f5208b6d6d2ef2` | v2 | VERIFIED |
| Ch.4 Data Engineering | 4.6 | CH4-4.6-REPRO | `docs/reproducibility.md` | EXP-0013 | `ff024c17ab86e46fae89dffcc13407c454b882cfefc18ea6b7f25372cf69c541` | v2 | VERIFIED |
| Ch.5 Results | 5.1 | CH5-5.1-SAMPLE | `outputs/tables/hypothesis_grid_results_v2.csv` | EXP-0011a | `a5486cd345cf60c070805c05a672be0213491fe22e263158edaf5e3452601874` | v2 | VERIFIED |
| Ch.5 Results | 5.2 | CH5-5.2-GRID-V1 | `outputs/tables/superseded_v2_0_2/hypothesis_grid_results.csv` | EXP-0004b | `9f916e3ea567a8b1b36101fd8944551acc50eb8574f926aed72ede7992deb4f2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.5 Results | 5.2 | CH5-5.2-H7-V1-P0274 | `outputs/tables/superseded_v2_0_2/hypothesis_grid_results.csv` | EXP-0004b | `9f916e3ea567a8b1b36101fd8944551acc50eb8574f926aed72ede7992deb4f2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.5 Results | 5.2 | CH5-5.2-GRID-V2 | `outputs/tables/hypothesis_grid_results_v2.csv` | EXP-0008a | `a5486cd345cf60c070805c05a672be0213491fe22e263158edaf5e3452601874` | v2 | VERIFIED |
| Ch.5 Results | 5.3 | CH5-5.3-PLACEBO | `outputs/tables/placebo_distribution_expanded.csv` | EXP-0008e | `5312f69eadc38d0f119891f35793b66578e16470b71ad44ca9d55ee0bf31df88` | v2 | VERIFIED |
| Ch.5 Results | 5.3 | CH5-5.3-PLACEBO-OUTCOME | `outputs/tables/placebo_outcome_test.csv` | EXP-0008d | `2525a890c6c7214895ff3d325d8eb3d6f91294ba131e7c4cdc2c33218a32a2fb` | v2 | VERIFIED |
| Ch.5 Results | 5.3 | CH5-5.3-REGIME | `outputs/tables/regime_split_results.csv` | EXP-0004d | `80df7d0c63e0e743256f65609fb461ffde0c825774e2eccf426ad4ece9391d23` | v2 | VERIFIED |
| Ch.5 Results | 5.4 | CH5-5.4-EVENT-V1 | `outputs/tables/superseded_v2_0_2/event_study_summary.csv` | EXP-0004e | `4b722ceb2d1cca6a04fd5e77b8752f84a086b00a957c1b7b564f23c87c064379` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.5 Results | 5.4 | CH5-5.4-EVENT-V2 | `outputs/tables/event_study_upgraded.csv` | EXP-0011e | `20bec51006905e72336c88244142a1a32954496109d9eac9b5c65049221e6d7f` | v2 | VERIFIED |
| Ch.5 Results | 5.4 | CH5-5.4-EVENT-CLUSTER | `outputs/tables/event_study_clustered_inference.csv` | EXP-0011e | `fe6576162c661401af1f92669013d73976c530eae36f71037808250dff29bb3e` | v2 | VERIFIED |
| Ch.5 Results | 5.5 | CH5-5.5-ROBUST | `outputs/tables/robustness_headline_survival.csv` | EXP-0005a | `3655ce3f2b9d57a8791c2a4d540f2223acb60476041a82e37a5d9890866f233c` | v2 | VERIFIED |
| Ch.5 Results | 5.6.1 | CH5-5.6.1-RW | `outputs/tables/hypothesis_grid_results_rw.csv` | EXP-0008b | `6f1b23112e4de9f8b19c6f325a671849c9872dbf3c3a8472a68f1e8c575e6798` | v2 | VERIFIED |
| Ch.5 Results | 5.6.2 | CH5-5.6.2-WB | `outputs/tables/wild_cluster_bootstrap.csv` | EXP-0009c | `484912f6fbb6246f4fd12ccc546806ead8d24beb52903ad62e922bbb0e909cf4` | v2 | VERIFIED |
| Ch.5 Results | 5.6.2 | CH5-5.6.2-SE | `outputs/tables/se_concordance.csv` | EXP-0009d | `8f326f6dd4d632436cad1a24fffb2daece124b54b0cf508c0541a74d215c293c` | v2 | VERIFIED |
| Ch.5 Results | 5.6.3 | CH5-5.6.3-LIQ | `outputs/tables/headline_with_liquidity_controls.csv` | EXP-0009b | `567484655604d8765f45b07ce399522ef8724aeda74d6efab37838ad6bf93e6f` | v2 | VERIFIED |
| Ch.5 Results | 5.6.4 | CH5-5.6.4-EGARCH | `outputs/tables/headline_with_egarch_outcome.csv` | EXP-0010a | `c6d85276db4312465cbf3cef6c7a35a6c4b5f2df7f74d6ec966f80d267531662` | v2 | VERIFIED |
| Ch.5 Results | 5.6.5 | CH5-5.6.5-QUANTILE | `outputs/tables/quantile_tail_summary.csv` | EXP-0010b | `76f0a72db971329107154a0b80ccda744fca76525174eea55d8cfe3670a4041a` | v2 | VERIFIED |
| Ch.5 Results | 5.6.6 | CH5-5.6.6-TRADESIZE | `outputs/tables/trade_size_heterogeneity.csv` | EXP-0010c | `7aab1e6f9d3d653e615b99c82c53456d7b910d11f0776521878bab82272dbc6d` | v2 | VERIFIED |
| Ch.5 Results | 5.6.7 | CH5-5.6.7-SPEC | `outputs/tables/specification_curve_h7_summary.csv` | EXP-0011b | `21278bf268fb7267ef4b24c8941025035cfa05f990c3090f35f2f4448d057aca` | v2 | VERIFIED |
| Ch.5 Results | 5.6.8 | CH5-5.6.8-SUBGROUP | `outputs/tables/heterogeneity_subgroups.csv` | EXP-0011d | `0fa128b827c8287fe0a4a5da15ea4d6b533547dd8f53d2ee3cc616b038d0999d` | v2 | VERIFIED |
| Ch.5 Results | 5.6.9 | CH5-5.6.9-COST | `outputs/tables/economic_magnitude.csv` | EXP-0011f | `2390fa2fa83bf689838f904b05b3e325cf7ca06ee784abc91df41863264a4a70` | v2 | VERIFIED |
| Ch.5 Results | 5.7 | CH5-5.7-FINAL | `outputs/tables/v2_final_headline_set.csv` | EXP-0012 | `049b83315d07a84fa6df9433dc9d1470ae23854c993b751344529d0faf3a53cd` | v2 | VERIFIED |
| Ch.6 Discussion | 6.1 | CH6-6.1-NEGATIVE | `outputs/tables/v2_final_headline_set.csv` | EXP-0012 | `049b83315d07a84fa6df9433dc9d1470ae23854c993b751344529d0faf3a53cd` | v2 | VERIFIED |
| Ch.6 Discussion | 6.1 | CH6-6.1-EXPLORATORY | `reports/exploratory_findings.md` | EXP-0008a | `d0690f5068563af238f5c2e8daacd72deb3dc047fd3951b67d1d9384672a10ae` | v2 | VERIFIED |
| Ch.6 Discussion | 6.2 | CH6-6.2-LIMITS | `reports/limitations.md` | EXP-0012 | `8793f4a70c491b27bf120c90970500c903eaa5e5ce46a1b102b6298b344be280` | v2 | VERIFIED |
| Ch.6 Discussion | 6.2 | CH6-6.2-PLAN | `docs/analysis_plan.md` | EXP-0004b | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.6 Discussion | 6.3 | CH6-6.3-LIMITS | `reports/limitations.md` | EXP-0012 | `8793f4a70c491b27bf120c90970500c903eaa5e5ce46a1b102b6298b344be280` | v2 | VERIFIED |
| Ch.6 Discussion | 6.4 | CH6-6.4-PANEL | `outputs/tables/broker_panel_summary.csv` | EXP-0011c | `ca510a6989d776760340b50444cb6ac9c9e17836709f86ed20f16f3144b409e2` | v2 | VERIFIED |
| Ch.6 Discussion | 6.4 | CH6-6.4-CORE | `outputs/tables/broker_core_transitions.csv` | EXP-0011c | `1f800f073e814caf6dc159bef84e8057ce74a8d75172992ddb85ef8ee773462a` | v2 | VERIFIED |
| Ch.6 Discussion | 6.4 | CH6-6.4-PERSIST | `outputs/tables/broker_top50_persistence.csv` | EXP-0011c | `ad99f03d4effd3716bf684b30c5d99372356adae5e33b08f65db42718917b27b` | v2 | VERIFIED |
| Ch.6 Discussion | 6.4 | CH6-6.4-PHD | `reports/broker_pilot_phd_seed.md` | EXP-0011c | `a562a8864cd31eab5b4ae0bc4485e3d567dd362ce7db72be3b9877838dadf21d` | v2 | VERIFIED |
| Ch.6 Discussion | 6.5 | CH6-6.5-COST | `outputs/tables/economic_magnitude.csv` | EXP-0011f | `2390fa2fa83bf689838f904b05b3e325cf7ca06ee784abc91df41863264a4a70` | v2 | VERIFIED |
| Ch.6 Discussion | 6.5 | CH6-6.5-REPRO | `docs/reproducibility.md` | EXP-0013 | `ff024c17ab86e46fae89dffcc13407c454b882cfefc18ea6b7f25372cf69c541` | v2 | VERIFIED |

**Counts.** 67 claims across 6 chapters; 50 distinct artefacts.
