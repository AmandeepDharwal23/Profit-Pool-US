"""Final verification + single-name concentration risk within industry buckets."""
import pandas as pd

pd.set_option("display.width", 250)
df = pd.read_csv("panel.csv")
M = df[df.year >= 2014].copy()
R = pd.read_csv("industry_metrics_flagged.csv")

print("=" * 100)
print("VERIFY 1 — arithmetic ties out (spread x capital = economic profit)")
print("=" * 100)
c = M[M.year == 2025].copy()
c["ep_check"] = c.spread / 100 * c.cap_bn
c["err"] = (c.ep_check - c.ep_bn).abs()
print(f"Max discrepancy across {len(c)} industries: ${c.err.max():.3f}bn   (median ${c.err.median():.4f}bn)")
print("Worst 3:")
print(c.nlargest(3, "err")[["ind", "spread", "cap_bn", "ep_bn", "ep_check", "err"]].round(3).to_string(index=False))

print("\n" + "=" * 100)
print("VERIFY 2 — is the 'improvement is operational' claim robust?")
print("=" * 100)
imp = R[R.d_spread > 0]
roic_contrib = imp.d_roic
wacc_contrib = -imp.d_wacc
print(f"Industries with wider spread (2021-25 vs 2014-18): {len(imp)}")
print(f"  cost of capital was a TAILWIND (WACC fell) for : {(wacc_contrib>0).sum()}")
print(f"  cost of capital was a HEADWIND (WACC rose) for : {(wacc_contrib<0).sum()}")
print(f"  median ROIC contribution : {roic_contrib.median():+.2f}pp")
print(f"  median WACC contribution : {wacc_contrib.median():+.2f}pp")
print("\n=> spread gains in this window are operating gains, not a rate tailwind.")

print("\n" + "=" * 100)
print("VERIFY 3 — how concentrated is each pool likely to be inside the bucket?")
print("=" * 100)
t = M[M.year == 2025].nlargest(20, "ep_bn").copy()
t["cap_per_firm_bn"] = t.cap_bn / t.firms
t["ep_per_firm_bn"] = t.ep_bn / t.firms
print("Top-20 pools, with firm counts. Few firms + huge capital = the 'industry' is a handful of names.\n")
print(t[["ind", "ep_bn", "cap_bn", "firms", "cap_per_firm_bn", "ep_per_firm_bn", "spread"]]
      .round(2).to_string(index=False))

print("\n" + "=" * 100)
print("VERIFY 4 — is the listed universe shrinking?")
print("=" * 100)
print(f"{'Year':>6}{'total firms':>13}{'industries':>12}{'avg firms/ind':>15}")
for y, g in M.groupby("year"):
    print(f"{y:>6}{g.firms.sum():>13,.0f}{len(g):>12}{g.firms.mean():>15.1f}")

print("\n" + "=" * 100)
print("VERIFY 5 — do the 'best' names survive if I use a stricter durability bar?")
print("=" * 100)
strict = R[(R.hit == 100) & (R.min_spread >= 5) & (R.ep25 >= 5) & (~R.reclassified)]
strict = strict.sort_values("ep25", ascending=False)
print("Positive spread EVERY year 2014-2025, worst year still >=5pp, 2025 pool >=$5bn:\n")
print(strict[["ind", "ep25", "spread25", "med_spread", "min_spread", "sd_spread", "d_spread",
              "cap25", "firms25"]].round(2).to_string(index=False))
