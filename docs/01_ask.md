# 01 — Ask

## Business Context

Someone deciding to release a game on Steam — an indie developer or a small
publisher — needs to decide which genre segment to compete in and which
pricing model to adopt, based on what the 2021–2025 market actually
rewarded in terms of engagement.

## Primary Business Question

Which genre and monetization model combinations (free vs. paid) were
associated with higher market engagement (recommendations) between 2021
and 2025, and how did this pattern evolve year over year?

## Supporting Questions

1. What is the market composition by genre and by year — are specific
   genres gaining or losing share in release volume between 2021 and 2025?
2. What is the proportion of free vs. paid games in the market, and has
   this proportion shifted over the years?

## Key Definitions (to avoid ambiguity downstream)

- **Engagement**: measured via the `recommendations` column. This is a
  proxy for visibility/engagement, not a measure of game quality, review
  score, or financial success.
- **Monetization model**: derived strictly from the `price` column
  (`price == 0` → Free, `price > 0` → Paid). The `Free To Play` tag found
  inside the `genres` column is NOT used for this classification — initial
  data inspection showed low reliability for this tag as a monetization
  indicator (see `02_prepare.md` for details).
- **Market scope**: limited to games with a release date between
  2021-01-01 and 2025-12-31, as captured in this dataset. This is not a
  full historical view of the Steam catalog.

## Explicitly Out of Scope

- **Game "success" or "quality"**: this analysis does not evaluate
  critical or commercial success. `recommendations` reflects
  engagement/visibility, not quality or revenue.
- **Comparison to the full Steam catalog**: conclusions apply only to the
  2021–2025 window present in this dataset, not to Steam's entire
  historical library.
- **The `categories` column** (e.g., "Single-player", "Steam
  Achievements"): rich metadata, but outside the scope of this project's
  current business question. Flagged as a potential extension for future
  work.

## Why This Framing (Design Rationale)

The original project brief proposed a broad theme ("genre, price, and
monetization trends"). This was narrowed into a single, measurable,
actionable question for two reasons:

1. **Focus over breadth**: a single guiding question produces a coherent
   dashboard narrative, rather than a set of disconnected charts covering
   too many angles at once.
2. **Alignment with data reality**: initial inspection (see
   `notebooks/01_initial_inspection.ipynb`) revealed that `recommendations`
   follows a long-tail distribution (mean ≈ 362, median = 0, max ≈
   862,487), and that `price` is a more reliable monetization signal than
   the `Free To Play` genre tag. The business question was worded to stay
   within what the data can support with confidence, rather than implying
   a level of precision (e.g., exact price-point optimization) the data
   does not reliably provide.