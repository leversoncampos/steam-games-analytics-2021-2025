# 02 — Prepare

## Data Source

- **Name**: Steam Games Dataset 2021-2025 (65k+)
- **Platform**: Kaggle
- **URL**: https://www.kaggle.com/datasets/jypenpen54534/steam-games-dataset-2021-2025-65k
- **Collection method**: gathered via the official Steam Web API (a
  collection script, `collect_data_v2.py`, is included in the raw dataset
  folder as provenance reference)
- **Format**: single CSV file, 65,521 rows, 10 columns
- **Storage**: no database used in this project (deliberate architecture
  decision — see project README). Raw file stored under `data/raw/`,
  processed under `data/processed/`.

## ROCCC Assessment

### Reliable — Partial

The dataset is internally consistent for most fields (no duplicate
`appid`, no full duplicate rows), but two reliability issues were
identified during initial inspection:

- The `Free To Play` tag inside `genres` does not reliably indicate
  monetization model: 90 games carry this tag while having `price > 0`
  (ranging from $0.99 to $29.99), and 4,009 games have `price == 0`
  without carrying this tag. `price` is treated as the authoritative
  monetization signal in this project; the tag is not used for that
  purpose.
- `recommendations` follows an extreme long-tail distribution (mean ≈
  362, median = 0, std ≈ 6,937, max ≈ 862,487). This is treated as a
  genuine market pattern (hit-driven engagement), not a data quality
  defect, but it means simple averages are misleading for group
  comparisons — median or ranking-based measures are used instead.

### Original — Confirmed, with a caveat

Data was collected directly from the official Steam Web API (a primary
source), not scraped or aggregated from a third party. However, the
dataset itself is a *curated extract* covering exactly 2021-01-01 to
2025-12-31 — an intentional collection window set by the dataset author,
not the full historical Steam catalog.

### Comprehensive — Partial

The dataset covers core metadata (title, release info, genres,
categories, price, recommendations, developer, publisher) for 65,521
titles, but does not include fields that would be needed for a
revenue-based or review-score-based analysis (e.g., actual sales figures,
user review scores, playtime). This is consistent with the project's Ask,
which explicitly scopes engagement (via `recommendations`) rather than
revenue or quality.

Missing values are low across the board and unlikely to bias conclusions:

| Column      | Missing | % of total |
|-------------|---------|------------|
| genres      | 66      | 0.10%      |
| categories  | 7       | 0.01%      |
| developer   | 53      | 0.08%      |
| publisher   | 183     | 0.28%      |

Additionally, 1,400 rows (2.1%) lack an exact `release_date` (values like
"2025", "Q4 2025", "December 2025") — all correspond to games not yet
released at collection time. `release_year` is fully populated (0 missing)
for all rows, including these, and serves as the reliable fallback
granularity for any yearly analysis.

### Current — Confirmed

The dataset covers through the end of 2025, which is current relative to
this project's analysis window. No data staleness concerns identified.

### Cited — Confirmed, with attribution note

Collected via the official Steam Web API and published on Kaggle for
educational use. All game titles, assets, and trademarks referenced in
this dataset belong to Valve Corporation and their respective developers
and publishers; this project uses the data strictly for educational and
portfolio purposes, with no commercial intent.

## Known Limitations (carried forward to Analyze/Act)

1. Analysis is scoped to the 2021–2025 window only — not representative
   of Steam's full historical catalog.
2. `recommendations` is an engagement/visibility proxy, not a measure of
   quality, review sentiment, or revenue.
3. Monetization is modeled strictly as free vs. paid (via `price`), not as
   a continuous price-point analysis, to avoid implying precision the data
   does not support for that use case.
4. 2.1% of rows lack an exact release date and are handled at
   `release_year` granularity only; this is documented, not silently
   dropped or estimated.

## License / Usage Note

This project is for educational and portfolio purposes only. Data was
collected via the official Steam Web API and is used here strictly for
analytical demonstration. All game names, assets, and trademarks belong to
Valve Corporation and the respective game developers/publishers.