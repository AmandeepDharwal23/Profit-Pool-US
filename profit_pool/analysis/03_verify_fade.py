"""Verification of outliers + the persistence/fade test (Mauboussin's core question)."""
import pandas as pd
import numpy as np

pd.set_option("display.width", 250)
df = pd.read_csv("panel.csv")
M = df[df.year >= 2014].copy()

print("=" * 100)
print("A. OUTLIER CHECKS — is this economics or a reclassification?")
print("=" * 100)
for ind in ["Software (Entertainment)", "Software (System & Application)", "Advertising",
            "Retail (General)", "Oil/Gas (Integrated)"]:
    g = M[M.ind == ind].sort_values("year")
    print(f"\n{ind}")
    print("  year : " + " ".join(f"{int(y):>7}" for y in g.year))
    print("  cap$bn:" + " ".join(f"{v:>7.0f}" for v in g.cap_bn))
    print("  firms :" + " ".join(f"{v:>7.0f}" for v in g.firms))
    print("  ROIC% :" + " ".join(f"{v:>7.1f}" for v in g.roic))
    print("  EP$bn :" + " ".join(f"{v:>7.0f}" for v in g.ep_bn))

print("\n" + "=" * 100)
print("B. IS THE POOL GETTING MORE CONCENTRATED?")
print("=" * 100)
print(f"{'Year':<6}{'created $bn':>13}{'destroyed $bn':>15}{'top5 %':>9}{'top10 %':>10}{'top20 %':>10}{'#creators':>11}{'#destroyers':>13}")
for y, g in M.groupby("year"):
    pos = g[g.ep_bn > 0].ep_bn
    neg = g[g.ep_bn < 0].ep_bn
    tot = pos.sum()
    print(f"{y:<6}{tot:>13,.0f}{neg.sum():>15,.0f}"
          f"{pos.nlargest(5).sum()/tot*100:>9.0f}{pos.nlargest(10).sum()/tot*100:>10.0f}"
          f"{pos.nlargest(20).sum()/tot*100:>10.0f}{len(pos):>11}{len(neg):>13}")

print("\n" + "=" * 100)
print("C. PERSISTENCE / FADE — do high spreads survive 5 years?")
print("=" * 100)
print("Sort industries into quintiles by spread in the base year, then look at")
print("the same industries' average spread 5 years later.\n")

for base in [2014, 2016, 2018, 2020]:
    later = base + 5
    b = M[M.year == base][["ind", "spread"]].rename(columns={"spread": "s0"})
    l = M[M.year == later][["ind", "spread"]].rename(columns={"spread": "s5"})
    j = b.merge(l, on="ind")
    if len(j) < 40:
        continue
    j["q"] = pd.qcut(j.s0, 5, labels=["Q1 low", "Q2", "Q3", "Q4", "Q5 high"])
    t = j.groupby("q", observed=True).agg(n=("ind", "size"), start=("s0", "mean"), after5=("s5", "mean"))
    t["change"] = t.after5 - t.start
    t["kept_%"] = (t.after5 / t.start * 100).where(t.start > 0)
    print(f"{base} -> {later}")
    print(t.round(1).to_string())
    print()

# how much of top-quintile stays top-quintile
print("Top-quintile retention (share of the top-20% spread group still in the top 20% five years on):")
for base in [2014, 2016, 2018, 2020]:
    later = base + 5
    b = M[M.year == base][["ind", "spread"]].rename(columns={"spread": "s0"})
    l = M[M.year == later][["ind", "spread"]].rename(columns={"spread": "s5"})
    j = b.merge(l, on="ind")
    if len(j) < 40:
        continue
    top0 = set(j.nlargest(int(len(j) * .2), "s0").ind)
    top5 = set(j.nlargest(int(len(j) * .2), "s5").ind)
    print(f"  {base}->{later}: {len(top0 & top5)}/{len(top0)} = {len(top0&top5)/len(top0)*100:.0f}%")

print("\n" + "=" * 100)
print("D. THE SPREAD-vs-DOLLARS DISCONNECT")
print("=" * 100)
c = M[M.year == 2025].copy()
c["cap_per_firm"] = c.cap_bn / c.firms
hi = c.nlargest(12, "spread")[["ind", "spread", "ep_bn", "cap_bn", "firms", "cap_per_firm"]]
print("\nHighest spread industries 2025 — note how small some dollar pools are:")
print(hi.round(2).to_string(index=False))
print(f"\nCorrelation between spread(pp) and dollar economic profit: {c.spread.corr(c.ep_bn):.2f}")
print(f"Correlation between invested capital and dollar economic profit: {c.cap_bn.corr(c.ep_bn):.2f}")
print(f"Median capital per firm, top-10-spread industries: ${hi.cap_per_firm.median()*1000:,.0f}mn")
print(f"Median capital per firm, top-10-dollar-pool industries: "
      f"${(c.nlargest(10,'ep_bn').cap_bn/c.nlargest(10,'ep_bn').firms).median()*1000:,.0f}mn")
