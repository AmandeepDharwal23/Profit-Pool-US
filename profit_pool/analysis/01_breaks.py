"""Detect and size the structural breaks in the ROIC/invested-capital series."""
import json
import pandas as pd
import numpy as np

d = json.load(open("../docs/profit_pool_data.json"))
df = pd.DataFrame(d["records"])
df = df.rename(columns={
    "ROIC_pct": "roic", "WACC_pct": "wacc", "ROIC_minus_WACC_pct": "spread",
    "Invested_Capital_USD_mn": "cap_mn", "Economic_Profit_USD_mn": "ep_mn",
    "NumFirms": "firms", "Year": "year", "Industry": "ind",
})
df["cap_bn"] = df.cap_mn / 1000
df["ep_bn"] = df.ep_mn / 1000

print(f"Universe: {df.ind.nunique()} industries, {df.year.nunique()} years, {len(df)} rows\n")

# --- Year-over-year churn per industry: a definitional change moves EVERYTHING at once ---
piv_cap = df.pivot_table(index="year", columns="ind", values="cap_mn")
piv_roic = df.pivot_table(index="year", columns="ind", values="roic")

cap_chg = piv_cap.pct_change() * 100
roic_chg = piv_roic.diff()

print("How much the whole cross-section moves each year")
print("(median |capital change| and median |ROIC change| across all industries;")
print(" a spike = every industry moved at once = definition change, not economics)\n")
print(f"{'Year':<6}{'med |cap chg| %':>16}{'% inds >50% cap chg':>22}{'med |ROIC chg| pp':>20}")
for y in sorted(piv_cap.index)[1:]:
    cc = cap_chg.loc[y].dropna()
    rc = roic_chg.loc[y].dropna()
    if len(cc) < 10:
        continue
    big = (cc.abs() > 50).mean() * 100
    print(f"{y:<6}{cc.abs().median():>16.1f}{big:>22.0f}{rc.abs().median():>20.2f}")

# --- Aggregate (capital-weighted) picture by year ---
print("\n\nAggregate profit pool by year (all industries in the filtered universe)")
print(f"{'Year':<6}{'Capital $bn':>14}{'EconProfit $bn':>16}{'Agg ROIC %':>12}{'Agg WACC %':>12}{'Agg spread pp':>14}{'#creators':>11}{'#inds':>7}")
agg_rows = []
for y, g in df.groupby("year"):
    cap = g.cap_mn.sum()
    ep = g.ep_mn.sum()
    # capital-weighted ROIC and WACC
    roic_w = (g.roic * g.cap_mn).sum() / cap
    wacc_w = (g.wacc * g.cap_mn).sum() / cap
    creators = (g.spread > 0).sum()
    agg_rows.append(dict(year=y, cap_bn=cap/1000, ep_bn=ep/1000, roic=roic_w, wacc=wacc_w,
                         spread=roic_w - wacc_w, creators=creators, n=len(g)))
    print(f"{y:<6}{cap/1000:>14,.0f}{ep/1000:>16,.0f}{roic_w:>12.2f}{wacc_w:>12.2f}{roic_w-wacc_w:>14.2f}{creators:>11}{len(g):>7}")

pd.DataFrame(agg_rows).to_csv("agg_by_year.csv", index=False)
df.to_csv("panel.csv", index=False)
print("\nSaved analysis/agg_by_year.csv and analysis/panel.csv")
