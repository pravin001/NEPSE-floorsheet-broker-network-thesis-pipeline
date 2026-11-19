# Superseded v2.0.2 result tables — audit only

These files are **byte-for-byte copies** of the tables of record produced by
the `v2.0.2-prewrite` release (tag `v2.0.2-prewrite`, commit `499f8c2`). They
are preserved because the v2.1.0 reciprocity correction changes the
`reciprocity_volume` feature and every downstream result that uses it.

**Do not cite these as current results.** The canonical tables are one
directory up (`outputs/tables/`). The current final classification is
`outputs/tables/v2_final_headline_set.csv`; the pre-correction classification
in this directory is retained only so the change can be audited row by row.

The correction, its exact code change, and an old-versus-corrected comparison
are documented in `reports/reciprocity_correction.md`.

`MANIFEST.sha256` records the digest of every file in this directory. Files
are copied, never regenerated; a hash mismatch means the audit copy was
altered.
