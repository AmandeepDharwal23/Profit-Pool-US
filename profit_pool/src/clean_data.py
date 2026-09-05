"""
Clean the raw profit-pool CSV (source: user-compiled from NYU Stern / Damodaran
industry ROIC-WACC-Invested Capital data, 2001-2025) and export a JSON the
chart can consume.

Data-quality decisions made here (documented in README.md too):
  1. Drop footer/parsing artifacts ("Variable definitions:" rows) that leaked
     into the CSV from the source spreadsheet's footnotes.
  2. Drop the "Market" aggregate row. It's present in only 4 of 25 years
     (2001, 2003, 2004, 2007) -- not a consistent time series -- so it can't
     be plotted as a trend and is excluded from the industry set. (It's kept
     in a separate `market_benchmark` array in the output in case it's useful
     as a reference line for those 4 years.)
  3. Recompute ROIC_minus_WACC_pct / Economic_Profit where present-but-null
     (e.g. 2025 Building Materials) from ROIC_pct - WACC_pct and Invested
     Capital, rather than dropping the row.
  4. Flag (not drop) rows that are likely data-entry outliers so the chart
     can visually mark them instead of silently hiding or silently trusting
     them:
       - WACC_pct < 0 (cost of capital is essentially never negative)
       - NumFirms < 3 (single/near-single-company "industries" are noise)
     Currently this flags 2003 Auto Parts (WACC -13.78%) and a few 1-firm
     "Other" buckets. These should be double-checked against Damodaran's
     original published file before being trusted in a public post.
  5. Industry names are NOT harmonized across years. Damodaran's own industry
     taxonomy changed multiple times over 2001-2025 (e.g. "Bank" -> "Banks
     (Regional)", "Restaurant" -> "Restaurant/Dining"). Forcing a single
     23-year name mapping would require judgment calls about which buckets
     are truly continuous; that crosswalk is left as a v2 task (see README).
     For v1, each year is treated as its own cross-section, which is also
     how Mauboussin's own exhibits treat profit pools (year-snapshots, not
     forced multi-year identity).
  6. Only industries present in the latest year (2025) are kept. A label
     that appears in earlier years but has no row in 2025 -- because its
     ROIC couldn't be computed that year, it was retired/merged into another
     bucket, or it's a source-file gap -- is dropped across ALL years rather
     than kept as a fragment that stops partway through the chart. Industries
     that ARE in 2025 keep every year they have data for, including gaps
     (see point 5 above for why gaps exist).
"""
import pandas as pd
import json
import sys

SRC = "../data/profit_pool_all_industries_2001-2025.csv"
OUT = "../docs/profit_pool_data.json"

# Definitional regimes in the source data. Damodaran changed how ROIC and
# invested capital are computed twice, and the 2003-2005 tabs use an
# aggregation basis that alternates year to year (capital roughly doubles and
# halves with firm counts flat). Verified two ways: the margin column header
# changes in the source workbook, and the cross-section moves as one -- in
# 2004, 89% of industries changed invested capital by more than 50%; in 2013,
# 51% did. Within a regime the numbers are comparable; across one they are not.
REGIMES = [
    {"from": 2001, "to": 2002, "label": "EBIT / book capital", "short": "EBIT basis",
     "note": "Returns unadjusted for leases or R&D.", "reliable": True},
    {"from": 2003, "to": 2005, "label": "Inconsistent source basis", "short": "unreliable",
     "note": "Invested capital alternates between two bases year to year while firm counts stay flat. Not comparable in either direction.",
     "reliable": False},
    {"from": 2006, "to": 2012, "label": "EBIT / book capital", "short": "EBIT basis",
     "note": "Returns unadjusted for leases or R&D. Internally consistent -- the only clean read on the financial crisis.",
     "reliable": True},
    {"from": 2013, "to": 2013, "label": "Transition: leases capitalised", "short": "leases",
     "note": "Operating leases moved into invested capital. Levels jump against both neighbours.",
     "reliable": False},
    {"from": 2014, "to": 2025, "label": "Lease + R&D adjusted", "short": "lease + R&D",
     "note": "Leases and R&D both capitalised. The current definition.", "reliable": True},
]

def main():
    df = pd.read_csv(SRC)

    # 1. drop footer artifacts
    df = df[~df.Industry.astype(str).str.contains(":", na=False)]
    df = df[df.Industry != "Unclassified"]

    # 2. split out Market rows
    market = df[df.Industry == "Market"].copy()
    df = df[df.Industry != "Market"].copy()

    # 3. recompute missing derived fields
    need_spread = df.ROIC_minus_WACC_pct.isna() & df.ROIC_pct.notna() & df.WACC_pct.notna()
    df.loc[need_spread, "ROIC_minus_WACC_pct"] = (
        df.loc[need_spread, "ROIC_pct"] - df.loc[need_spread, "WACC_pct"]
    ).round(2)

    need_ep = df.Economic_Profit_USD_mn.isna() & df.ROIC_minus_WACC_pct.notna() & df.Invested_Capital_USD_mn.notna()
    df.loc[need_ep, "Economic_Profit_USD_mn"] = (
        df.loc[need_ep, "ROIC_minus_WACC_pct"] / 100 * df.loc[need_ep, "Invested_Capital_USD_mn"]
    ).round(1)
    df.loc[need_ep, "Economic_Profit_USD_bn"] = (df.loc[need_ep, "Economic_Profit_USD_mn"] / 1000).round(3)

    # drop any row still missing core fields after recompute
    before = len(df)
    df = df.dropna(subset=["ROIC_pct", "WACC_pct", "ROIC_minus_WACC_pct", "Invested_Capital_USD_mn", "Economic_Profit_USD_mn"])
    dropped = before - len(df)

    # 5. MARK (don't drop) industries still reported in the latest year.
    # This used to delete every row of any industry missing from 2025, which
    # quietly gutted the historical cross-sections -- a 2008 snapshot was left
    # with 38 of that year's 92 industries holding only ~34% of its invested
    # capital. Cross-sections (Snapshot, Compare) compare industries *within* a
    # single year and never need cross-year name continuity, so they should see
    # every industry that existed that year. Only the Trend view needs the
    # restriction, to avoid lines that stop dead where a label was renamed.
    # The chart applies the flag per view.
    latest_year = df.Year.max()
    industries_in_latest = set(df.loc[df.Year == latest_year, "Industry"].unique())
    df["trend_eligible"] = df.Industry.isin(industries_in_latest)
    not_in_latest = sorted(set(df.Industry.unique()) - industries_in_latest)

    # 6. flag likely outliers (do not drop)
    df["flag_negative_wacc"] = df.WACC_pct < 0
    df["flag_thin_sample"] = df.NumFirms < 3

    records = df.to_dict(orient="records")
    market_records = market.to_dict(orient="records")

    years = sorted(df.Year.unique().tolist())
    industries = sorted(df.Industry.unique().tolist())

    out = {
        "generated_from": SRC,
        "years": years,
        "industries": industries,
        "records": records,
        "market_benchmark": market_records,
        "regimes": REGIMES,
        "notes": {
            "rows_after_clean": len(df),
            "rows_dropped_unrecoverable": int(dropped),
            "industries_not_in_latest_year": not_in_latest,
            "rows_not_trend_eligible": int((~df.trend_eligible).sum()),
            "flagged_negative_wacc": int(df.flag_negative_wacc.sum()),
            "flagged_thin_sample": int(df.flag_thin_sample.sum()),
        },
    }

    with open(OUT, "w") as f:
        json.dump(out, f)

    print(f"Wrote {OUT}: {len(records)} records, {len(years)} years, {len(industries)} distinct industry labels")
    print(f"Dropped {dropped} unrecoverable rows.")
    print(f"{len(not_in_latest)} industries have no {latest_year} row and are marked trend-ineligible "
          f"({(~df.trend_eligible).sum()} rows) -- still shown in cross-section views.")
    print(f"Flagged {out['notes']['flagged_negative_wacc']} negative-WACC rows, "
          f"{out['notes']['flagged_thin_sample']} thin-sample (<3 firm) rows")

if __name__ == "__main__":
    main()
