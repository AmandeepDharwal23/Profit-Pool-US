"""
Core profit-pool analysis on the reliable window (2014-2025).

Why 2014-2025: Damodaran's ROIC/invested-capital definition changed twice
(2013 = operating leases capitalised, 2014 = R&D capitalised as well), and the
2001-2005 tabs alternate between two different aggregation bases (capital
sawtooths ~2x every other year with firm counts flat). 2014-2025 is one
consistent definition with full industry coverage (88-90 industries/yr).
"""
import pandas as pd
import numpy as np

pd.set_option("display.width", 250)
df = pd.read_csv("panel.csv")
M = df[df.year >= 2014].copy()          # modern, comparable regime

EARLY = [2014, 2015, 2016, 2017, 2018]  # pre-COVID, ZIRP-ish
LATE = [2021, 2022, 2023, 2024, 2025]   # post-COVID, rate shock + recovery

rows = []
for ind, g in M.groupby("ind"):
    g = g.sort_values("year")
    yrs = len(g)
    pos = (g.spread > 0).sum()
    cur = g[g.year == 2025]
    if cur.empty:
        continue
    cur = cur.iloc[0]

    e = g[g.year.isin(EARLY)]
    l = g[g.year.isin(LATE)]
    if len(e) < 3 or len(l) < 3:
        continue

    cap14 = g[g.year == 2014].cap_bn
    cap14 = cap14.iloc[0] if len(cap14) else np.nan

    # rate-shock test: spread held through the 2022 WACC spike?
    s21 = g[g.year == 2021].spread
    s22 = g[g.year == 2022].spread
    shock = (s22.iloc[0] - s21.iloc[0]) if (len(s21) and len(s22)) else np.nan

    rows.append(dict(
        ind=ind,
        yrs=yrs, hit=pos / yrs * 100,
        med_spread=g.spread.median(), min_spread=g.spread.min(), sd_spread=g.spread.std(),
        spread25=cur.spread, roic25=cur.roic, wacc25=cur.wacc,
        ep25=cur.ep_bn, cap25=cur.cap_bn, firms25=cur.firms,
        spread_e=e.spread.mean(), spread_l=l.spread.mean(),
        roic_e=e.roic.mean(), roic_l=l.roic.mean(),
        wacc_e=e.wacc.mean(), wacc_l=l.wacc.mean(),
        ep_e=e.ep_bn.mean(), ep_l=l.ep_bn.mean(),
        cap_e=e.cap_bn.mean(), cap_l=l.cap_bn.mean(),
        cap14=cap14, shock22=shock,
    ))

R = pd.DataFrame(rows)
R["d_spread"] = R.spread_l - R.spread_e
R["d_roic"] = R.roic_l - R.roic_e
R["d_wacc"] = R.wacc_l - R.wacc_e
R["d_ep"] = R.ep_l - R.ep_e
R["cap_growth"] = (R.cap_l / R.cap_e - 1) * 100
R["cap_per_firm"] = R.cap25 / R.firms25 * 1000  # $mn per firm
R.to_csv("industry_metrics.csv", index=False)

def show(d, cols, n=None, title=""):
    if title:
        print("\n" + title)
        print("-" * len(title))
    print(d[cols].head(n if n else len(d)).to_string(index=False))

# ============================================================
print("=" * 100)
print("1. THE 2025 PROFIT POOL — WHERE THE DOLLARS ARE")
print("=" * 100)
tot_pos = R[R.ep25 > 0].ep25.sum()
tot_neg = R[R.ep25 < 0].ep25.sum()
print(f"\nTotal economic profit created: ${tot_pos:,.0f}bn across {(R.ep25>0).sum()} industries")
print(f"Total economic profit destroyed: ${tot_neg:,.0f}bn across {(R.ep25<0).sum()} industries")
print(f"Net: ${R.ep25.sum():,.0f}bn on ${R.cap25.sum():,.0f}bn of invested capital")

top = R.nlargest(15, "ep25")
top = top.assign(share=lambda x: x.ep25 / tot_pos * 100)
show(top, ["ind", "ep25", "share", "spread25", "roic25", "wacc25", "cap25", "firms25"],
     title="Top 15 by dollar economic profit, 2025 ($bn, spread in pp)")

print(f"\nConcentration: top 5 = {R.nlargest(5,'ep25').ep25.sum()/tot_pos*100:.0f}% of all economic profit created")
print(f"               top 10 = {R.nlargest(10,'ep25').ep25.sum()/tot_pos*100:.0f}%")
print(f"               top 20 = {R.nlargest(20,'ep25').ep25.sum()/tot_pos*100:.0f}%")

show(R.nsmallest(10, "ep25"), ["ind", "ep25", "spread25", "roic25", "wacc25", "cap25", "firms25"],
     title="Biggest value destroyers, 2025 ($bn)")

# ============================================================
print("\n" + "=" * 100)
print("2. BEST — DURABLE HIGH RETURNS (2014-2025)")
print("=" * 100)
durable = R[(R.hit >= 90) & (R.med_spread >= 5)].sort_values("med_spread", ascending=False)
show(durable, ["ind", "hit", "med_spread", "min_spread", "sd_spread", "spread25", "ep25", "cap25", "firms25"],
     title=f"Never (or almost never) destroyed value, median spread >=5pp  [{len(durable)} industries]")

# ============================================================
print("\n" + "=" * 100)
print("3. GETTING BETTER — SPREAD MOMENTUM (2021-25 avg vs 2014-18 avg)")
print("=" * 100)
imp = R.nlargest(15, "d_spread")
show(imp, ["ind", "spread_e", "spread_l", "d_spread", "d_roic", "d_wacc", "d_ep", "cap_growth"],
     title="Most improved spread (pp), with driver split")
det = R.nsmallest(15, "d_spread")
show(det, ["ind", "spread_e", "spread_l", "d_spread", "d_roic", "d_wacc", "d_ep", "cap_growth"],
     title="Most deteriorated spread (pp)")

# ============================================================
print("\n" + "=" * 100)
print("4. WHAT ACTUALLY DRIVES THE CHANGE — ROIC vs COST OF CAPITAL")
print("=" * 100)
print(f"\nAcross all {len(R)} industries, 2014-18 avg -> 2021-25 avg:")
print(f"  mean change in ROIC : {R.d_roic.mean():+.2f}pp   (median {R.d_roic.median():+.2f})")
print(f"  mean change in WACC : {R.d_wacc.mean():+.2f}pp   (median {R.d_wacc.median():+.2f})")
print(f"  mean change in spread: {R.d_spread.mean():+.2f}pp  (median {R.d_spread.median():+.2f})")
imp_only = R[R.d_spread > 0]
roic_led = (imp_only.d_roic > -imp_only.d_wacc).sum()
print(f"\nOf the {len(imp_only)} industries whose spread improved, {roic_led} improved mainly on ROIC")
print(f"and {len(imp_only)-roic_led} mainly because their cost of capital fell.")

# ============================================================
print("\n" + "=" * 100)
print("5. THE 2022 RATE SHOCK — WHOSE SPREAD SURVIVED IT")
print("=" * 100)
print("Aggregate cost of capital jumped from 5.35% (2021) to 9.11% (2022).")
sh = R.dropna(subset=["shock22"])
print(f"Median spread change 2021->2022: {sh.shock22.median():+.1f}pp")
show(sh.nlargest(12, "shock22"), ["ind", "shock22", "spread25", "med_spread", "hit"],
     title="Held up best through the shock (spread change 2021->2022, pp)")
show(sh.nsmallest(12, "shock22"), ["ind", "shock22", "spread25", "med_spread", "hit"],
     title="Hit hardest by the shock")

# ============================================================
print("\n" + "=" * 100)
print("6. GROWING THE POOL — SPREAD *AND* CAPITAL (compounding machines)")
print("=" * 100)
comp = R[(R.spread_l > 0) & (R.cap_growth > 0)].copy()
comp["ep_added"] = comp.d_ep
show(comp.nlargest(15, "ep_added"),
     ["ind", "ep_e", "ep_l", "d_ep", "spread_e", "spread_l", "d_spread", "cap_growth", "cap25"],
     title="Biggest increase in dollar economic profit ($bn), positive spread + growing capital")
