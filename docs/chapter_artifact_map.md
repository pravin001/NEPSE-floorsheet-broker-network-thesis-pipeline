# Chapter → artefact crosswalk (v2.0.1 handoff)

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
| Ch.1 Introduction | 1.1 | CH1-1.1-SCOPE | `README.md` | EXP-0002b,EXP-0012 | `c96c6950f9e07b24c85c893b64a2672063b5ed507d999db3e0cdd9ec35ffbe29` | v2 | VERIFIED |
| Ch.1 Introduction | 1.1 | CH1-1.1-LIMITS | `reports/limitations.md` | EXP-0012 | `be91dad74c29639361c04f7e4c7e18890e1f420af7f14a6f18f13765ff18ea7d` | v2 | VERIFIED |
| Ch.1 Introduction | 1.2 | CH1-1.2-HYPOTHESES | `docs/analysis_plan.md` | EXP-0004b | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.1 Introduction | 1.3 | CH1-1.3-HEADLINE | `outputs/tables/v2_final_headline_set.csv` | EXP-0012 | `228c4ec82da451ab4b139031bc6de299d49d302c736d12fe9429b6110051e00f` | v2 | VERIFIED |
| Ch.1 Introduction | 1.4 | CH1-1.4-COST | `outputs/tables/economic_magnitude.csv` | EXP-0011f | `e1b7a0ff230198f8284a932b95a8a65dc9a7339cd31a392c1771f605b0df33f2` | v2 | VERIFIED |
| Ch.1 Introduction | 1.5 | CH1-1.5-CONTRIBUTION | `reports/economic_magnitude_analysis.md` | EXP-0011f | `f185dfa07fdddd9fd076031a1dd83848b57ce056718994b6e295d46640ec396f` | v2 | VERIFIED |
| Ch.2 Literature | 2.1 | CH2-2.1-MATRIX | `reports/chapter_assets/ch2_literature_matrix.csv` | EXP-0014 | `f1287a5c1347bd196ab70b13b9237e7154b84f86342c41bcdb75f1afe5dbd0c6` | v2 | SCAFFOLD |
| Ch.2 Literature | 2.2 | CH2-2.2-GAP | `reports/chapter_assets/ch2_research_gap.md` | EXP-0014 | `8b25e3999a845f74a074a669f8c48de69159425bba566195311c3b2718f02f20` | v2 | SCAFFOLD |
| Ch.2 Literature | 2.3 | CH2-2.3-COMPARE | `reports/chapter_assets/ch2_comparison_table.csv` | EXP-0014 | `6f33ba765e746366852f7308b91a5d245a2ee36695f33f5446dc446b5e0e3f6a` | v2 | SCAFFOLD |
| Ch.2 Literature | 2.4 | CH2-2.4-HYPOMAP | `docs/analysis_plan.md` | EXP-0004b | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.2 Literature | 2.4 | CH2-2.4-FRONTIER | `reports/limitations.md` | EXP-0012 | `be91dad74c29639361c04f7e4c7e18890e1f420af7f14a6f18f13765ff18ea7d` | v2 | VERIFIED |
| Ch.3 Methodology | 3.1 | CH3-3.1-DESIGN | `docs/analysis_plan.md` | EXP-0004b | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.3 Methodology | 3.2 | CH3-3.2-PREDECL | `docs/analysis_plan_v2_extension.md` | EXP-0008a | `5599c5a33d3801cc28143716db40ea186d70dc8a1d8b02e8016b4aff5f9d9d98` | v2 | VERIFIED |
| Ch.3 Methodology | 3.2 | CH3-3.2-FREEZE | `configs/v2_freeze/freeze_manifest.csv` | EXP-0013 | `f610ba67af7737c5682b679556d42004c4e8676cdb263977ec2c647058103acd` | v2 | VERIFIED |
| Ch.3 Methodology | 3.3 | CH3-3.3-WALKFORWARD | `reports/chapter_assets/ch3_walk_forward_diagram.md` | EXP-0004a | `2ed6714d79191de32f57490c323ea80cd637504b439ef64c6985a4a4636ae1a9` | v2 | SCAFFOLD |
| Ch.3 Methodology | 3.3 | CH3-3.3-WALKFORWARD-PLAN | `docs/analysis_plan.md` | EXP-0004a | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.3 Methodology | 3.4 | CH3-3.4-FEATURES | `reports/chapter_assets/ch3_feature_dictionary.csv` | EXP-0003a | `2105c90c0947ec0371640d775704fe404ab2ccfbc3dfb9b85fdeebd3c51a01fe` | v2 | SCAFFOLD |
| Ch.3 Methodology | 3.5 | CH3-3.5-ESTIMATION | `docs/analysis_plan.md` | EXP-0004b | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.3 Methodology | 3.6 | CH3-3.6-ROBUSTNESS | `docs/analysis_plan.md` | EXP-0005a | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.3 Methodology | 3.6 | CH3-3.6-EVENT | `docs/analysis_plan.md` | EXP-0004e | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.1 | CH4-4.1-PIPELINE | `reports/chapter_assets/ch4_pipeline_diagram.md` | EXP-0013 | `b043e3a066aee065c07c56f2b408505d3deeba3832b51e5279d0f7348428093f` | v2 | SCAFFOLD |
| Ch.4 Data Engineering | 4.1 | CH4-4.1-DRIVER | `scripts/run_stage6_rebuild.py` | EXP-0013 | `01748ac61512065392375bdf441fe7ccb507d18b1c4430cdc17c9cd71f562a3a` | v2 | VERIFIED |
| Ch.4 Data Engineering | 4.2 | CH4-4.2-PROVENANCE | `data/metadata/corpus_files_sha256.csv` | EXP-0002b | `e78df58d539b59e4e8e8636437a8870ffb3a727a9095c7c00d9e0931cffbedac` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.2 | CH4-4.2-LICENCE | `docs/ai_use_policy.md` | EXP-0002d | `86497cdbcb5b6e87bb2356fb8cbf1faaf00451da62313449534fbb22c8c35c13` | v2 | VERIFIED |
| Ch.4 Data Engineering | 4.3 | CH4-4.3-CORPUS-AUDIT | `notebooks/01_data_quality_audit.ipynb` | EXP-0002f | `4fb7abe2b9aa2a176e00a58c5cb043e6236629a558e00e4ccc068e864165bb56` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.3 | CH4-4.3-DUP | `outputs/tables/corpus_duplicate_keys.csv` | EXP-0002c | `398b0c6d0da268675ea9c9878aeb1f6f97a330c1c39d8f90300c5903859336a5` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.3 | CH4-4.3-MISSING | `outputs/tables/corpus_missing_broker_ids.csv` | EXP-0002c | `c1232f5686922124230152fa9a2a0918725fef19ef1bc392391ac41e99f5e586` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.3 | CH4-4.3-COVERAGE | `outputs/tables/corpus_symbol_coverage.csv` | EXP-0002c | `3e758f6ff81deab875fa54ce7776a27e640f817388abad2c8a89a476b6c35faa` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.3 | CH4-4.3-DAILY | `outputs/tables/corpus_daily_summary.csv` | EXP-0002c | `f79e328ea33a57fc065f4a8bcd09d1bcdd10026593b5e770d0125d5f0c84b67d` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.4 | CH4-4.4-VOLUME | `outputs/tables/volume_reconciliation.csv` | EXP-0002e | `e4246fef017e7d28a2481357ee5b1f683879fb3f6c7d8c35a0f1d5920372ee0c` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.5 | CH4-4.5-UNIVERSE | `outputs/tables/universe_selected_top10.csv` | EXP-0002a | `5f1ff249050a72a9c1cd23575d47163fbce9a64ec66812dd9c033a8a8b06b21a` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.5 | CH4-4.5-EXCLUSIONS | `outputs/tables/universe_exclusions.csv` | EXP-0002a | `ac547acc53717642273edba603dc47d8f68b1c973fe3a0d16290706a7365f6fc` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.4 Data Engineering | 4.6 | CH4-4.6-DRIFT | `outputs/tables/v2_clean_rebuild_audit.csv` | EXP-0013 | `e7c913a8c8401a55bde3c7fe31f71667e9a4047b40f6ee9165f5208b6d6d2ef2` | v2 | VERIFIED |
| Ch.4 Data Engineering | 4.6 | CH4-4.6-REPRO | `docs/reproducibility.md` | EXP-0013 | `8dca719606f3ce1c136d2a7b28bdc48107fe07e70b1ae441b5e2817fe8b38acb` | v2 | VERIFIED |
| Ch.5 Results | 5.1 | CH5-5.1-SAMPLE | `outputs/tables/hypothesis_grid_results_v2.csv` | EXP-0011a | `e8d0e050d6e55f9a72238892d600e4aa7675d8a8bbe06a3d8ef0d2adc88547f3` | v2 | VERIFIED |
| Ch.5 Results | 5.2 | CH5-5.2-GRID-V1 | `outputs/tables/hypothesis_grid_results.csv` | EXP-0004b | `9f916e3ea567a8b1b36101fd8944551acc50eb8574f926aed72ede7992deb4f2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.5 Results | 5.2 | CH5-5.2-H7-V1-P0274 | `outputs/tables/hypothesis_grid_results.csv` | EXP-0004b | `9f916e3ea567a8b1b36101fd8944551acc50eb8574f926aed72ede7992deb4f2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.5 Results | 5.2 | CH5-5.2-GRID-V2 | `outputs/tables/hypothesis_grid_results_v2.csv` | EXP-0008a | `e8d0e050d6e55f9a72238892d600e4aa7675d8a8bbe06a3d8ef0d2adc88547f3` | v2 | VERIFIED |
| Ch.5 Results | 5.3 | CH5-5.3-PLACEBO | `outputs/tables/placebo_distribution_expanded.csv` | EXP-0008e | `07f2f4e2ec62f2b90db7d3d3e8a5501750eb944f29589a12564e2b09baf46a23` | v2 | VERIFIED |
| Ch.5 Results | 5.3 | CH5-5.3-PLACEBO-OUTCOME | `outputs/tables/placebo_outcome_test.csv` | EXP-0008d | `1081142a33f5b5a74776bb2f30b369777d5faec09875a6d02524bc0883c3ffb7` | v2 | VERIFIED |
| Ch.5 Results | 5.3 | CH5-5.3-REGIME | `outputs/tables/regime_split_results.csv` | EXP-0004d | `c59d96655b0b87ff9bf795aea1890024ff74aec0a851d0d25dedaf6114120979` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.5 Results | 5.4 | CH5-5.4-EVENT-V1 | `outputs/tables/event_study_summary.csv` | EXP-0004e | `4b722ceb2d1cca6a04fd5e77b8752f84a086b00a957c1b7b564f23c87c064379` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.5 Results | 5.4 | CH5-5.4-EVENT-V2 | `outputs/tables/event_study_upgraded.csv` | EXP-0011e | `4ccc8059f1544afd1d9a6f54f8287e7c086afc1222c46430b95daa0b24d4c4a8` | v2 | VERIFIED |
| Ch.5 Results | 5.4 | CH5-5.4-EVENT-CLUSTER | `outputs/tables/event_study_clustered_inference.csv` | EXP-0011e | `b3e0ffafd355096ee8a6ed446a392ac7f8195c352fc248ddc4e44ea486d61f29` | v2 | VERIFIED |
| Ch.5 Results | 5.5 | CH5-5.5-ROBUST | `outputs/tables/robustness_headline_survival.csv` | EXP-0005a | `82f3cc4d92b474f6f6ec5a8f51c67de47ab56f8ba3e282d27d98fb7c20b408e8` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.5 Results | 5.6.1 | CH5-5.6.1-RW | `outputs/tables/hypothesis_grid_results_rw.csv` | EXP-0008b | `e1ad375faf236808eaaf89267f3fc610118e1e668c4d474d68e39897b55f3835` | v2 | VERIFIED |
| Ch.5 Results | 5.6.2 | CH5-5.6.2-WB | `outputs/tables/wild_cluster_bootstrap.csv` | EXP-0009c | `6f15ccdc3960f469c81c624d450016ad0574450cf7e929f40114c675cc616449` | v2 | VERIFIED |
| Ch.5 Results | 5.6.2 | CH5-5.6.2-SE | `outputs/tables/se_concordance.csv` | EXP-0009d | `ec644015411880a608310a4f65ff65e96592965da96f0dac295ac120d1a2d67a` | v2 | VERIFIED |
| Ch.5 Results | 5.6.3 | CH5-5.6.3-LIQ | `outputs/tables/headline_with_liquidity_controls.csv` | EXP-0009b | `5511697348cd92b510e06ebad44bae89409e65b2e656fece971fdb9330061909` | v2 | VERIFIED |
| Ch.5 Results | 5.6.4 | CH5-5.6.4-EGARCH | `outputs/tables/headline_with_egarch_outcome.csv` | EXP-0010a | `1847d5a091cb28b6ff02b0ee0a8437c4161b4476661b9536ea0aee32844b7a1d` | v2 | VERIFIED |
| Ch.5 Results | 5.6.5 | CH5-5.6.5-QUANTILE | `outputs/tables/quantile_tail_summary.csv` | EXP-0010b | `bd2a3dca9a400b221692ecff1edb59723ac0be198389d7e3b2c8322057d36444` | v2 | VERIFIED |
| Ch.5 Results | 5.6.6 | CH5-5.6.6-TRADESIZE | `outputs/tables/trade_size_heterogeneity.csv` | EXP-0010c | `7aab1e6f9d3d653e615b99c82c53456d7b910d11f0776521878bab82272dbc6d` | v2 | VERIFIED |
| Ch.5 Results | 5.6.7 | CH5-5.6.7-SPEC | `outputs/tables/specification_curve_h7_summary.csv` | EXP-0011b | `21278bf268fb7267ef4b24c8941025035cfa05f990c3090f35f2f4448d057aca` | v2 | VERIFIED |
| Ch.5 Results | 5.6.8 | CH5-5.6.8-SUBGROUP | `outputs/tables/heterogeneity_subgroups.csv` | EXP-0011d | `5d910a0ea9a382f8df335770768ca30a40fbf42b76e525707f026108cd6dc2d3` | v2 | VERIFIED |
| Ch.5 Results | 5.6.9 | CH5-5.6.9-COST | `outputs/tables/economic_magnitude.csv` | EXP-0011f | `e1b7a0ff230198f8284a932b95a8a65dc9a7339cd31a392c1771f605b0df33f2` | v2 | VERIFIED |
| Ch.5 Results | 5.7 | CH5-5.7-FINAL | `outputs/tables/v2_final_headline_set.csv` | EXP-0012 | `228c4ec82da451ab4b139031bc6de299d49d302c736d12fe9429b6110051e00f` | v2 | VERIFIED |
| Ch.6 Discussion | 6.1 | CH6-6.1-NEGATIVE | `outputs/tables/v2_final_headline_set.csv` | EXP-0012 | `228c4ec82da451ab4b139031bc6de299d49d302c736d12fe9429b6110051e00f` | v2 | VERIFIED |
| Ch.6 Discussion | 6.1 | CH6-6.1-EXPLORATORY | `reports/exploratory_findings.md` | EXP-0008a | `5a9b1f6590f1be7857df958c9ad9c23ffacd63e02c2b27085a20e3e566d91705` | v2 | VERIFIED |
| Ch.6 Discussion | 6.2 | CH6-6.2-LIMITS | `reports/limitations.md` | EXP-0012 | `be91dad74c29639361c04f7e4c7e18890e1f420af7f14a6f18f13765ff18ea7d` | v2 | VERIFIED |
| Ch.6 Discussion | 6.2 | CH6-6.2-PLAN | `docs/analysis_plan.md` | EXP-0004b | `7d29da6b49393eddca828db0ab21c130ed27f892a23f0e4c6609be8e1ffdead2` | v1 | VERIFIED_V1_IMMUTABLE |
| Ch.6 Discussion | 6.3 | CH6-6.3-LIMITS | `reports/limitations.md` | EXP-0012 | `be91dad74c29639361c04f7e4c7e18890e1f420af7f14a6f18f13765ff18ea7d` | v2 | VERIFIED |
| Ch.6 Discussion | 6.4 | CH6-6.4-PANEL | `outputs/tables/broker_panel_summary.csv` | EXP-0011c | `ca510a6989d776760340b50444cb6ac9c9e17836709f86ed20f16f3144b409e2` | v2 | VERIFIED |
| Ch.6 Discussion | 6.4 | CH6-6.4-CORE | `outputs/tables/broker_core_transitions.csv` | EXP-0011c | `1f800f073e814caf6dc159bef84e8057ce74a8d75172992ddb85ef8ee773462a` | v2 | VERIFIED |
| Ch.6 Discussion | 6.4 | CH6-6.4-PERSIST | `outputs/tables/broker_top50_persistence.csv` | EXP-0011c | `ad99f03d4effd3716bf684b30c5d99372356adae5e33b08f65db42718917b27b` | v2 | VERIFIED |
| Ch.6 Discussion | 6.4 | CH6-6.4-PHD | `reports/broker_pilot_phd_seed.md` | EXP-0011c | `7acc02a7a7dc164f4e7d40e001816298436887641be8f1ab4d82a134bc62a0c1` | v2 | VERIFIED |
| Ch.6 Discussion | 6.5 | CH6-6.5-COST | `outputs/tables/economic_magnitude.csv` | EXP-0011f | `e1b7a0ff230198f8284a932b95a8a65dc9a7339cd31a392c1771f605b0df33f2` | v2 | VERIFIED |
| Ch.6 Discussion | 6.5 | CH6-6.5-REPRO | `docs/reproducibility.md` | EXP-0013 | `8dca719606f3ce1c136d2a7b28bdc48107fe07e70b1ae441b5e2817fe8b38acb` | v2 | VERIFIED |

**Counts.** 67 claims across 6 chapters; 50 distinct artefacts.
