# US Industry Profit Pools, 2001–2025

An interactive profit-pool chart of US industries, built on Michael Mauboussin's
framework from *[Measuring the Moat](https://www.morganstanley.com/im/publication/insights/articles/article_measuringthemoat_us.pdf)*:
**economic profit = (ROIC − WACC) × invested capital** (see p.15, "Profit Pool")
and the ROIC-vs-spread trend line from Exhibit 12. Visual design (colors,
type, card style) is pulled from the Viability Check Webflow site's own
design tokens (Inter + Manrope, `#0075DE` link blue, warm off-white ground)
so the chart reads as part of the site rather than an embedded foreign widget.

Three views, switchable at the top of the chart:
- **Snapshot** — one year's profit pool as Mauboussin's variable-width box
  chart (bar width = capital, bar height = spread, bar area = economic profit).
- **Compare years** — the same box chart repeated as small multiples across
  a few chosen years (2001/2008/2013/2020/2025 by default), so eras sit side
  by side instead of behind a play button.
- **Trend** — Exhibit-12 style: pick one industry and see its ROIC and
  ROIC−WACC spread as two lines across all 25 years.

An earlier version used a modern animated bubble chart for the time
dimension; it was replaced with Compare-years + Trend after review — a
modern-looking animation read as generic and the moving bubbles were harder
to read at a glance than static small multiples or a plain line.

**Live chart:** `docs/index.html` (deploy to GitHub Pages — see below). A
standalone copy with the data embedded is also published as a Claude artifact
for quick review before it goes on the site.

## What's in this repo

```
data/
  profit_pool_all_industries_2001-2025.csv   raw input data (not modified)
src/
  clean_data.py                cleans the raw CSV -> docs/profit_pool_data.json
  export_slim.py                docs/profit_pool_data.json -> docs/pp_slim.json (chart payload)
  compare_with_source_sheet.py audit script: checks the CSV against the original
                                 Google Sheet it was compiled from (see below)
docs/
  index.html            the chart (GitHub Pages serves this folder)
  pp_slim.json          slim data payload index.html fetches
  profit_pool_data.json full cleaned dataset + cleaning notes (not fetched by the chart;
                          useful if you want to do further analysis)
```

## Data source

Data is sourced from Aswath Damodaran, NYU Stern School of Business:

- Current data: <https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datacurrent.html>
- Archived data: <https://pages.stern.nyu.edu/~adamodar/New_Home_Page/dataarchived.html>

Used with attribution, not resale, per his site's terms. The chart itself
carries this same attribution and both links in a footnote (`docs/index.html`).

**Checked against the source spreadsheet (2026-09-05):** the CSV was compiled
from a 25-tab Google Sheet (one tab per year, in Damodaran's original column
layout — Industry Name / Number of Firms / ROIC / Cost of Capital / spread /
BV of Capital / EVA). `src/compare_with_source_sheet.py` diffs every
(year, industry) row between the two. Result: **2,348 common rows, zero
numeric mismatches.** The only rows that exist in the sheet but not the CSV
(112 of them, mostly banks/insurers/thrifts in the mid-2000s) all share one
trait — their ROIC was unusable in the source itself that year (`NA`, or a
formula error like `#VALUE!`/`#DIV/0!`), so they were correctly excluded
rather than miscopied. A further 29 sheet rows were footer noise (aggregate
"Grand Total" lines, and a block of column-definition rows in 2019-2023) that
aren't industries at all. In short: the CSV is a faithful, if selectively
filtered, copy of its source — no corrections were needed. Re-run the audit
script (see its docstring) whenever the sheet is updated with a new year.

## Data-quality decisions (made in `src/clean_data.py`)

1. **Footer artifacts dropped.** A few rows (`"Variable definitions:"`,
   `"Unclassified"`) are copy-paste leakage from the source spreadsheet's
   footnotes, not real data.
2. **"Market" aggregate excluded from the industry set.** It only appears in
   4 of 25 years (2001, 2003, 2004, 2007) in the raw file, so it can't be
   plotted as a continuous benchmark line. It's preserved separately in
   `profit_pool_data.json`'s `market_benchmark` array in case those 4 points
   are useful as a reference later.
3. **Missing derived fields recomputed, not dropped** — e.g. 2025 Building
   Materials was missing `ROIC_minus_WACC_pct` and `Economic_Profit` even
   though ROIC/WACC/capital were present; recomputed from those.
4. **Likely data-entry outliers are flagged, not deleted or silently
   trusted.** Currently: one row (2003 Auto Parts, WACC = **−13.78%**) — a
   negative cost of capital is very unlikely to be genuine and should be
   checked against the original source — and ten industry-year rows with
   fewer than 3 firms in the sample (noisy by construction). The chart marks
   these with a dashed outline; they're included in all totals unless you
   check "Hide flagged data-quality rows."
5. **Industry names are *not* harmonized across the 25 years.** Damodaran's
   own taxonomy changed multiple times (e.g. `Bank` → `Banks (Regional)`,
   `Restaurant` → `Restaurant/Dining`) — of the 202 distinct industry labels
   that appear somewhere in 2001-2025, only a subset persist under an
   identical name across the whole period. This shows up most in the Trend
   view: an industry's line simply has gaps in the years it was filed under a
   different label. Building a name-crosswalk so a "lineage" can be tracked
   across renames is the natural v2 — see below. For v1 each label is its own
   series, which is also how Mauboussin's own exhibits treat profit pools
   (year-snapshots, not forced multi-year identity).
6. **Extreme outliers are shown at true scale, not clamped.** A handful of
   dot-com-bust-era rows are severe (2003 E-Commerce hits −276pp spread) —
   in Compare-years and Trend, the axis is sized to the selected years'/
   industry's own data (not the full 25-year cross-industry range), so a
   single extreme industry-year doesn't compress every other view into a
   sliver near zero. Flagged rows (see point 4) are still visually marked
   wherever they appear.
7. **Only industries still reported in 2025 are kept — retired labels are
   dropped entirely, not truncated.** Of the 202 labels in point 5, 112 have
   no row in 2025 (mostly the pre-2013 name for something that was later
   renamed, per point 5, plus a few — Bank (Money Center), Banks (Regional),
   Brokerage & Investment Banking, Financial Svcs. (Non-bank & Insurance) —
   that dropped out because their 2024/2025 ROIC is a source-file formula
   error, not a real disappearance). Rather than show these as series that
   stop partway through the chart, all 749 of their rows across every year
   are excluded, leaving 90 industries with 1,588 rows. Industries that
   *are* in 2025 keep every year they have data for, gaps and all — see
   `clean_data.py`'s step 5 to change the cutoff year or turn this off.

## Reproducing / updating the data

```bash
cd src
pip install -r ../requirements.txt
python3 clean_data.py     # data/*.csv -> docs/profit_pool_data.json
python3 export_slim.py    # docs/profit_pool_data.json -> docs/pp_slim.json
```

To add a new year once Damodaran publishes it, append the new rows to
`data/profit_pool_all_industries_2001-2025.csv` (same columns) and re-run both
scripts. Since the industry set is filtered to whatever's in the latest year
(point 7 above), adding a new year will also change which older industries
get dropped — check `docs/profit_pool_data.json`'s `notes` field after
re-running to see the new counts.

To re-verify the CSV against its source spreadsheet, see
`src/compare_with_source_sheet.py`'s docstring.

## Deploying the chart

**GitHub Pages:** Settings → Pages → deploy from the `docs/` folder on
`main`. The chart will be live at `https://amandeepdharwal23.github.io/Profit-Pool-US/`.

**Embedding in Webflow (Viability Check):** add an Embed element with:

```html
<iframe
  src="https://<user>.github.io/<repo>/"
  style="width:100%; border:0; height:900px;"
  loading="lazy"
  title="US industry profit pools, 2001-2025">
</iframe>
```

Adjust `height` to the chart's rendered height (check on mobile widths too —
the chart is responsive but the fixed iframe height isn't; consider posting a
`resize` message from the chart if this becomes a recurring embed pattern).

## Possible v2 work

- Industry-lineage crosswalk (point 5 above) so the Trend view can track one
  industry's trajectory across all 25 years instead of stopping at renamed
  labels.
- Sector roll-up (group ~90-200 industry buckets into ~10-12 broader sectors)
  as a less noisy alternative view.
- A written companion piece: which industries were durable profit pools
  across the full cycle vs. one-off winners of a single year.

## License

Code in this repo (MIT — add a LICENSE file with your name if you want this
public). The underlying data's license/attribution requirements depend on its
source — see "Data source" above before republishing it.
