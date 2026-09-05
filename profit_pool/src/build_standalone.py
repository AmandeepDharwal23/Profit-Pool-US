"""
Build a single self-contained HTML file from docs/index.html + docs/pp_slim.json,
for hosting somewhere that can't serve two files together (e.g. Claude's
Artifact publisher). GitHub Pages doesn't need this -- it serves docs/index.html
and docs/pp_slim.json side by side directly, which is the normal/preferred path.

Usage:
    cd src && python3 build_standalone.py
Produces docs/standalone.html (embeds the data inline, no fetch() call).
"""
import json

INDEX = "../docs/index.html"
DATA = "../docs/pp_slim.json"
OUT = "../docs/standalone.html"

FETCH_BLOCK_OLD = '''<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<script>
(async function () {
  const DATA_URL = "pp_slim.json";
  let DATA;
  try {
    const res = await fetch(DATA_URL);
    DATA = await res.json();
  } catch (e) {
    document.getElementById("chart-holder").innerHTML =
      '<div class="empty-state">Could not load pp_slim.json (must be served from the same folder, e.g. via GitHub Pages or a local server -- opening this file directly with file:// will fail).</div>';
    return;'''

FETCH_BLOCK_NEW = '''<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<script type="application/json" id="pp-data-json">
{data}
</script>
<script>
(function () {{
  let DATA;
  try {{
    DATA = JSON.parse(document.getElementById("pp-data-json").textContent);
  }} catch (e) {{
    document.getElementById("chart-holder").innerHTML =
      '<div class="empty-state">Could not parse embedded profit-pool data.</div>';
    return;'''

def main():
    with open(INDEX, encoding="utf-8") as f:
        html = f.read()
    with open(DATA, encoding="utf-8") as f:
        data = f.read()

    if FETCH_BLOCK_OLD not in html:
        raise SystemExit("docs/index.html's data-loading block doesn't match what this script expects -- "
                          "it was probably edited. Update FETCH_BLOCK_OLD in this script to match.")

    html = html.replace(FETCH_BLOCK_OLD, FETCH_BLOCK_NEW.format(data=data))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT} ({len(html)} bytes, data embedded inline)")

if __name__ == "__main__":
    main()
