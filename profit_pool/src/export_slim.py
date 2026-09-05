"""
Produce docs/pp_slim.json from docs/profit_pool_data.json (the output of
clean_data.py). This is a separate step so the chart's payload only carries
the fields it actually renders, keeping docs/index.html's fetch small.

Field name key (short keys keep the JSON compact -- this repo's the only
place that needs to know the mapping):
    y      Year
    i      Industry
    n      NumFirms
    roic   ROIC_pct
    wacc   WACC_pct
    spread ROIC_minus_WACC_pct
    cap    Invested_Capital_USD_mn
    ep     Economic_Profit_USD_mn
    fw     flag_negative_wacc  (bool)
    ft     flag_thin_sample    (bool, NumFirms < 3)

Also passes through a small `notes` object (flag counts, how many industries/
rows the 2025-presence filter dropped) so the chart's data-quality copy can
read real numbers instead of a hand-typed sentence going stale.

Run after clean_data.py:
    cd src && python3 clean_data.py && python3 export_slim.py
"""
import json

SRC = "../docs/profit_pool_data.json"
OUT = "../docs/pp_slim.json"

def main():
    with open(SRC) as f:
        d = json.load(f)

    slim = [{
        "y": r["Year"], "i": r["Industry"], "n": r["NumFirms"],
        "roic": r["ROIC_pct"], "wacc": r["WACC_pct"], "spread": r["ROIC_minus_WACC_pct"],
        "cap": r["Invested_Capital_USD_mn"], "ep": r["Economic_Profit_USD_mn"],
        "fw": r["flag_negative_wacc"], "ft": r["flag_thin_sample"],
    } for r in d["records"]]

    notes = d.get("notes", {})
    out = {
        "years": d["years"],
        "industries": d["industries"],
        "records": slim,
        "notes": {
            "flagged_negative_wacc": notes.get("flagged_negative_wacc"),
            "flagged_thin_sample": notes.get("flagged_thin_sample"),
            "industries_dropped_not_in_2025": len(notes.get("industries_dropped_not_in_2025", [])),
            "rows_dropped_not_in_2025": notes.get("rows_dropped_not_in_2025"),
        },
    }
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))

    print(f"Wrote {OUT}: {len(slim)} records ({sum(len(json.dumps(r)) for r in slim)} bytes of record data)")

if __name__ == "__main__":
    main()
