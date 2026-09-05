"""Flag reclassification discontinuities, then build clean 'best' and 'improving' screens."""
import pandas as pd
import numpy as np

pd.set_option("display.width", 250)
df = pd.read_csv("panel.csv")
M = df[df.year >= 2014].copy()
R = pd.read_csv("industry_metrics.csv")

# ---- detect bucket discontinuities (reclassification fingerprints) ----
flags = []
for ind, g in M.groupby("ind"):
    g = g.sort_values("year")
    fc = g.firms.pct_change().abs() * 100
    cc = g.cap_bn.pct_change().abs() * 100
    bad_years = g.year[(fc > 40) | (cc > 100)].tolist()
    flags.append(dict(ind=ind, reclass_years=bad_years, reclassified=len(bad_years) > 0))
F = pd.DataFrame(flags)
R = R.merge(F, on="ind", how="left")

print("=" * 100)
print("RECLASSIFICATION SCREEN — buckets whose firm count or capital jumped discontinuously")
print("=" * 100)
rc = R[R.reclassified].sort_values("ep25", ascending=False)
print(f"{len(rc)} of {len(R)} industries show at least one discontinuity:\n")
print(rc[["ind", "reclass_years", "ep25", "cap25", "d_spread"]].head(20).to_string(index=False))

# ---- aggregate decomposition: pool growth from capital vs from spread ----
print("\n" + "=" * 100)
print("WHY THE POOL GREW, 2014 -> 2025")
print("=" * 100)
a14, a25 = M[M.year == 2014], M[M.year == 2025]
cap14, cap25 = a14.cap_bn.sum(), a25.cap_bn.sum()
ep14, ep25 = a14.ep_bn.sum(), a25.ep_bn.sum()
sp14, sp25 = ep14 / cap14 * 100, ep25 / cap25 * 100
print(f"  invested capital : ${cap14:,.0f}bn -> ${cap25:,.0f}bn  ({cap25/cap14-1:+.0%})")
print(f"  aggregate spread : {sp14:.2f}pp -> {sp25:.2f}pp  ({sp25-sp14:+.2f}pp)")
print(f"  economic profit  : ${ep14:,.0f}bn -> ${ep25:,.0f}bn  ({ep25/ep14-1:+.0%})")
print(f"\n  Of the ${ep25-ep14:,.0f}bn increase in economic profit:")
print(f"    from deploying more capital at the old spread : ${(cap25-cap14)*sp14/100:,.0f}bn")
print(f"    from a wider spread on the old capital        : ${cap14*(sp25-sp14)/100:,.0f}bn")
print(f"    interaction                                    : ${(cap25-cap14)*(sp25-sp14)/100:,.0f}bn")

# ---- concentration excluding the two big reclassified buckets ----
print("\nConcentration check, excluding the two reclassified mega-buckets")
print("(Software (Entertainment) jumped 13->92 firms in 2018; Retail (General) 15->26 in 2023)")
excl = ["Software (Entertainment)", "Retail (General)"]
print(f"{'Year':<6}{'top5 % (all)':>14}{'top5 % (ex-reclass)':>22}")
for y, g in M.groupby("year"):
    p = g[g.ep_bn > 0]
    pe = p[~p.ind.isin(excl)]
    print(f"{y:<6}{p.ep_bn.nlargest(5).sum()/p.ep_bn.sum()*100:>14.0f}"
          f"{pe.ep_bn.nlargest(5).sum()/pe.ep_bn.sum()*100:>22.0f}")

# ---- CLEAN SCREENS ----
print("\n" + "=" * 100)
print("SCREEN 1 — BEST: durable, material, clean")
print("=" * 100)
best = R[(R.hit >= 90) & (R.med_spread >= 8) & (R.ep25 >= 5) & (~R.reclassified)]
best = best.sort_values("ep25", ascending=False)
print("(positive spread in >=90% of years, median spread >=8pp, 2025 pool >=$5bn, no reclassification)\n")
print(best[["ind", "ep25", "spread25", "med_spread", "min_spread", "sd_spread", "hit",
            "cap25", "firms25", "d_spread"]].round(2).to_string(index=False))

print("\n" + "=" * 100)
print("SCREEN 2 — GETTING BETTER: improving AND durable (not a commodity bounce)")
print("=" * 100)
imp = R[(R.d_spread > 2) & (R.hit >= 80) & (R.ep25 >= 3) & (~R.reclassified)]
imp = imp.sort_values("d_spread", ascending=False)
print("(spread up >2pp, positive in >=80% of years, 2025 pool >=$3bn, no reclassification)\n")
print(imp[["ind", "spread_e", "spread_l", "d_spread", "d_roic", "d_wacc", "ep_e", "ep_l",
           "cap_growth", "hit", "ep25"]].round(2).to_string(index=False))

print("\n" + "=" * 100)
print("SCREEN 3 — CYCLICAL REBOUNDS (improving, but low hit rate = mean reversion risk)")
print("=" * 100)
cyc = R[(R.d_spread > 5) & (R.hit < 80)].sort_values("d_spread", ascending=False)
print(cyc[["ind", "spread_e", "spread_l", "d_spread", "hit", "min_spread", "spread25", "ep25"]].round(2).to_string(index=False))

print("\n" + "=" * 100)
print("SCREEN 4 — DETERIORATING: durable history but spread eroding")
print("=" * 100)
det = R[(R.d_spread < -3) & (R.hit >= 80)].sort_values("d_spread")
print(det[["ind", "spread_e", "spread_l", "d_spread", "d_roic", "d_wacc", "spread25", "ep25", "cap_growth"]].round(2).to_string(index=False))

R.to_csv("industry_metrics_flagged.csv", index=False)
