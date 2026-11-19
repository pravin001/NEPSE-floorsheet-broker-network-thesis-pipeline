"""Build the canonical final headline set (V2-5, Stage 5).

Reads only frozen/v2 result tables, applies the pre-declared composition rule

    final = Stage-1 classification
            cap Stage-2 concordance
            cap Stage-3 checks (liquidity, EGARCH, tails)

and writes `outputs/tables/v2_final_headline_set.csv` with the EXACT columns
required by the brief.  Every label is derived from the source tables and
asserted back against them, so the table cannot drift silently.

v2.1.0 change: the mapping is no longer a hardcoded per-hypothesis dict.  The
v2.0.2 dict encoded the old outcome (H10 = HEADLINE_MODERATE).  After the
reciprocity correction a confirmed result can legitimately fail a cap, and a
fixed dict would either reproduce a stale claim or abort.  The rule below is
the same pre-declared composition rule, applied to whatever the corrected
tables say.

Classification taxonomy (brief): HEADLINE_ROBUST, HEADLINE_MODERATE,
EXPLORATORY_POST_HOC, NULL_POWERED, NULL_FRAGILE, NULL_UNDERPOWERED.

Mapping decisions (logged as Stage-5 deviations):
  * Stage-1 `NULL_ROBUST` has no direct brief label; it maps to NULL_POWERED
    when the MDE table classifies it NULL_POWERED, else NULL_UNDERPOWERED.
  * A 4/4 (`STRONG`) concordance is HEADLINE_ROBUST; 3/4 (`MODERATE`) is
    HEADLINE_MODERATE.
  * A Stage-1 confirmed result that fails Stage-2 (not STRONG/MODERATE) or a
    Stage-3 check is capped to NULL_FRAGILE with an explicit cap reason.
  * H8 remains NULL_FRAGILE even though MDE says NULL_UNDERPOWERED: fragility
    (two registered robustness failures) is the specific demotion fact; the
    underpower property stays in `null_classification.csv` and limitations L8.
  * `survives_egarch` is the Stage-3 definition: sign match vs the v1 beta AND
    p < ALPHA (= 0.10, scripts/run_v2_stage3.py), not p < 0.05.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from nepsemsc.utils.io import atomic_write_df

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"

HYPOTHESES = [f"H{i}" for i in range(1, 11)]
ALLOWED = {
    "HEADLINE_ROBUST", "HEADLINE_MODERATE", "EXPLORATORY_POST_HOC",
    "NULL_POWERED", "NULL_FRAGILE", "NULL_UNDERPOWERED",
}

DIRECTION_WORD = {"pos": "positive", "neg": "negative", "amb": "ambiguous"}


def _final_label(hid: str, grid: pd.DataFrame, rw: pd.DataFrame,
                 conc: pd.DataFrame, liq: pd.DataFrame, eg: pd.DataFrame,
                 mde: pd.DataFrame) -> tuple[str, str]:
    """Apply the pre-declared composition rule; return (label, reason)."""
    base = str(grid.loc[hid, "result_classification"])

    if base == "CONFIRMED_HEADLINE":
        if not bool(conc.loc[hid, "stage2_headline"]):
            return ("NULL_FRAGILE",
                    "composition_cap_stage2_concordance")
        if not bool(liq.loc[hid, "survives_liquidity"]):
            return "NULL_FRAGILE", "composition_cap_liquidity"
        if not bool(eg.loc[hid, "survives_egarch"]):
            return "NULL_FRAGILE", "composition_cap_egarch"
        if str(conc.loc[hid, "se_concordance"]) == "STRONG":
            return ("HEADLINE_ROBUST",
                    "stage1_confirmed_stage2_strong_stage3_pass")
        if str(conc.loc[hid, "se_concordance"]) == "MODERATE":
            return ("HEADLINE_MODERATE",
                    "stage1_confirmed_stage2_moderate_stage3_pass")
        return "NULL_FRAGILE", "composition_cap_stage2_concordance"

    if base == "EXPLORATORY_POST_HOC":
        return base, "stage1_exploratory_post_hoc"

    if base == "NULL_FRAGILE":
        return base, "stage1_null_fragile"

    if base == "NULL_ROBUST":
        if hid in mde.index and mde.loc[hid, "classification"] == "NULL_POWERED":
            return "NULL_POWERED", "stage1_null_robust_mde_powered"
        return "NULL_UNDERPOWERED", "stage1_null_robust_mde_underpowered"

    raise AssertionError(f"{hid}: unknown Stage-1 label {base!r}")


def _tail_label(hid: str, row: pd.Series) -> str:
    """Compact tail label; null-test tails are descriptive only."""
    cls = str(row["tail_classification"])
    shape = str(row["tail_shape"])
    if hid in {"H4", "H6", "H7", "H8", "H10"}:
        return f"{cls} ({shape})"
    return f"{cls} (descriptive)"


def main() -> None:
    grid = pd.read_csv(TABLES / "hypothesis_grid_results_v2.csv")
    rw = pd.read_csv(TABLES / "hypothesis_grid_results_rw.csv")
    conc = pd.read_csv(TABLES / "se_concordance.csv")
    liq = pd.read_csv(TABLES / "headline_with_liquidity_controls.csv")
    eg = pd.read_csv(TABLES / "headline_with_egarch_outcome.csv")
    tails = pd.read_csv(TABLES / "quantile_tail_summary.csv")
    mde = pd.read_csv(TABLES / "null_classification.csv")

    grid = grid.set_index("test_id")
    rw = rw.set_index("test_id")
    conc = conc.set_index("test_id")
    tails = tails.set_index("test_id")
    mde = mde.set_index("test_id")

    liq = liq[liq["spec"] == "single_feature_liquidity"].set_index("test_id")
    eg = eg[eg["spec"] == "egarch_primary"].set_index("test_id")

    # Hard source checks: every hypothesis present exactly once.
    for name, frame in [("grid", grid), ("rw", rw), ("concordance", conc),
                        ("liquidity", liq), ("egarch", eg), ("tails", tails)]:
        missing = sorted(set(HYPOTHESES) - set(frame.index))
        if missing:
            raise AssertionError(f"{name} missing hypotheses: {missing}")
        if len(frame.loc[HYPOTHESES]) != 10:
            raise AssertionError(f"{name} does not have one row per hypothesis")

    # Composition assertions: the final label must be earned, not asserted.
    labels: dict[str, str] = {}
    reasons: dict[str, str] = {}
    for hid in HYPOTHESES:
        label, reason = _final_label(hid, grid, rw, conc, liq, eg, mde)
        labels[hid], reasons[hid] = label, reason
        if label not in ALLOWED:
            raise AssertionError(f"{hid}: {label} outside brief taxonomy")
        base = str(grid.loc[hid, "result_classification"])
        if label in {"HEADLINE_ROBUST", "HEADLINE_MODERATE"}:
            if base != "CONFIRMED_HEADLINE":
                raise AssertionError(f"{hid}: headline without Stage-1 confirmation")
            if not bool(conc.loc[hid, "stage2_headline"]):
                raise AssertionError(f"{hid}: headline absent from Stage-2 set")
            if not bool(liq.loc[hid, "survives_liquidity"]):
                raise AssertionError(f"{hid}: headline fails liquidity controls")
            if not bool(eg.loc[hid, "survives_egarch"]):
                raise AssertionError(f"{hid}: headline fails EGARCH check")
            want = "STRONG" if label == "HEADLINE_ROBUST" else "MODERATE"
            if str(conc.loc[hid, "se_concordance"]) != want:
                raise AssertionError(
                    f"{hid}: {label} but concordance is "
                    f"{conc.loc[hid, 'se_concordance']!r}, not {want}")
        elif label == "EXPLORATORY_POST_HOC":
            if base != "EXPLORATORY_POST_HOC":
                raise AssertionError(f"{hid}: not Stage-1 exploratory")
            if np.sign(grid.loc[hid, "bp"]) == np.sign(
                    {"pos": 1, "neg": -1}[grid.loc[hid, "predicted_sign"]]):
                raise AssertionError(f"{hid}: opposite-sign rationale missing")
        elif label == "NULL_FRAGILE":
            if base == "NULL_FRAGILE":
                if (float(rw.loc[hid, "rw_p"]) <= 0.10
                        and bool(grid.loc[hid, "bh_sig_q10"])):
                    raise AssertionError(
                        f"{hid}: fragile label but both RW p <= .10 and BH pass")
            elif base == "CONFIRMED_HEADLINE":
                if not reason.startswith("composition_cap_"):
                    raise AssertionError(
                        f"{hid}: confirmed headline capped without a reason")
                cap = reason.removeprefix("composition_cap_")
                cap_ok = {
                    "stage2_concordance": not bool(
                        conc.loc[hid, "stage2_headline"]),
                    "liquidity": not bool(liq.loc[hid, "survives_liquidity"]),
                    "egarch": not bool(eg.loc[hid, "survives_egarch"]),
                }.get(cap)
                if cap_ok is None:
                    raise AssertionError(f"{hid}: unknown cap {cap!r}")
                if not cap_ok:
                    raise AssertionError(
                        f"{hid}: recorded cap {cap!r} is not actually failed")
            else:
                raise AssertionError(
                    f"{hid}: fragile label without Stage-1 fragility or a cap")
        elif label in {"NULL_POWERED", "NULL_UNDERPOWERED"}:
            if base != "NULL_ROBUST":
                raise AssertionError(f"{hid}: powered null without Stage-1 robust")
            mde_cls = str(mde.loc[hid, "classification"])
            if label == "NULL_POWERED" and mde_cls != "NULL_POWERED":
                raise AssertionError(f"{hid}: MDE does not confirm power")
            if label == "NULL_UNDERPOWERED" and mde_cls == "NULL_POWERED":
                raise AssertionError(f"{hid}: MDE confirms power")
        else:
            raise AssertionError(f"{hid}: unexpected final label {label}")

    rows = []
    for hid in HYPOTHESES:
        g = grid.loc[hid]
        t = tails.loc[hid]
        rows.append({
            "hypothesis": hid,
            "pre_declared_direction": DIRECTION_WORD[str(g["predicted_sign"])],
            "estimated_beta": float(g["bp"]),
            "dk_p": float(g["p_dk"]),
            "rw_p": float(rw.loc[hid, "rw_p"]),
            "wild_bootstrap_p": float(conc.loc[hid, "p_wb"]),
            "se_concordance": ("NULL (0/4)"
                               if pd.isna(conc.loc[hid, "se_concordance"])
                               else str(conc.loc[hid, "se_concordance"])),
            "survives_liquidity": bool(liq.loc[hid, "survives_liquidity"]),
            "survives_egarch": bool(eg.loc[hid, "survives_egarch"]),
            "tail_concentration": _tail_label(hid, t),
            "final_classification": labels[hid],
        })

    out = pd.DataFrame(rows)
    exact = ["hypothesis", "pre_declared_direction", "estimated_beta", "dk_p",
             "rw_p", "wild_bootstrap_p", "se_concordance", "survives_liquidity",
             "survives_egarch", "tail_concentration", "final_classification"]
    if out.columns.tolist() != exact:
        raise AssertionError(f"column order mismatch: {out.columns.tolist()}")
    if len(out) != 10 or out["hypothesis"].duplicated().any():
        raise AssertionError("final table must be 10 unique hypotheses")
    if out["final_classification"].isna().any():
        raise AssertionError("unclassified hypothesis")
    if out["final_classification"].nunique() < 3:
        raise AssertionError("degenerate classification set")

    atomic_write_df(out, TABLES / "v2_final_headline_set.csv", index=False)

    print("final headline set written")
    print(out.to_string(index=False), flush=True)
    print("\ncomposition audit")
    audit = pd.DataFrame({
        "hypothesis": HYPOTHESES,
        "stage1": [grid.loc[h, "result_classification"] for h in HYPOTHESES],
        "stage2_headline": [bool(conc.loc[h, "stage2_headline"]) for h in HYPOTHESES],
        "stage2_concordance": [conc.loc[h, "se_concordance"] for h in HYPOTHESES],
        "mde": [mde.loc[h, "classification"] if h in mde.index else "n/a"
                for h in HYPOTHESES],
        "liquidity": [bool(liq.loc[h, "survives_liquidity"]) for h in HYPOTHESES],
        "egarch": [bool(eg.loc[h, "survives_egarch"]) for h in HYPOTHESES],
        "rw_p": [float(rw.loc[h, "rw_p"]) for h in HYPOTHESES],
        "final": [labels[h] for h in HYPOTHESES],
        "reason": [reasons[h] for h in HYPOTHESES],
    })
    print(audit.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
