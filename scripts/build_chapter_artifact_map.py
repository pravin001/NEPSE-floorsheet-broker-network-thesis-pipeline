"""Build the verified chapter -> artefact crosswalk (v2.0.1 handoff).

The Stage-5 `docs/chapter_artifact_map.md` named six conceptual v1 files that
were never produced.  This builder replaces it with a crosswalk whose every path
is resolved, SHA-256 hashed, and later audited by `scripts/audit_chapter_map.py`.

`claim_version` is deliberate:

* ``v1`` = the claim/table is a frozen v1 result or v1 pre-declaration.  v1
  numbers remain citable even when v2 reclassifies the hypothesis.
* ``v2`` = the claim is a v2 governance/robustness result, or a post-freeze
  handoff scaffold with no numeric claim (``status = SCAFFOLD``).

The builder also writes one machine-readable asset manifest per chapter pack
(Ch.1-Ch.4).  It performs no manifest writes; use
`scripts/append_chapter_handoff_hashes.py` after it.

Usage:
    nepse-msc/bin/python scripts/build_chapter_artifact_map.py
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "docs" / "chapter_artifact_map.md"
ASSETS = ROOT / "reports" / "chapter_assets"

# chapter, section, claim_id, artifact_path, exp_id, claim_version, status
CLAIMS = [
    # Ch.1 Introduction
    ("Ch.1 Introduction", "1.1", "CH1-1.1-SCOPE", "README.md",
     "EXP-0002b,EXP-0012", "v2", "VERIFIED"),
    ("Ch.1 Introduction", "1.1", "CH1-1.1-LIMITS", "reports/limitations.md",
     "EXP-0012", "v2", "VERIFIED"),
    ("Ch.1 Introduction", "1.2", "CH1-1.2-HYPOTHESES", "docs/analysis_plan.md",
     "EXP-0004b", "v1", "VERIFIED_V1_IMMUTABLE"),
    ("Ch.1 Introduction", "1.3", "CH1-1.3-HEADLINE",
     "outputs/tables/v2_final_headline_set.csv", "EXP-0012", "v2", "VERIFIED"),
    ("Ch.1 Introduction", "1.4", "CH1-1.4-COST",
     "outputs/tables/economic_magnitude.csv", "EXP-0011f", "v2", "VERIFIED"),
    ("Ch.1 Introduction", "1.5", "CH1-1.5-CONTRIBUTION",
     "reports/economic_magnitude_analysis.md", "EXP-0011f", "v2", "VERIFIED"),

    # Ch.2 Literature
    ("Ch.2 Literature", "2.1", "CH2-2.1-MATRIX",
     "reports/chapter_assets/ch2_literature_matrix.csv", "EXP-0014", "v2",
     "SCAFFOLD"),
    ("Ch.2 Literature", "2.2", "CH2-2.2-GAP",
     "reports/chapter_assets/ch2_research_gap.md", "EXP-0014", "v2",
     "SCAFFOLD"),
    ("Ch.2 Literature", "2.3", "CH2-2.3-COMPARE",
     "reports/chapter_assets/ch2_comparison_table.csv", "EXP-0014", "v2",
     "SCAFFOLD"),
    ("Ch.2 Literature", "2.4", "CH2-2.4-HYPOMAP", "docs/analysis_plan.md",
     "EXP-0004b", "v1", "VERIFIED_V1_IMMUTABLE"),
    ("Ch.2 Literature", "2.4", "CH2-2.4-FRONTIER", "reports/limitations.md",
     "EXP-0012", "v2", "VERIFIED"),

    # Ch.3 Methodology
    ("Ch.3 Methodology", "3.1", "CH3-3.1-DESIGN", "docs/analysis_plan.md",
     "EXP-0004b", "v1", "VERIFIED_V1_IMMUTABLE"),
    ("Ch.3 Methodology", "3.2", "CH3-3.2-PREDECL",
     "docs/analysis_plan_v2_extension.md", "EXP-0008a", "v2", "VERIFIED"),
    ("Ch.3 Methodology", "3.2", "CH3-3.2-FREEZE",
     "configs/v2_freeze/freeze_manifest.csv", "EXP-0013", "v2", "VERIFIED"),
    ("Ch.3 Methodology", "3.3", "CH3-3.3-WALKFORWARD",
     "reports/chapter_assets/ch3_walk_forward_diagram.md", "EXP-0004a", "v2",
     "SCAFFOLD"),
    ("Ch.3 Methodology", "3.3", "CH3-3.3-WALKFORWARD-PLAN",
     "docs/analysis_plan.md", "EXP-0004a", "v1", "VERIFIED_V1_IMMUTABLE"),
    ("Ch.3 Methodology", "3.4", "CH3-3.4-FEATURES",
     "reports/chapter_assets/ch3_feature_dictionary.csv", "EXP-0003a", "v2",
     "SCAFFOLD"),
    ("Ch.3 Methodology", "3.5", "CH3-3.5-ESTIMATION", "docs/analysis_plan.md",
     "EXP-0004b", "v1", "VERIFIED_V1_IMMUTABLE"),
    ("Ch.3 Methodology", "3.6", "CH3-3.6-ROBUSTNESS", "docs/analysis_plan.md",
     "EXP-0005a", "v1", "VERIFIED_V1_IMMUTABLE"),
    ("Ch.3 Methodology", "3.6", "CH3-3.6-EVENT", "docs/analysis_plan.md",
     "EXP-0004e", "v1", "VERIFIED_V1_IMMUTABLE"),

    # Ch.4 Data engineering
    ("Ch.4 Data Engineering", "4.1", "CH4-4.1-PIPELINE",
     "reports/chapter_assets/ch4_pipeline_diagram.md", "EXP-0013", "v2",
     "SCAFFOLD"),
    ("Ch.4 Data Engineering", "4.1", "CH4-4.1-DRIVER",
     "scripts/run_stage6_rebuild.py", "EXP-0013", "v2", "VERIFIED"),
    ("Ch.4 Data Engineering", "4.2", "CH4-4.2-PROVENANCE",
     "data/metadata/corpus_files_sha256.csv", "EXP-0002b", "v1",
     "VERIFIED_V1_IMMUTABLE"),
    # Rewritten in the v2.0.2 pre-write sprint (Phase D); the v1 hash is
    # recorded in git history and in the provenance manifest, but the live
    # licence register is a v2 governance artefact.
    ("Ch.4 Data Engineering", "4.2", "CH4-4.2-LICENCE",
     "docs/ai_use_policy.md", "EXP-0002d", "v2", "VERIFIED"),
    ("Ch.4 Data Engineering", "4.3", "CH4-4.3-CORPUS-AUDIT",
     "notebooks/01_data_quality_audit.ipynb", "EXP-0002f", "v1",
     "VERIFIED_V1_IMMUTABLE"),
    ("Ch.4 Data Engineering", "4.3", "CH4-4.3-DUP",
     "outputs/tables/corpus_duplicate_keys.csv", "EXP-0002c", "v1",
     "VERIFIED_V1_IMMUTABLE"),
    ("Ch.4 Data Engineering", "4.3", "CH4-4.3-MISSING",
     "outputs/tables/corpus_missing_broker_ids.csv", "EXP-0002c", "v1",
     "VERIFIED_V1_IMMUTABLE"),
    ("Ch.4 Data Engineering", "4.3", "CH4-4.3-COVERAGE",
     "outputs/tables/corpus_symbol_coverage.csv", "EXP-0002c", "v1",
     "VERIFIED_V1_IMMUTABLE"),
    ("Ch.4 Data Engineering", "4.3", "CH4-4.3-DAILY",
     "outputs/tables/corpus_daily_summary.csv", "EXP-0002c", "v1",
     "VERIFIED_V1_IMMUTABLE"),
    ("Ch.4 Data Engineering", "4.4", "CH4-4.4-VOLUME",
     "outputs/tables/volume_reconciliation.csv", "EXP-0002e", "v1",
     "VERIFIED_V1_IMMUTABLE"),
    ("Ch.4 Data Engineering", "4.5", "CH4-4.5-UNIVERSE",
     "outputs/tables/universe_selected_top10.csv", "EXP-0002a", "v1",
     "VERIFIED_V1_IMMUTABLE"),
    ("Ch.4 Data Engineering", "4.5", "CH4-4.5-EXCLUSIONS",
     "outputs/tables/universe_exclusions.csv", "EXP-0002a", "v1",
     "VERIFIED_V1_IMMUTABLE"),
    ("Ch.4 Data Engineering", "4.6", "CH4-4.6-DRIFT",
     "outputs/tables/v2_clean_rebuild_audit.csv", "EXP-0013", "v2", "VERIFIED"),
    ("Ch.4 Data Engineering", "4.6", "CH4-4.6-REPRO",
     "docs/reproducibility.md", "EXP-0013", "v2", "VERIFIED"),

    # Ch.5 Results
    ("Ch.5 Results", "5.1", "CH5-5.1-SAMPLE",
     "outputs/tables/hypothesis_grid_results_v2.csv", "EXP-0011a", "v2",
     "VERIFIED"),
    # v2.1.0: the live grid is regenerated with the corrected reciprocity
    # feature, so it is no longer a byte-frozen v1 artifact.  The v1 claims
    # point at the preserved byte-for-byte v2.0.2 snapshot instead.
    ("Ch.5 Results", "5.2", "CH5-5.2-GRID-V1",
     "outputs/tables/superseded_v2_0_2/hypothesis_grid_results.csv",
     "EXP-0004b", "v1", "VERIFIED_V1_IMMUTABLE"),
    ("Ch.5 Results", "5.2", "CH5-5.2-H7-V1-P0274",
     "outputs/tables/superseded_v2_0_2/hypothesis_grid_results.csv",
     "EXP-0004b", "v1", "VERIFIED_V1_IMMUTABLE"),
    ("Ch.5 Results", "5.2", "CH5-5.2-GRID-V2",
     "outputs/tables/hypothesis_grid_results_v2.csv", "EXP-0008a", "v2",
     "VERIFIED"),
    ("Ch.5 Results", "5.3", "CH5-5.3-PLACEBO",
     "outputs/tables/placebo_distribution_expanded.csv", "EXP-0008e", "v2",
     "VERIFIED"),
    ("Ch.5 Results", "5.3", "CH5-5.3-PLACEBO-OUTCOME",
     "outputs/tables/placebo_outcome_test.csv", "EXP-0008d", "v2", "VERIFIED"),
    ("Ch.5 Results", "5.3", "CH5-5.3-REGIME",
     "outputs/tables/regime_split_results.csv", "EXP-0004d", "v2", "VERIFIED"),
    ("Ch.5 Results", "5.4", "CH5-5.4-EVENT-V1",
     "outputs/tables/superseded_v2_0_2/event_study_summary.csv",
     "EXP-0004e", "v1", "VERIFIED_V1_IMMUTABLE"),
    ("Ch.5 Results", "5.4", "CH5-5.4-EVENT-V2",
     "outputs/tables/event_study_upgraded.csv", "EXP-0011e", "v2", "VERIFIED"),
    ("Ch.5 Results", "5.4", "CH5-5.4-EVENT-CLUSTER",
     "outputs/tables/event_study_clustered_inference.csv", "EXP-0011e", "v2",
     "VERIFIED"),
    ("Ch.5 Results", "5.5", "CH5-5.5-ROBUST",
     "outputs/tables/robustness_headline_survival.csv", "EXP-0005a", "v2",
     "VERIFIED"),
    ("Ch.5 Results", "5.6.1", "CH5-5.6.1-RW",
     "outputs/tables/hypothesis_grid_results_rw.csv", "EXP-0008b", "v2",
     "VERIFIED"),
    ("Ch.5 Results", "5.6.2", "CH5-5.6.2-WB",
     "outputs/tables/wild_cluster_bootstrap.csv", "EXP-0009c", "v2",
     "VERIFIED"),
    ("Ch.5 Results", "5.6.2", "CH5-5.6.2-SE",
     "outputs/tables/se_concordance.csv", "EXP-0009d", "v2", "VERIFIED"),
    ("Ch.5 Results", "5.6.3", "CH5-5.6.3-LIQ",
     "outputs/tables/headline_with_liquidity_controls.csv", "EXP-0009b", "v2",
     "VERIFIED"),
    ("Ch.5 Results", "5.6.4", "CH5-5.6.4-EGARCH",
     "outputs/tables/headline_with_egarch_outcome.csv", "EXP-0010a", "v2",
     "VERIFIED"),
    ("Ch.5 Results", "5.6.5", "CH5-5.6.5-QUANTILE",
     "outputs/tables/quantile_tail_summary.csv", "EXP-0010b", "v2",
     "VERIFIED"),
    ("Ch.5 Results", "5.6.6", "CH5-5.6.6-TRADESIZE",
     "outputs/tables/trade_size_heterogeneity.csv", "EXP-0010c", "v2",
     "VERIFIED"),
    ("Ch.5 Results", "5.6.7", "CH5-5.6.7-SPEC",
     "outputs/tables/specification_curve_h7_summary.csv", "EXP-0011b", "v2",
     "VERIFIED"),
    ("Ch.5 Results", "5.6.8", "CH5-5.6.8-SUBGROUP",
     "outputs/tables/heterogeneity_subgroups.csv", "EXP-0011d", "v2",
     "VERIFIED"),
    ("Ch.5 Results", "5.6.9", "CH5-5.6.9-COST",
     "outputs/tables/economic_magnitude.csv", "EXP-0011f", "v2", "VERIFIED"),
    ("Ch.5 Results", "5.7", "CH5-5.7-FINAL",
     "outputs/tables/v2_final_headline_set.csv", "EXP-0012", "v2", "VERIFIED"),

    # Ch.6 Discussion
    ("Ch.6 Discussion", "6.1", "CH6-6.1-NEGATIVE",
     "outputs/tables/v2_final_headline_set.csv", "EXP-0012", "v2", "VERIFIED"),
    ("Ch.6 Discussion", "6.1", "CH6-6.1-EXPLORATORY",
     "reports/exploratory_findings.md", "EXP-0008a", "v2", "VERIFIED"),
    ("Ch.6 Discussion", "6.2", "CH6-6.2-LIMITS", "reports/limitations.md",
     "EXP-0012", "v2", "VERIFIED"),
    ("Ch.6 Discussion", "6.2", "CH6-6.2-PLAN", "docs/analysis_plan.md",
     "EXP-0004b", "v1", "VERIFIED_V1_IMMUTABLE"),
    ("Ch.6 Discussion", "6.3", "CH6-6.3-LIMITS", "reports/limitations.md",
     "EXP-0012", "v2", "VERIFIED"),
    ("Ch.6 Discussion", "6.4", "CH6-6.4-PANEL",
     "outputs/tables/broker_panel_summary.csv", "EXP-0011c", "v2", "VERIFIED"),
    ("Ch.6 Discussion", "6.4", "CH6-6.4-CORE",
     "outputs/tables/broker_core_transitions.csv", "EXP-0011c", "v2",
     "VERIFIED"),
    ("Ch.6 Discussion", "6.4", "CH6-6.4-PERSIST",
     "outputs/tables/broker_top50_persistence.csv", "EXP-0011c", "v2",
     "VERIFIED"),
    ("Ch.6 Discussion", "6.4", "CH6-6.4-PHD",
     "reports/broker_pilot_phd_seed.md", "EXP-0011c", "v2", "VERIFIED"),
    ("Ch.6 Discussion", "6.5", "CH6-6.5-COST",
     "outputs/tables/economic_magnitude.csv", "EXP-0011f", "v2", "VERIFIED"),
    ("Ch.6 Discussion", "6.5", "CH6-6.5-REPRO", "docs/reproducibility.md",
     "EXP-0013", "v2", "VERIFIED"),
]

# chapter pack -> (asset_id, path, role, exp_id, claim_version)
PACKS = {
    "ch1": [
        ("CH1-A1", "README.md", "scope + epistemic frame", "EXP-0002b,EXP-0012", "v2"),
        ("CH1-A2", "docs/analysis_plan.md", "pre-declared design", "EXP-0004b", "v1"),
        ("CH1-A3", "reports/limitations.md", "boundary conditions", "EXP-0012", "v2"),
        ("CH1-A4", "outputs/tables/v2_final_headline_set.csv", "canonical headline set", "EXP-0012", "v2"),
        ("CH1-A5", "outputs/tables/economic_magnitude.csv", "cost-benefit arithmetic", "EXP-0011f", "v2"),
        ("CH1-A6", "reports/economic_magnitude_analysis.md", "cost-floor rationale", "EXP-0011f", "v2"),
    ],
    "ch2": [
        ("CH2-A1", "reports/chapter_assets/ch2_literature_matrix.csv", "literature matrix scaffold", "EXP-0014", "v2"),
        ("CH2-A2", "reports/chapter_assets/ch2_research_gap.md", "research-gap scaffold", "EXP-0014", "v2"),
        ("CH2-A3", "reports/chapter_assets/ch2_comparison_table.csv", "comparison-table scaffold", "EXP-0014", "v2"),
        ("CH2-A4", "docs/analysis_plan.md", "hypothesis mapping", "EXP-0004b", "v1"),
        ("CH2-A5", "reports/limitations.md", "boundary conditions", "EXP-0012", "v2"),
    ],
    "ch3": [
        ("CH3-A1", "docs/analysis_plan.md", "v1 frozen design", "EXP-0004a,EXP-0004b", "v1"),
        ("CH3-A2", "docs/analysis_plan_v2_extension.md", "v2 pre-declaration", "EXP-0008a,EXP-0013", "v2"),
        ("CH3-A3", "configs/v2_freeze/freeze_manifest.csv", "binding-file hashes", "EXP-0013", "v2"),
        ("CH3-A4", "reports/chapter_assets/ch3_walk_forward_diagram.md", "Figure 3.1 scaffold", "EXP-0004a,EXP-0013", "v2"),
        ("CH3-A5", "reports/chapter_assets/ch3_feature_dictionary.csv", "Table 3.3 scaffold", "EXP-0003a,EXP-0009a", "v2"),
    ],
    "ch4": [
        ("CH4-A1", "scripts/run_stage6_rebuild.py", "21-step rebuild driver", "EXP-0013", "v2"),
        ("CH4-A2", "data/metadata/corpus_files_sha256.csv", "per-file provenance", "EXP-0002b", "v1"),
        ("CH4-A3", "docs/ai_use_policy.md", "licence register", "EXP-0002d", "v2"),
        ("CH4-A4", "notebooks/01_data_quality_audit.ipynb", "executable corpus audit", "EXP-0002f", "v1"),
        ("CH4-A5", "outputs/tables/volume_reconciliation.csv", "volume reconciliation", "EXP-0002e", "v1"),
        ("CH4-A6", "outputs/tables/v2_clean_rebuild_audit.csv", "drift evidence", "EXP-0013", "v2"),
        ("CH4-A7", "docs/reproducibility.md", "clean-rebuild record", "EXP-0013", "v2"),
        ("CH4-A8", "reports/chapter_assets/ch4_pipeline_diagram.md", "Figure 4.1 scaffold", "EXP-0013", "v2"),
    ],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def render_map() -> str:
    lines = [
        "# Chapter → artefact crosswalk (v2.1.0 handoff)",
        "",
        "**Version note.** v2.1.0 corrects the `reciprocity_volume` metric and",
        "rebuilds every downstream artifact. The v1 claims that used to point at",
        "the live `hypothesis_grid_results.csv` and `event_study_summary.csv` now",
        "point at the byte-frozen v2.0.2 copies in",
        "`outputs/tables/superseded_v2_0_2/`. Live results carry",
        "`claim_version = v2`. The correction record is",
        "`reports/reciprocity_correction.md`; the tag `v2.0.2-prewrite` is not",
        "moved.",
        "",
        "**Status.** Verified crosswalk replacing the Stage-5 placeholder map.",
        "Every row is audited by `scripts/audit_chapter_map.py`;",
        "`tests/test_chapter_map_integrity.py` fails the build if a path, hash,",
        "provenance-manifest row, or EXP key drifts.",
        "",
        "**Defect record.** The Stage-5 map named six conceptual files that were",
        "never produced (`main_regression.csv`, `placebo_distribution.csv`,",
        "`regime_split.csv`, `event_study_car.csv`, `robustness_matrix.csv`,",
        "`broker_persistence.csv`). This was latent documentation drift, not a v2",
        "regression; the Stage-6 register audit did not cover the chapter surface.",
        "Diagnosis and audit-coverage gap: `docs/analysis_deviations.md` #31.",
        "",
        "**Reading the table.** `claim_version` distinguishes frozen v1 claims",
        "(`v1`) from v2 governance/robustness claims (`v2`). A v1 number remains",
        "citable even when v2 reclassifies the hypothesis: H7's v1 p=.0274 is a",
        "v1 claim, while its `NULL_FRAGILE` label is a v2 claim. `status` is",
        "`VERIFIED`, `VERIFIED_V1_IMMUTABLE`, or `SCAFFOLD` (structural handoff",
        "asset with no numeric claim). Hashes are SHA-256 at generation; the audit",
        "also requires the latest hash-bearing provenance-manifest row to match.",
        "",
        "| chapter | section | claim_id | artifact_path | exp_id | sha256 | claim_version | status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for chapter, section, claim_id, artifact, exp_id, version, status in CLAIMS:
        path = ROOT / artifact
        if not path.is_file():
            raise SystemExit(f"missing crosswalk artefact: {artifact}")
        lines.append(
            f"| {chapter} | {section} | {claim_id} | `{artifact}` | "
            f"{exp_id} | `{sha256(path)}` | {version} | {status} |")
    lines += [
        "",
        "**Counts.** "
        f"{len(CLAIMS)} claims across {len({c[0] for c in CLAIMS})} chapters; "
        f"{len({c[3] for c in CLAIMS})} distinct artefacts.",
        "",
    ]
    return "\n".join(lines)


def write_pack_manifests() -> None:
    for chapter, rows in PACKS.items():
        out = ASSETS / f"{chapter}_asset_manifest.csv"
        with open(out, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(["asset_id", "artifact_path", "role", "exp_id",
                             "claim_version", "sha256"])
            for asset_id, artifact, role, exp_id, version in rows:
                path = ROOT / artifact
                if not path.is_file():
                    raise SystemExit(f"missing pack artefact: {artifact}")
                writer.writerow([asset_id, artifact, role, exp_id, version,
                                 sha256(path)])
        print(f"pack manifest: {out.relative_to(ROOT)} ({len(rows)} assets)")


def main() -> None:
    MAP.write_text(render_map(), encoding="utf-8")
    print(f"crosswalk: {MAP.relative_to(ROOT)} ({len(CLAIMS)} claims)")
    write_pack_manifests()


if __name__ == "__main__":
    main()
