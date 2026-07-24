# 02 — Prepare

## Data Source

- **Name**: Steam Games Dataset 2021-2025 (65k+)
- **Platform**: Kaggle
- **URL**: https://www.kaggle.com/datasets/jypenpen54534/steam-games-dataset-2021-2025-65k
- **Collection method**: gathered via the official Steam Web API. The
  author's collection script (`collect_data_v2.py`) is included in
  `data/raw/` for provenance and was reviewed directly as part of this
  project's Prepare phase.
- **Format**: single CSV file, 65,521 rows, 10 columns
- **Storage**: no database used in this project (deliberate architecture
  decision — see project README). Raw file stored under `data/raw/`,
  processed under `data/processed/`.

## Collection Method Details (from source code review)

Reviewing `collect_data_v2.py` directly (rather than relying only on the
Kaggle page description) clarified several aspects of how this dataset
was built:

- **Endpoints used**: Steam's `IStoreService/GetAppList` (to enumerate all
  app IDs) and `store.steampowered.com/api/appdetails` (to fetch metadata
  per app).
- **Type filter**: only apps where `type == 'game'` are kept — DLCs,
  soundtracks, and software are excluded by the script itself, prior to
  any filtering done in this project.
- **Year filter**: the script restricts results to `TARGET_YEARS =
  range(2021, 2026)`, extracting the year from the raw `release_date`
  string via a regex (`202[1-5]`). This is why the 2021–2025 window is an
  exact, deliberate collection boundary, not an organic range in the data.
- **App ID heuristic**: an `appid > 1,200,000` filter was applied to skip
  pre-2021 games efficiently, assuming newer games have higher app IDs.
- **Region/language**: requests were made with `cc: 'us'` and
  `l: 'english'`, meaning `price` reflects US-region Steam store pricing
  only.
- **Missing-field handling**: the script defaults several fields to empty
  values when absent from the API response — most notably
  `recommendations`, which defaults to `0` via
  `.get('recommendations', {}).get('total', 0)` (see Reliable section
  below for the implication of this).

## ROCCC Assessment

### Reliable — Partial

The dataset is internally consistent for most fields (no duplicate
`appid`, no full duplicate rows), but the following reliability issues
were identified — the last two confirmed directly from the author's
collection script, not inferred from the data alone:

- The `Free To Play` tag inside `genres` does not reliably indicate
  monetization model: 90 games carry this tag while having `price > 0`
  (ranging from $0.99 to $29.99), and 4,009 games have `price == 0`
  without carrying this tag. `price` is treated as the authoritative
  monetization signal in this project; the tag is not used for that
  purpose.
- `recommendations` follows an extreme long-tail distribution (mean ≈
  362, median = 0, std ≈ 6,937, max ≈ 862,487). This is consistent with a
  genuine hit-driven engagement pattern (a small number of high-visibility
  titles dominating the metric), but the collection script confirms that
  missing `recommendations` data from the Steam API is silently defaulted
  to `0` rather than left null. This means the dataset cannot distinguish
  "genuinely zero recommendations" from "recommendations data unavailable
  at collection time." Median and ranking-based measures are used instead
  of averages to reduce (but not eliminate) sensitivity to this ambiguity.
- `price` reflects US-region pricing only (`cc: 'us'` in the collection
  script). Conclusions about pricing/monetization apply to the US Steam
  storefront, not a global or regionally averaged price.

### Original — Confirmed, with a caveat

Data was collected directly from the official Steam Web API (a primary
source), not scraped or aggregated from a third party. This is confirmed
directly by the author's collection script (`collect_data_v2.py`), which
targets the `IStoreService` and `appdetails` endpoints. However, the
dataset itself is a *curated extract* covering exactly 2021-01-01 to
2025-12-31 — an intentional collection window set by the script's
`TARGET_YEARS` filter, not the full historical Steam catalog. This filter
also explains the approximate date values found in `release_date` for
unreleased titles (e.g., "Q4 2025"), since the year-extraction regex
matches on any string containing a valid year, regardless of date format
completeness.

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
released at collection time. `release_year` is fully populated (0
missing) for all rows, including these, and serves as the reliable
fallback granularity for any yearly analysis.

Collection also applied an `appid > 1,200,000` filter as a heuristic to
skip pre-2021 games efficiently. This assumes higher app IDs correspond to
newer releases, which holds in most cases but could theoretically exclude
a small number of games released in 2021-2025 under an older-registered
app ID (e.g., long Early Access titles). This is a minor, acknowledged gap
in coverage. The dataset is also restricted to `type == 'game'`, meaning
DLCs, soundtracks, and software are excluded — consistent with this
project's focus on games specifically.

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
   quality, review sentiment, or revenue — and may include an unknown
   proportion of zeros that reflect missing API data rather than genuine
   zero engagement.
3. Monetization is modeled strictly as free vs. paid (via `price`), not as
   a continuous price-point analysis, to avoid implying precision the data
   does not support for that use case. Pricing also reflects the US Steam
   storefront only.
4. 2.1% of rows lack an exact release date and are handled at
   `release_year` granularity only; this is documented, not silently
   dropped or estimated.
5. Coverage may slightly under-represent games released in 2021-2025 but
   registered under an older (lower) Steam app ID, due to the collection
   script's app ID heuristic filter.

## License / Usage Note

This project is for educational and portfolio purposes only. Data was
collected via the official Steam Web API and is used here strictly for
analytical demonstration. All game names, assets, and trademarks belong to
Valve Corporation and the respective game developers/publishers.