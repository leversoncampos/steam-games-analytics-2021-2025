# 03 — Process

## Overview

Data cleaning was performed in Python (pandas), in
`notebooks/02_data_cleaning.ipynb`, starting fresh from the raw CSV file
(independent of the earlier inspection notebook). This phase produced two
output files under `data/processed/`:

- **`games_clean.csv`** — the main fact table, one row per game (65,521
  rows, 12 columns). Source-faithful: original columns are preserved as
  collected, with only objective corrections applied (see below). No
  analytical scoping decisions were applied to this file.
- **`games_genres_bridge.csv`** — an analytical bridge table (`appid`,
  `genre`), one row per game-genre combination (175,691 rows), built
  specifically to resolve the many-to-many relationship between games and
  gameplay genres for this project's business question.

This separation is deliberate: `games_clean.csv` prioritizes fidelity to
the original Steam data, while `games_genres_bridge.csv` prioritizes
analytical usefulness for the specific question defined in `01_ask.md`.
Data correction and analytical scoping are treated as two distinct
concerns, not conflated into a single cleaning step.

## Transformations Applied to `games_clean.csv`

### 1. Monetization flag (`is_free`)

A boolean column derived strictly from `price == 0`. As established in
`01_ask.md` and `02_prepare.md`, the `Free To Play` genre tag was found
unreliable as a monetization indicator (90 games tagged `Free To Play`
with `price > 0`; 4,009 games with `price == 0` not tagged `Free To
Play`), so `price` is the sole source of truth for this flag.

### 2. Release date handling

- `release_date` was parsed to a proper `datetime` type.
- A new boolean column, `has_exact_release_date`, flags whether the
  original value resolved to a real calendar date (`True`, 64,121 rows)
  or not (`False`, 1,400 rows).
- Rows without an exact date correspond to unreleased titles with
  approximate release windows in the source data (e.g., "Q4 2025",
  "December 2025") — confirmed via review of the collection script's
  year-extraction logic (see `02_prepare.md`).
- The original raw text value of `release_date` was **not** retained in
  the final file. Decision rationale: retaining both the raw text and the
  parsed date would duplicate the same limitation already captured by
  `has_exact_release_date`, without adding analytical value. Only the
  parsed `datetime` value is kept, with `NaT` for the 1,400 rows lacking
  an exact date. `release_year` (100% populated) remains the reliable
  fallback granularity for any date-based analysis.
- No date was estimated or invented (e.g., defaulting "Q4 2025" to a
  specific day) — this was a deliberate choice to avoid introducing false
  precision not present in the source.

### 3. Missing value handling (`genres`, `categories`, `developer`, `publisher`)

Null values in these four columns (ranging from 0.01% to 0.28% of rows)
were filled with the explicit string `"Unknown"`, rather than left as
`NaN`. Rationale: Power BI can silently drop `NULL`/blank values from
groupings and visuals, making missing data invisible. An explicit
`"Unknown"` label ensures missing data remains visible and traceable in
any downstream visual or filter.

## Transformations Applied to `games_genres_bridge.csv`

### 4. Gameplay genre filtering — an analytical scoping decision, not a data correction

**Why this was necessary:** Steam's `genres` field is a shared taxonomy
used by the store for both games and non-game software products.
Initial exploration of the raw `genres` values (post-split) revealed
three distinct categories of tags mixed together:

- **True gameplay genres**: Action, Adventure, Casual, Indie, RPG, Racing,
  Simulation, Sports, Strategy, Massively Multiplayer
- **Software/tool categories**: Accounting, Animation & Modeling, Audio
  Production, Design & Illustration, Education, Game Development,
  Software Training, Utilities, Video Production, Web Publishing
- **Product status/model tags**: Early Access, Free To Play

This is a known characteristic of how Steam's store classifies products
— not a data quality defect, and not something introduced by the
collection script. However, mixing these categories into a single
"genre" dimension would make any genre-based analysis meaningless for
this project's business question (e.g., "Accounting" or "Web Publishing"
appearing as low-volume "genres" alongside "Action" or "RPG" has no
business interpretation relevant to a game developer deciding which
gameplay genre to compete in).

**What was excluded from the bridge table:**
`Accounting, Animation & Modeling, Audio Production, Design &
Illustration, Early Access, Education, Free To Play, Game Development,
Software Training, Utilities, Video Production, Web Publishing`

**What was preserved:**
The 10 gameplay genres listed above, kept exactly as they appear in the
source (no renaming or merging).

**Source data integrity:** this filtering was applied **only** to
`games_genres_bridge.csv`. The `genres` column in `games_clean.csv`
remains fully unmodified and contains the original semicolon-delimited
string exactly as collected, including software and status tags. Anyone
auditing this project can always trace the bridge table's scope back to
the untouched original field.

### 5. `Unknown` fallback in the bridge table

195 games had no gameplay-genre tag at all after filtering (i.e., their
`genres` value consisted entirely of software/status tags, or was
originally null). These games were assigned a single row with
`genre = "Unknown"` in the bridge table.

**What `"Unknown"` represents here, precisely:** it does not mean "genre
data is missing from Steam." It means "this game's Steam-assigned tags
did not include any tag classified as a gameplay genre for the purposes
of this project's analytical scope." This distinction matters because a
reader could otherwise assume `"Unknown"` reflects a data collection gap,
when it is in fact a scoping outcome — a deliberate byproduct of the
Section 4 filtering decision.

## Summary of Design Rationale

This Process phase treats data correction (fixing types, handling true
missing values, standardizing the free/paid flag) and analytical
modeling (scoping the genre dimension to the business question) as two
separate responsibilities, kept in two separate files. This avoids a
common pitfall in BI portfolio projects: silently reshaping the source
data to fit the analysis, without leaving a trace of what was original
versus what was scoped for a specific business question.