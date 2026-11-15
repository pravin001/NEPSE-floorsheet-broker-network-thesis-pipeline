# Licence Review — v2.0.2 pre-write sprint

**Retrieved:** 2026-11-13T10:21:13Z (UTC)
**Scope:** every raw data source in `data/metadata/provenance_manifest.csv`.
**Rule applied:** only the text actually returned by the source at retrieval is
quoted. Where a source is silent, the entry is marked `UNCERTAIN`; no permission
is inferred from silence. This review does not change any frozen result.

> **Critical finding for tier1.** The live Kaggle dataset metadata for
> `rohankasichhwa/nepse-daily-stock-data-2012-2025` now returns
> `"licenseName":"MIT"`. The earlier `pending_user_ui_check` status is therefore
> closed at the Kaggle layer. The dataset description separately says it is
> “intended for educational and research purposes”, and its prices are “scraped
> from NEPSE Alpha”. The upstream NEPSE Alpha terms were **not** retrieved; that
> residual is marked `UNCERTAIN` below.

---

## 1. Kaggle `viking303/nepse-historical-floorsheet` (2021–2023 corpus)

**Source page:** https://www.kaggle.com/datasets/viking303/nepse-historical-floorsheet
**Metadata endpoint used:** `https://www.kaggle.com/api/v1/datasets/view/viking303/nepse-historical-floorsheet`
**Version retrieved:** 14 · **Last updated:** 2026-05-03T16:59:02.197Z

### Quoted terms

Kaggle metadata field, verbatim:

> `"licenseName":"CC0: Public Domain"`

Dataset description, verbatim:

> “Data is scraped as-is from merolagani.com with no modifications”

CC0 1.0 legal code (https://creativecommons.org/publicdomain/zero/1.0/legalcode.txt), verbatim:

> “Affirmer hereby overtly, fully, permanently, irrevocably and unconditionally
> waives, abandons, and surrenders all of Affirmer's Copyright and Related Rights
> and associated claims and causes of action … in the Work … for any purpose
> whatsoever, including without limitation commercial, advertising or promotional
> purposes”

> “4. Limitations and Disclaimers. … c. Affirmer disclaims responsibility for
> clearing rights of other persons that may apply to the Work or any use thereof”

### Conclusions

| Question | Answer |
|---|---|
| (a) What does it permit? | Reproduction, adaptation, distribution, display, communication, translation, and database extraction/reuse, for any purpose including commercial use. Academic use is squarely within the grant. |
| (b) What does it require? | No attribution, notice, or share-alike condition is imposed by CC0. No warranty. |
| (c) Price-derived figures permitted? | **YES** as to the dataset as distributed by the uploader. |
| (d) Derived tables in the deposit permitted? | **YES** as to the dataset as distributed by the uploader. |

**Ambiguity / residual risk:** the uploader states the data was scraped from
merolagani.com. CC0 paragraph 4(c) expressly disclaims responsibility for
third-party rights. The uploader's CC0 dedication cannot, by itself, clear any
rights merolagani may hold in the underlying compilation. **Upstream:
`UNCERTAIN`.** This does not affect the thesis's internal academic use; it is a
deposit/redistribution caution.

**Traffic light:** 🟢 **GREEN** for the dataset grant; 🟡 **AMBER** note for
upstream merolagani rights.

---

## 2. `socrateai-official/nepse-open-data` (2024 floorsheets)

**Repository:** https://github.com/socrateai-official/nepse-open-data
**Licence file retrieved:** https://raw.githubusercontent.com/socrateai-official/nepse-open-data/main/LICENSE
**GitHub licence API:** https://api.github.com/repos/socrateai-official/nepse-open-data/license

### Quoted terms (full licence, verbatim)

> MIT License
>
> Copyright (c) 2025 SocrateAI
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this dataset and associated documentation files (the "Data"), to deal
> in the Data without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Data, and to permit persons to whom the Data is furnished to do so,
> subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in
> all copies or substantial portions of the Data.
>
> THE DATA IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
> INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
> PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
> COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
> IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
> CONNECTION WITH THE DATA OR THE USE OR OTHER DEALINGS IN THE DATA.

### Conclusions

| Question | Answer |
|---|---|
| (a) What does it permit? | Use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the data, without restriction; academic use included. |
| (b) What does it require? | The copyright notice and permission notice must be included in all copies or substantial portions of the data. No share-alike. No warranty. |
| (c) Price-derived figures permitted? | **YES**, with the notice preserved in the thesis/deposit documentation. |
| (d) Derived tables in the deposit permitted? | **YES**, with the notice preserved. |

**Ambiguity / residual risk:** the licence text is MIT in substance but replaces
“Software” with “Data”; GitHub's licence detector consequently reports
`"key":"other"`, `"spdx_id":"NOASSERTION"`. The document itself is titled
“MIT License” and contains the full MIT permission grant, so the operative
terms are clear on their face. The upstream NEPSE/merolagani rights are not
addressed. **Upstream: `UNCERTAIN`.**

**Traffic light:** 🟢 **GREEN** with attribution/notice; 🟡 note for upstream
rights and the `NOASSERTION` classifier.

---

## 3. Kaggle `rohankasichhwa/nepse-daily-stock-data-2012-2025` (tier1 OHLCV — critical)

**Source page:** https://www.kaggle.com/datasets/rohankasichhwa/nepse-daily-stock-data-2012-2025
**Metadata endpoint used:** `https://www.kaggle.com/api/v1/datasets/view/rohankasichhwa/nepse-daily-stock-data-2012-2025`
**File-list endpoint used:** `https://www.kaggle.com/api/v1/datasets/list/rohankasichhwa/nepse-daily-stock-data-2012-2025`
**Version retrieved:** 1 · **Last updated:** 2025-09-28T16:19:57.793Z

### Quoted terms

Kaggle metadata field, verbatim:

> `"licenseName":"MIT"`

Dataset description, verbatim:

> “This dataset contains historical daily stock data for 100 companies listed on
> the Nepal Stock Exchange (NEPSE) from 2012 to 2025.”

> “The dataset is intended for educational and research purposes.”

> “**Source:** Raw stock prices scraped from NEPSE Alpha, processed and enhanced
> for analysis.”

The public file listing returned per-symbol CSV files (e.g. `ADBL.csv`,
`AHL.csv`, `AHPC.csv`, …). No separate dataset-specific licence file was exposed
in the retrieved listing.

### Conclusions

| Question | Answer |
|---|---|
| (a) What does it permit? | Kaggle declares the dataset MIT. MIT permits use, copy, modify, merge, publish, distribute, sublicense, and/or sell, subject to the notice condition; the description additionally states educational/research intent, which covers the thesis. |
| (b) What does it require? | Under the declared MIT licence: include the copyright and permission notice in copies or substantial portions. No share-alike. No warranty. The exact dataset-specific notice was not exposed at retrieval, so the notice text must be taken from the standard MIT terms or requested from the uploader. |
| (c) Price-derived figures permitted? | **YES for the academic thesis** on the Kaggle-declared MIT grant plus the explicit educational/research statement. Public redistribution of the figures remains subject to the upstream caveat below. |
| (d) Derived tables in the deposit permitted? | **YES for derived tables** on the same basis; raw OHLCV is not part of the derived-only deposit. Upstream caveat applies to any attempt to redistribute the raw series. |

**Ambiguity / residual risk (material):** the upstream is “NEPSE Alpha”, and no
NEPSE Alpha terms were retrieved. The Kaggle uploader's MIT label is a grant by
the uploader; it may not exhaust upstream rights in the scraped prices. No
separate licence text file appeared in the retrieved file listing. **Upstream:
`UNCERTAIN`.** The correct viva/deposit wording is: “Kaggle metadata declares
MIT; the dataset description limits the intended use to education and research;
upstream NEPSE Alpha terms were not independently verified.”

**Status change:** the prior manifest entry `pending_user_ui_check` is superseded
by this retrieval. The live Kaggle metadata is MIT. This is a documentation
update only; no frozen result changes.

**Traffic light:** 🟢 **GREEN** for academic use and thesis figures; 🟡 **AMBER**
for public redistribution until the NEPSE Alpha upstream terms are checked.

---

## 4. `SamirWagle/Nepse-All-Scraper` (tier2 OHLCV gap-fill)

**Repository:** https://github.com/SamirWagle/Nepse-All-Scraper
**Metadata endpoint used:** `https://api.github.com/repos/SamirWagle/Nepse-All-Scraper`
**README retrieved:** https://raw.githubusercontent.com/SamirWagle/Nepse-All-Scraper/main/README.md

### Quoted terms

GitHub repository metadata, verbatim:

> `"license":null`

README licence badge, verbatim:

> `License: Educational`

README disclaimer, verbatim:

> “This project is for **educational purposes only**.
> Data is sourced from publicly available websites (ShareSansar, Merolagani).
> Not financial advice. Do your own research before making investment decisions.”

Repository contents listing returned no `LICENSE` file.

### Conclusions

| Question | Answer |
|---|---|
| (a) What does it permit? | No formal copyright licence is granted. The README states an educational-purpose intent. Academic research use is consistent with that stated intent, but it is not a legal licence grant. |
| (b) What does it require? | No attribution text is specified. Academic norms require attribution to the repository and its upstream sources. |
| (c) Price-derived figures permitted? | **UNCERTAIN.** Tier2 is a gap-fill only; the thesis figures should use tier1 as the primary source. Any figure that materially depends on tier2 rows needs the user's manual clearance. |
| (d) Derived tables in the deposit permitted? | **NO** without permission. Do not redistribute tier2 raw or materially tier2-derived data. |

**Ambiguity / residual risk:** `license:null` plus “educational purposes only”
is not a reuse grant. The upstream sources (ShareSansar, Merolagani) are not
licensed in the repository. **`UNCERTAIN` for figures; RED for redistribution.**

**Traffic light:** 🟡 **AMBER** for internal academic use with attribution;
🔴 **RED** for deposit/redistribution.

---

## 5. `menaceXnadin/nepse-historical-market-data-csv` (NEPSE composite index)

**Repository:** https://github.com/menaceXnadin/nepse-historical-market-data-csv
**Metadata endpoint used:** `https://api.github.com/repos/menaceXnadin/nepse-historical-market-data-csv`
**README retrieved:** https://raw.githubusercontent.com/menaceXnadin/nepse-historical-market-data-csv/master/README.md
**Data file used:** `data/index/adjusted/NEPSE_adjusted.csv`

### Quoted terms

GitHub repository metadata, verbatim:

> `"license":null`

README, verbatim:

> “This is an unofficial mirror, not data published by NEPSE itself. Check
> anything important against an official source.”

> “Daily prices: [ShareHub Nepal](https://sharehubnepal.com) candle-chart API”

Repository contents listing returned no `LICENSE` file.

### Conclusions

| Question | Answer |
|---|---|
| (a) What does it permit? | Nothing is stated. No licence grant. Default copyright applies to whatever the repository author contributed; the upstream ShareHub/NEPSE rights are also unstated. |
| (b) What does it require? | No terms specified. Academic attribution is expected as a matter of scholarly practice, not as a licence condition. |
| (c) Price-derived figures permitted? | **UNCERTAIN.** The index is a secondary input for regime shading/benchmark only and is not used in the F1–F10 priority figures. Do not build a headline figure on it without clearance. |
| (d) Derived tables in the deposit permitted? | **NO** without permission. Keep index-derived material out of the deposit. |

**Ambiguity / residual risk:** `license:null` and an explicit “unofficial
mirror” statement. **`UNCERTAIN` for academic use; RED for redistribution.**

**Traffic light:** 🟡 **AMBER** for internal academic use only; 🔴 **RED** for
deposit/redistribution.

---

## 6. Summary traffic-light table

| Source | Role in thesis | Dataset grant as shown | Academic use | Figures in thesis | Derived tables in deposit | Overall |
|---|---|---|---|---|---|---|
| Kaggle `viking303` floorsheets 2021–2023 | Primary floorsheet corpus | **CC0: Public Domain** | 🟢 Permitted | 🟢 Permitted | 🟢 Permitted | 🟢 (upstream 🟡) |
| `socrateai` 2024 floorsheets | 2024 floorsheet corpus | **MIT** (modified wording; GitHub `NOASSERTION`) | 🟢 Permitted | 🟢 Permitted with notice | 🟢 Permitted with notice | 🟢 (upstream 🟡) |
| Kaggle `rohankasichhwa` OHLCV | Tier1 prices / outcomes | **MIT** | 🟢 Permitted; description says education/research | 🟢 Permitted for thesis; 🟡 for public redistribution | 🟢 Derived tables permitted; raw not deposited | 🟢 academic / 🟡 redistribution |
| `SamirWagle` OHLCV | Tier2 gap-fill | **None** (`license:null`; “Educational”) | 🟡 Stated educational intent, no formal grant | 🟡 `UNCERTAIN` — avoid material reliance | 🔴 Not permitted | 🟡 / 🔴 |
| `menaceXnadin` NEPSE index | Secondary regime shading | **None** (`license:null`; “unofficial mirror”) | 🟡 Internal academic use only | 🟡 `UNCERTAIN` — not used in F1–F10 | 🔴 Not permitted | 🟡 / 🔴 |

**Legend:** 🟢 permitted on the quoted terms; 🟡 conditional/uncertain, user
decision or attribution required; 🔴 not permitted without explicit permission.

---

## 7. What remains for the user to resolve manually

1. **Tier1 upstream (NEPSE Alpha).** The Kaggle metadata says MIT and the
   description says education/research. If the university or deposit requires a
   clean upstream chain, ask the Kaggle uploader for the NEPSE Alpha permission
   or use an official NEPSE/SEBON series. Until then, the thesis can cite the
   Kaggle MIT label and the education/research statement; the deposit should not
   redistribute raw OHLCV.
2. **Tier2 (SamirWagle) and NEPSE index (menaceXnadin).** Neither has a licence
   file. They are not needed for the F1–F10 priority figures. If either is used
   in a printed figure beyond incidental benchmark shading, obtain permission or
   replace the series.
3. **Attribution block.** For socrateai and (if used) tier1, include the
   copyright/permission notice in the thesis data appendix or deposit README.
   Suggested wording is a direct quotation of the retrieved licence notice, not
   a paraphrase.
4. **Deposit archive.** The v2.0.1 derived-only archive already excludes raw
   data and figures. The licence position above does not require rebuilding it;
   it does require the deposit README's licence table to be updated from
   “tier1 pending” to “tier1 Kaggle metadata MIT; upstream NEPSE Alpha
   `UNCERTAIN`”.

---

## 8. Retrieval record

| Source | URL actually retrieved | What it returned |
|---|---|---|
| viking303 | `https://www.kaggle.com/api/v1/datasets/view/viking303/nepse-historical-floorsheet` | JSON with `licenseName: CC0: Public Domain`, version 14 |
| CC0 legal code | `https://creativecommons.org/publicdomain/zero/1.0/legalcode.txt` | Full CC0 1.0 text |
| socrateai | `https://raw.githubusercontent.com/socrateai-official/nepse-open-data/main/LICENSE` | Full MIT-style licence text, copyright 2025 SocrateAI |
| socrateai API | `https://api.github.com/repos/socrateai-official/nepse-open-data/license` | Licence blob; detector `key: other`, `spdx_id: NOASSERTION` |
| tier1 Kaggle | `https://www.kaggle.com/api/v1/datasets/view/rohankasichhwa/nepse-daily-stock-data-2012-2025` | JSON with `licenseName: MIT`, version 1 |
| tier1 file list | `https://www.kaggle.com/api/v1/datasets/list/rohankasichhwa/nepse-daily-stock-data-2012-2025` | Per-symbol CSV listing; no separate licence file in the returned page |
| SamirWagle | `https://api.github.com/repos/SamirWagle/Nepse-All-Scraper`; `.../main/README.md` | `license:null`; README “License: Educational” and disclaimer |
| menaceXnadin | `https://api.github.com/repos/menaceXnadin/nepse-historical-market-data-csv`; `.../master/README.md` | `license:null`; README “unofficial mirror” and sources |

No licence conclusion in this document is based on memory or on a secondary
summary. Every quoted sentence above was returned by the cited URL on
2026-11-13.

---

## 9. Author decision (2026-11-14)

The author reviewed this review and **accepted the tier1 AMBER caveat** for
public release of the thesis repository, including price-derived figures. The
public GitHub repository therefore includes `outputs/figures/` (33 tracked
files). This acceptance is not a finding that upstream NEPSE Alpha rights are
cleared; the upstream position remains `UNCERTAIN`, and the derived-only
deposit archive continues to exclude figures. Recorded in
`docs/analysis_deviations.md` #42.

---

## 10. Upstream NEPSE Alpha terms (retrieved 2026-11-14)

**Source page:** `https://nepsealpha.com/login` — the “Terms & Conditions”
modal for the Sastoshare Service, operated by Nepse Alpha Private Limited.
**Retrieved:** 2026-11-14T09:12:54Z.

### Quoted terms (verbatim; typography preserved)

> “This document, the "Terms & Conditions " for Using the "Sastoshare" Service,
> governs the relationship between the Client (Subscribers) and Nepse Alpha
> Private Limited (the "Company") regarding the use of the Service”

> “The data, analysis, informations, description, Signals, Statistics etc. and
> any other information available on the Companyr services, is independently
> work and effort of the Company and is not subject to verification.”

> “Upon expiration of the account subscription, all data access and features
> will be immediately terminated until the subscription is renewed.”

> “Nepsealpha.com ©2026 All rights reserved”

### What the terms do and do not say

- They are subscription terms between NEPSE Alpha and its clients.
- They describe the data and analysis as the Company's own work and reserve
  rights (`All rights reserved`).
- They grant **no** open licence, redistribution right, or permission to
  create a public derivative dataset.
- They do not explicitly address third-party academic quotation of aggregate
  results; that remains a separate fair-use/University question.
- No separate `/terms`, `/terms-and-conditions`, or `/privacy-policy` page was
  available: all three returned HTTP 404 on 2026-11-14.

### Conclusion

The upstream status remains `UNCERTAIN` for legal clearance, but the operative
finding is stronger than silence: **no explicit redistribution grant was
found, and the provider claims the data as its own work with all rights
reserved.** Do not treat the Kaggle `MIT` label as clearing upstream rights.

- **Thesis:** cite the Kaggle label and the NEPSE Alpha terms; do not
  redistribute raw OHLCV.
- **Deposit:** the derived-only archive excludes figures; any public
  redistribution of materially tier1-derived tables or figures remains the
  author's accepted risk (#42) unless written permission is obtained or the
  series is replaced with an official/licensed source.

This section records the terms; it is not legal advice and does not upgrade the
upstream status.
