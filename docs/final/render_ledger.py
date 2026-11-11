"""Render the system architecture as a technical schematic.

The design direction is a bank operations schematic: flat component blocks,
one oxblood flow spine through the build stages, table and page glyphs, a
persisted-artifacts shelf, and audit flags for the validation gates.

The HTML is written to a temp file and captured with headless Chrome at
1600x900 CSS px and 1.5x device scale, giving a 2400x1350 PNG.

Run with: venv\\Scripts\\python.exe docs\\final\\render_ledger.py
"""
from __future__ import annotations

import html
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "final" / "images" / "architecture"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

PAPER = "#eef0e9"
PANEL = "#e7ebe2"
INK = "#171a17"
MUTED = "#5f665f"
RULE = "#c9cec4"
OXBLOOD = "#8e2f2f"
GREEN = "#2f6b4f"


def esc(text: object) -> str:
    return html.escape(str(text), quote=False)


def table_glyph() -> str:
    return """<svg width="14" height="12" viewBox="0 0 14 12" fill="none"
      stroke="currentColor" stroke-width="1">
      <rect x="0.5" y="0.5" width="13" height="11"/>
      <line x1="1" y1="4" x2="13" y2="4"/>
      <line x1="1" y1="7.5" x2="13" y2="7.5"/>
    </svg>"""


def page_glyph() -> str:
    return """<svg width="12" height="14" viewBox="0 0 12 14" fill="none"
      stroke="currentColor" stroke-width="1">
      <rect x="0.5" y="0.5" width="11" height="13"/>
      <line x1="3" y1="4" x2="9" y2="4"/>
      <line x1="3" y1="7" x2="9" y2="7"/>
      <line x1="3" y1="10" x2="7" y2="10"/>
    </svg>"""


def source_row(name: str, rows: str, fields: str) -> str:
    return f"""
      <div class="source">
        <div class="glyph">{table_glyph()}</div>
        <div class="source-main">
          <div class="name">{esc(name)}</div>
          <div class="fields">{esc(fields)}</div>
        </div>
        <div class="rows">{esc(rows)}</div>
      </div>"""


def page_row(num: str, name: str, sub: str) -> str:
    return f"""
      <div class="page-row">
        <div class="glyph">{page_glyph()}</div>
        <div class="page-main">
          <div class="pname">{esc(name)}</div>
          <div class="psub">{esc(sub)}</div>
        </div>
        <div class="pnum">{esc(num)}</div>
      </div>"""


def build_block(
    left: int,
    num: str,
    tag: str,
    title: str,
    command: str,
    source: str,
    output: str,
    audit: str,
    stat: str,
    stat_label: str,
    gate: str,
) -> str:
    return f"""
      <div class="block" style="left:{left}px">
        <div class="block-head"><span class="stage-no">{esc(num)}</span><span class="stage-tag">{esc(tag)}</span></div>
        <div class="block-body">
          <div class="block-title">{esc(title)}</div>
          <div class="block-cmd">{esc(command)}</div>
          <div class="block-rule"></div>
          <div class="io"><span class="k">in</span><span class="v">{esc(source)}</span></div>
          <div class="io out"><span class="k">out</span><span class="v">{esc(output)}</span></div>
          <div class="audit">{esc(audit)}</div>
          <div class="stat"><span class="stat-no">{esc(stat)}</span><span class="stat-label">{esc(stat_label)}</span></div>
        </div>
        <div class="gate"><span class="check">✓</span><span>{esc(gate)}</span></div>
      </div>"""


def artifact(name: str, count: str, unit: str, desc: str) -> str:
    return f"""
      <div class="artifact">
        <div class="name">{esc(name)}</div>
        <div class="count">{esc(count)}<small>{esc(unit)}</small></div>
        <div class="desc">{esc(desc)}</div>
      </div>"""


SPINE_SVG = """
<svg class="spine" width="1600" height="900" viewBox="0 0 1600 900" xmlns="http://www.w3.org/2000/svg">
  <line x1="314" y1="520" x2="1286" y2="520" stroke="#8e2f2f" stroke-width="3"/>
  <polygon points="350,514 360,520 350,526" fill="#8e2f2f"/>
  <polygon points="580,514 590,520 580,526" fill="#8e2f2f"/>
  <polygon points="810,514 820,520 810,526" fill="#8e2f2f"/>
  <polygon points="1040,514 1050,520 1040,526" fill="#8e2f2f"/>
  <polygon points="1276,514 1286,520 1276,526" fill="#8e2f2f"/>
  <circle cx="455" cy="520" r="6" fill="#eef0e9" stroke="#8e2f2f" stroke-width="2.5"/>
  <circle cx="685" cy="520" r="6" fill="#eef0e9" stroke="#8e2f2f" stroke-width="2.5"/>
  <circle cx="915" cy="520" r="6" fill="#eef0e9" stroke="#8e2f2f" stroke-width="2.5"/>
  <circle cx="1145" cy="520" r="6" fill="#eef0e9" stroke="#8e2f2f" stroke-width="2.5"/>
  <path d="M 685 576 L 685 608 L 74 608 L 74 640" fill="none" stroke="#5f665f"
        stroke-width="1.2" stroke-dasharray="2 3"/>
  <polygon points="69,634 79,634 74,640" fill="#5f665f"/>
  <line x1="1145" y1="576" x2="1145" y2="640" stroke="#8e2f2f"
        stroke-width="1.5" stroke-dasharray="4 3"/>
  <polygon points="1140,634 1150,634 1145,640" fill="#8e2f2f"/>
</svg>
"""

def render_system() -> str:
    sources = "".join(
        [
            source_row("loan.csv", "682", "loan_id · account_id · status"),
            source_row("trans.csv", "1,056,320", "trans_id · account_id · type"),
            source_row("client.csv", "5,369", "client_id · birth_number"),
            source_row("account.csv", "4,500", "account_id · district_id · date"),
            source_row("disp.csv", "5,369", "disp_id · client_id · account_id"),
            source_row("district.csv", "77", "district_id · A2 · A3 · A10"),
        ]
    )

    build = "".join(
        [
            build_block(
                360,
                "01",
                "INGEST",
                "Extract + transform",
                "etl_pipeline.py",
                "data/*.csv",
                "mart.* · data/clean",
                "6 tables · 5 dims + 2 facts",
                "6",
                "tables in",
                "NO UNMAPPED LOANS",
            ),
            build_block(
                590,
                "02",
                "STORE",
                "Warehouse",
                "data/banking_dw.duckdb",
                "clean frames",
                "2 facts · 5 dimensions",
                "682 loans · 1,056,320 txns",
                "2+5",
                "facts + dims",
                "COUNTS > 0",
            ),
            build_block(
                820,
                "03",
                "FEATURE",
                "Feature mart",
                "sql/local/03_feature_mart.sql",
                "mart.*",
                "682 × 27 · analytics.loan_features",
                "76 defaults · 11.14%",
                "682",
                "loans · 27 cols",
                "N_TXN MATCHES",
            ),
            build_block(
                1050,
                "04",
                "MODEL",
                "Models + patterns",
                "build_advanced_models.py",
                "loan_features",
                "artifacts/models · metrics · rules · segments",
                "6 classifiers · 4 clusterers",
                "6+4",
                "models + clusterers",
                "SCORES = 682",
            ),
        ]
    )

    pages = "".join(
        [
            page_row("P1", "Executive overview", "threshold trade-off"),
            page_row("P2", "Data & leakage", "provenance audit"),
            page_row("P3", "Models", "CV + held-out checks"),
            page_row("P4", "Patterns", "rules + segments"),
            page_row("P5", "Simulator", "score one application"),
            page_row("P6", "Data model card", "galaxy schema"),
        ]
    )

    artifacts = "".join(
        [
            artifact("artifacts/models", "4", ".pkl", "baseline · tuned · capacity · MLP"),
            artifact("artifacts/metrics", "8", ".csv", "scores · CV · advanced"),
            artifact("artifacts/rules", "3", ".csv", "CBA · patterns · itemsets"),
            artifact("artifacts/segments", "4", ".csv", "labels · profiles · clusters"),
            artifact("data/features", "1", ".csv", "682 × 27 · upload input"),
        ]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>System architecture — schematic</title>
<style>
  :root {{
    --paper: {PAPER};
    --panel: {PANEL};
    --ink: {INK};
    --muted: {MUTED};
    --rule: {RULE};
    --oxblood: {OXBLOOD};
    --green: {GREEN};
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; background: var(--paper); }}
  body {{ width: 1600px; height: 900px; overflow: hidden; }}
  .page {{
    position: relative;
    width: 1600px;
    height: 900px;
    background: var(--paper);
    color: var(--ink);
    font-family: "Segoe UI", sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .page > * {{ position: absolute; }}

  .header {{ left: 64px; top: 36px; width: 1472px; }}
  .running {{
    font-family: "Cascadia Mono", monospace;
    font-size: 9px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
  }}
  .title {{
    margin-top: 10px;
    font-family: Georgia, serif;
    font-size: 44px;
    line-height: 1.05;
    font-weight: 400;
    letter-spacing: -0.015em;
  }}
  .subtitle {{
    margin-top: 8px;
    width: 1040px;
    font-size: 14px;
    line-height: 1.45;
    color: #454b45;
  }}
  .header-meta {{
    position: absolute;
    right: 0;
    top: 0;
    text-align: right;
    font-family: "Cascadia Mono", monospace;
    font-size: 8.5px;
    line-height: 1.8;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }}
  .header-meta strong {{ color: var(--ink); font-weight: 400; }}
  .header-rule {{
    left: 64px;
    top: 154px;
    width: 1472px;
    height: 1px;
    background: var(--ink);
  }}

  .spine {{ left: 0; top: 0; z-index: 10; pointer-events: none; }}

  .panel {{
    top: 220px;
    height: 356px;
    border: 1.5px solid var(--ink);
    background: var(--panel);
    z-index: 1;
  }}
  .sources {{ left: 64px; width: 250px; }}
  .serving {{ left: 1286px; width: 250px; }}
  .panel-head {{
    height: 32px;
    border-bottom: 1px solid var(--ink);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 10px;
    font-family: "Cascadia Mono", monospace;
    font-size: 7.5px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }}
  .panel-head .note {{
    color: var(--muted);
    letter-spacing: 0.06em;
  }}

  .source {{
    height: 54px;
    border-bottom: 1px solid var(--rule);
    padding: 6px 10px;
    display: grid;
    grid-template-columns: 18px 1fr 58px;
    gap: 6px;
  }}
  .source:last-child {{ border-bottom: none; }}
  .source .glyph {{ color: var(--muted); padding-top: 2px; }}
  .source .name {{
    font-family: Georgia, serif;
    font-size: 14.5px;
    line-height: 1.1;
  }}
  .source .fields {{
    margin-top: 2px;
    font-family: "Cascadia Mono", monospace;
    font-size: 7px;
    line-height: 1.2;
    color: var(--muted);
  }}
  .source .rows {{
    text-align: right;
    font-family: "Cascadia Mono", monospace;
    font-size: 12.5px;
    line-height: 1.2;
    white-space: nowrap;
  }}

  .page-row {{
    height: 54px;
    border-bottom: 1px solid var(--rule);
    padding: 6px 10px;
    display: grid;
    grid-template-columns: 18px 1fr 20px;
    gap: 6px;
  }}
  .page-row:last-child {{ border-bottom: none; }}
  .page-row .glyph {{ color: var(--muted); padding-top: 2px; }}
  .page-row .pname {{
    font-size: 11px;
    font-weight: 600;
    line-height: 1.15;
  }}
  .page-row .psub {{
    margin-top: 2px;
    font-family: "Cascadia Mono", monospace;
    font-size: 7px;
    color: var(--muted);
  }}
  .page-row .pnum {{
    text-align: right;
    font-family: "Cascadia Mono", monospace;
    font-size: 7px;
    color: var(--muted);
    padding-top: 1px;
  }}

  .block {{
    top: 260px;
    width: 190px;
    height: 316px;
    border: 1.5px solid var(--ink);
    background: var(--paper);
    z-index: 1;
  }}
  .block-head {{
    height: 44px;
    background: var(--ink);
    color: var(--paper);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 10px;
  }}
  .stage-no {{
    font-family: "Cascadia Mono", monospace;
    font-size: 20px;
    line-height: 1;
  }}
  .stage-tag {{
    font-family: "Cascadia Mono", monospace;
    font-size: 7px;
    letter-spacing: 0.16em;
    color: var(--rule);
  }}
  .block-body {{
    position: relative;
    height: 244px;
    padding: 10px;
  }}
  .block-title {{
    font-family: Georgia, serif;
    font-size: 17px;
    line-height: 1.1;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    min-height: 38px;
  }}
  .block-cmd {{
    margin-top: 2px;
    font-family: "Cascadia Mono", monospace;
    font-size: 8px;
    line-height: 1.25;
    color: var(--muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .block-rule {{
    margin-top: 7px;
    border-top: 1px solid var(--rule);
  }}
  .io {{
    display: flex;
    gap: 6px;
    margin-top: 5px;
    font-family: "Cascadia Mono", monospace;
    font-size: 7.5px;
    line-height: 1.3;
  }}
  .io .k {{
    width: 20px;
    flex: none;
    font-size: 6.5px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    padding-top: 1px;
  }}
  .io .v {{ flex: 1; }}
  .io.out .v {{ min-height: 20px; }}
  .audit {{
    margin-top: 3px;
    font-family: "Cascadia Mono", monospace;
    font-size: 7px;
    line-height: 1.3;
    color: var(--muted);
  }}
  .stat {{
    position: absolute;
    left: 10px;
    bottom: 52px;
  }}
  .stat-no {{
    display: block;
    font-family: "Cascadia Mono", monospace;
    font-size: 22px;
    line-height: 1;
  }}
  .stat-label {{
    display: block;
    margin-top: 2px;
    font-family: "Cascadia Mono", monospace;
    font-size: 7px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
  }}
  .gate {{
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 28px;
    background: #e9f0eb;
    border-top: 1px solid var(--green);
    color: var(--green);
    font-family: "Cascadia Mono", monospace;
    font-size: 7px;
    letter-spacing: 0.06em;
    display: flex;
    align-items: center;
    padding: 0 10px;
  }}
  .gate .check {{
    font-family: "Segoe UI Symbol", "Segoe UI", sans-serif;
    font-size: 9px;
    margin-right: 5px;
  }}

  .artifacts {{
    left: 360px;
    top: 640px;
    width: 880px;
    height: 110px;
    border: 1.5px solid var(--ink);
    background: var(--panel);
    z-index: 1;
  }}
  .artifacts-head {{
    height: 26px;
    border-bottom: 1px solid var(--ink);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 10px;
    font-family: "Cascadia Mono", monospace;
    font-size: 7px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }}
  .artifacts-head .note {{
    color: var(--muted);
    letter-spacing: 0.04em;
    text-transform: none;
  }}
  .artifacts-grid {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    height: 84px;
  }}
  .artifact {{
    border-left: 1px solid var(--rule);
    padding: 7px 8px;
  }}
  .artifact:first-child {{ border-left: none; }}
  .artifact .name {{
    font-family: "Cascadia Mono", monospace;
    font-size: 7px;
    color: var(--muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .artifact .count {{
    margin-top: 2px;
    font-family: "Cascadia Mono", monospace;
    font-size: 22px;
    line-height: 1;
  }}
  .artifact .count small {{
    font-size: 7px;
    color: var(--muted);
    margin-left: 2px;
  }}
  .artifact .desc {{
    margin-top: 2px;
    font-size: 7.5px;
    line-height: 1.2;
    color: #454b45;
  }}

  .cloud {{
    left: 64px;
    top: 640px;
    width: 250px;
    height: 110px;
    border: 1px dotted var(--muted);
    background: var(--paper);
    z-index: 1;
  }}
  .cloud-head {{
    height: 24px;
    padding: 0 10px;
    display: flex;
    align-items: center;
    font-family: "Cascadia Mono", monospace;
    font-size: 7px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
  }}
  .cloud-box {{
    margin: 0 10px;
    height: 30px;
    border: 1px dotted var(--rule);
    padding: 4px 6px;
  }}
  .cloud-box .cname {{
    font-family: "Cascadia Mono", monospace;
    font-size: 8.5px;
    line-height: 1.1;
  }}
  .cloud-box .csub {{
    font-family: "Cascadia Mono", monospace;
    font-size: 6.5px;
    color: var(--muted);
  }}
  .cloud-arrow {{
    height: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--muted);
    font-family: "Cascadia Mono", monospace;
    font-size: 8px;
  }}

  .legend {{
    left: 1286px;
    top: 640px;
    width: 250px;
    height: 110px;
    border: 1.5px solid var(--ink);
    background: var(--paper);
    z-index: 1;
  }}
  .legend-head {{
    height: 26px;
    border-bottom: 1px solid var(--ink);
    padding: 0 10px;
    display: flex;
    align-items: center;
    font-family: "Cascadia Mono", monospace;
    font-size: 7px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }}
  .legend-body {{ padding: 6px 10px; }}
  .legend-item {{
    display: flex;
    align-items: center;
    gap: 7px;
    height: 18px;
    font-family: "Cascadia Mono", monospace;
    font-size: 7px;
    color: var(--muted);
  }}
  .legend-line {{ width: 20px; height: 2px; background: var(--oxblood); }}
  .legend-line.dashed {{
    background: none;
    border-top: 2px dashed var(--oxblood);
    height: 0;
  }}
  .legend-line.dotted {{
    background: none;
    border-top: 2px dotted var(--muted);
    height: 0;
  }}
  .legend-gate {{
    width: 9px;
    height: 9px;
    background: #e9f0eb;
    border: 1px solid var(--green);
  }}

  .footnote {{
    left: 64px;
    top: 772px;
    width: 1472px;
    font-size: 7.5px;
    line-height: 1.4;
    color: var(--muted);
  }}
  .footnote .mark {{ color: var(--oxblood); }}

  .footer {{
    left: 64px;
    top: 852px;
    width: 1472px;
    border-top: 1px solid var(--rule);
    padding-top: 7px;
    display: flex;
    justify-content: space-between;
    font-family: "Cascadia Mono", monospace;
    font-size: 7.5px;
    color: var(--muted);
  }}
</style>
</head>
<body>
  <div class="page">
    <header class="header">
      <div class="running">Banking analytics data warehouse / system map</div>
      <h1 class="title">System architecture</h1>
      <div class="subtitle">Six CSVs → DuckDB galaxy schema → leakage-safe feature mart → artifacts → six-page review app.</div>
      <div class="header-meta">
        <div><strong>FIG. 01</strong></div>
        <div>PKDD'99 · LOCAL BUILD</div>
        <div>682 LOANS · 1,056,320 TXNS</div>
      </div>
    </header>
    <div class="header-rule"></div>

    <section class="panel sources">
      <div class="panel-head"><span>Sources</span><span class="note">6 CSVs</span></div>
      {sources}
    </section>

    <section class="panel serving">
      <div class="panel-head"><span>Serving</span><span class="note">6 pages</span></div>
      {pages}
    </section>

    {build}

    {SPINE_SVG}

    <section class="artifacts">
      <div class="artifacts-head"><span>Persisted artifacts</span><span class="note">read by the app · never retrained</span></div>
      <div class="artifacts-grid">{artifacts}</div>
    </section>

    <section class="cloud">
      <div class="cloud-head">Optional cloud</div>
      <div class="cloud-box" style="margin-top:6px"><div class="cname">Snowflake</div><div class="csub">RAW / MART</div></div>
      <div class="cloud-arrow">↓</div>
      <div class="cloud-box"><div class="cname">Power BI</div><div class="csub">report</div></div>
    </section>

    <section class="legend">
      <div class="legend-head">Legend</div>
      <div class="legend-body">
        <div class="legend-item"><span class="legend-line"></span><span>local data flow</span></div>
        <div class="legend-item"><span class="legend-line dashed"></span><span>persisted artifact</span></div>
        <div class="legend-item"><span class="legend-line dotted"></span><span>optional cloud path</span></div>
        <div class="legend-item"><span class="legend-gate"></span><span>validation gate</span></div>
      </div>
    </section>

    <div class="footnote">
      <div><span class="mark">†</span> Optional path: upload_to_snowflake.py → Snowflake RAW / MART → Power BI. Model and pattern artifacts stay local.</div>
      <div><span class="mark">‡</span> card.csv and order.csv are present in data/ but are not used by the build.</div>
    </div>

    <footer class="footer">
      <div>Source: scripts/build_local.py · sql/local/03_feature_mart.sql · app/streamlit_app.py</div>
      <div>FIG. 01 / 03 · 2400 × 1350</div>
    </footer>
  </div>
</body>
</html>"""


BASE_CSS = """
  :root {
    --paper: #eef0e9;
    --panel: #e7ebe2;
    --ink: #171a17;
    --muted: #5f665f;
    --rule: #c9cec4;
    --oxblood: #8e2f2f;
    --green: #2f6b4f;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: var(--paper); }
  body { width: 1600px; height: 900px; overflow: hidden; }
  .page {
    position: relative;
    width: 1600px;
    height: 900px;
    background: var(--paper);
    color: var(--ink);
    font-family: "Segoe UI", sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  .page > * { position: absolute; }
  .header { left: 64px; top: 36px; width: 1472px; }
  .running {
    font-family: "Cascadia Mono", monospace;
    font-size: 9px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
  }
  .title {
    margin-top: 10px;
    font-family: Georgia, serif;
    font-size: 44px;
    line-height: 1.05;
    font-weight: 400;
    letter-spacing: -0.015em;
  }
  .subtitle {
    margin-top: 8px;
    width: 1040px;
    font-size: 14px;
    line-height: 1.45;
    color: #454b45;
  }
  .header-meta {
    position: absolute;
    right: 0;
    top: 0;
    text-align: right;
    font-family: "Cascadia Mono", monospace;
    font-size: 8.5px;
    line-height: 1.8;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .header-meta strong { color: var(--ink); font-weight: 400; }
  .header-rule {
    left: 64px;
    top: 154px;
    width: 1472px;
    height: 1px;
    background: var(--ink);
  }
  .footer {
    left: 64px;
    top: 852px;
    width: 1472px;
    border-top: 1px solid var(--rule);
    padding-top: 7px;
    display: flex;
    justify-content: space-between;
    font-family: "Cascadia Mono", monospace;
    font-size: 7.5px;
    color: var(--muted);
  }
"""


PIPELINE_CSS = """
  .orchestrator {
    left: 64px; top: 174px; width: 1472px; height: 52px;
    background: var(--ink); color: var(--paper); padding: 9px 14px;
  }
  .orch-top { display: flex; justify-content: space-between; align-items: baseline; }
  .orch-name { font-family: "Cascadia Mono", monospace; font-size: 10px; }
  .orch-note {
    font-family: "Cascadia Mono", monospace; font-size: 7px;
    letter-spacing: 0.14em; color: var(--rule);
  }
  .orch-run {
    margin-top: 4px; font-family: "Cascadia Mono", monospace;
    font-size: 7.5px; color: #b9c4b8; white-space: nowrap;
  }
  .stage {
    top: 246px; width: 350px; height: 176px;
    border: 1.5px solid var(--ink); background: var(--paper);
  }
  .stage.second { top: 462px; }
  .stage-head {
    height: 40px; background: var(--ink); color: var(--paper);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 10px;
  }
  .stage-no { font-family: "Cascadia Mono", monospace; font-size: 18px; line-height: 1; }
  .stage-tag {
    font-family: "Cascadia Mono", monospace; font-size: 7px;
    letter-spacing: 0.16em; color: var(--rule);
  }
  .stage-body { position: relative; height: 110px; padding: 9px 10px; }
  .stage-title {
    font-family: Georgia, serif; font-size: 15px; line-height: 1.05;
    text-transform: uppercase; letter-spacing: 0.02em;
  }
  .stage-cmd {
    margin-top: 2px; font-family: "Cascadia Mono", monospace;
    font-size: 8px; color: var(--muted);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .stage-rule { margin-top: 6px; border-top: 1px solid var(--rule); }
  .io {
    display: flex; gap: 6px; margin-top: 4px;
    font-family: "Cascadia Mono", monospace; font-size: 7.5px; line-height: 1.25;
  }
  .io .k {
    width: 22px; flex: none; font-size: 6.5px; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--muted); padding-top: 1px;
  }
  .io .v { flex: 1; }
  .detail {
    margin-top: 3px; font-family: "Cascadia Mono", monospace;
    font-size: 7px; line-height: 1.25; color: var(--muted);
  }
  .gate {
    position: absolute; left: 0; right: 0; bottom: 0; height: 26px;
    background: #e9f0eb; border-top: 1px solid var(--green);
    color: var(--green); font-family: "Cascadia Mono", monospace;
    font-size: 7px; letter-spacing: 0.06em;
    display: flex; align-items: center; padding: 0 10px;
  }
  .rail { left: 0; top: 0; z-index: 10; pointer-events: none; }
  .nb-head {
    left: 64px; top: 664px; width: 1472px;
    border-top: 1px solid var(--ink); padding-top: 6px;
    display: flex; justify-content: space-between; align-items: baseline;
  }
  .nb-head .label {
    font-family: "Cascadia Mono", monospace; font-size: 8px;
    letter-spacing: 0.14em; text-transform: uppercase;
  }
  .nb-head .note { font-family: "Cascadia Mono", monospace; font-size: 7px; color: var(--muted); }
  .nb-block {
    top: 690px; height: 78px; width: 237px;
    border: 1px dashed var(--muted); padding: 7px 8px;
  }
  .nb-top { display: flex; gap: 6px; align-items: baseline; }
  .nb-no { font-family: "Cascadia Mono", monospace; font-size: 7px; color: var(--muted); }
  .nb-name {
    font-family: "Cascadia Mono", monospace; font-size: 8px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .nb-detail {
    margin-top: 5px; font-family: "Cascadia Mono", monospace;
    font-size: 7px; line-height: 1.35; color: #454b45;
  }
  .nb-detail + .nb-detail { margin-top: 2px; }
  .legend-row {
    left: 900px; top: 800px; width: 636px;
    display: flex; justify-content: flex-end; gap: 18px;
    font-family: "Cascadia Mono", monospace; font-size: 7px; color: var(--muted);
  }
  .legend-item { display: flex; align-items: center; gap: 6px; }
  .legend-line { width: 22px; height: 2px; background: var(--oxblood); }
  .legend-line.dashed { background: none; border-top: 2px dashed var(--muted); height: 0; }
  .legend-gate { width: 9px; height: 9px; background: #e9f0eb; border: 1px solid var(--green); }
  .footnote {
    left: 64px; top: 800px; width: 820px;
    font-size: 7.5px; line-height: 1.4; color: var(--muted);
  }
"""


PIPELINE_RAIL_SVG = """
<svg class="rail" width="1600" height="900" viewBox="0 0 1600 900" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="pipe-arrow" viewBox="0 0 10 10" refX="9" refY="5"
      markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#8e2f2f"/>
    </marker>
  </defs>
  <line x1="414" y1="334" x2="438" y2="334" stroke="#8e2f2f" stroke-width="2" marker-end="url(#pipe-arrow)"/>
  <line x1="788" y1="334" x2="812" y2="334" stroke="#8e2f2f" stroke-width="2" marker-end="url(#pipe-arrow)"/>
  <line x1="1162" y1="334" x2="1186" y2="334" stroke="#8e2f2f" stroke-width="2" marker-end="url(#pipe-arrow)"/>
  <line x1="414" y1="550" x2="438" y2="550" stroke="#8e2f2f" stroke-width="2" marker-end="url(#pipe-arrow)"/>
  <line x1="788" y1="550" x2="812" y2="550" stroke="#8e2f2f" stroke-width="2" marker-end="url(#pipe-arrow)"/>
  <line x1="1162" y1="550" x2="1186" y2="550" stroke="#8e2f2f" stroke-width="2" marker-end="url(#pipe-arrow)"/>
  <path d="M 1361 422 L 1361 442 L 239 442 L 239 462" fill="none"
    stroke="#8e2f2f" stroke-width="2" stroke-linejoin="miter" marker-end="url(#pipe-arrow)"/>
  <text x="800" y="437" text-anchor="middle" font-family="Cascadia Mono, monospace"
    font-size="6.5" fill="#5f665f" letter-spacing="0.12em">PRODUCTION ORDER</text>
</svg>
"""


def pipeline_stage(
    left: int,
    second: bool,
    num: str,
    tag: str,
    title: str,
    command: str,
    source: str,
    output: str,
    detail: str,
    gate: str,
) -> str:
    top_class = "second" if second else ""
    return f"""
    <div class="stage {top_class}" style="left:{left}px">
      <div class="stage-head"><span class="stage-no">{esc(num)}</span><span class="stage-tag">{esc(tag)}</span></div>
      <div class="stage-body">
        <div class="stage-title">{esc(title)}</div>
        <div class="stage-cmd">{esc(command)}</div>
        <div class="stage-rule"></div>
        <div class="io"><span class="k">in</span><span class="v">{esc(source)}</span></div>
        <div class="io"><span class="k">out</span><span class="v">{esc(output)}</span></div>
        <div class="detail">{esc(detail)}</div>
      </div>
      <div class="gate">✓ {esc(gate)}</div>
    </div>"""


def notebook_block(left: int, num: str, name: str, lines: list[str]) -> str:
    body = "".join(f'<div class="nb-detail">{esc(line)}</div>' for line in lines)
    return f"""
    <div class="nb-block" style="left:{left}px">
      <div class="nb-top"><span class="nb-no">{esc(num)}</span><span class="nb-name">{esc(name)}</span></div>
      {body}
    </div>"""


def render_pipeline() -> str:
    row1 = "".join(
        [
            pipeline_stage(64, False, "01", "EXTRACT", "Extract", "extract_data()",
                           "data/*.csv", "6 DataFrames",
                           "loan · trans · client · account · disp · district", "FILES EXIST"),
            pipeline_stage(438, False, "02", "TRANSFORM", "Transform", "transform_dimensions()",
                           "raw frames", "5 dims + 2 facts",
                           "parse birth numbers · map owners + branches", "NO UNKNOWN CODES"),
            pipeline_stage(812, False, "03", "WAREHOUSE", "Warehouse", "load_data()",
                           "clean frames", "data/banking_dw.duckdb",
                           "mart schema · dim_date 2,191 days", "COUNTS > 0"),
            pipeline_stage(1186, False, "04", "FEATURE MART", "Feature mart", "03_feature_mart.sql",
                           "mart.*", "analytics.loan_features",
                           "682 loans × 27 cols · 76 defaults (11.14%)", "NO POST-LOAN ROWS"),
        ]
    )
    row2 = "".join(
        [
            pipeline_stage(64, True, "05", "MODELS", "Models", "build_advanced_models.py",
                           "loan_features", "models + metrics",
                           "MLP · capacity-aware GB · 50-fold CV", "SCORES = 682"),
            pipeline_stage(438, True, "06", "PATTERNS", "Patterns + segments", "tools/pattern_mining.py",
                           "loan_features", "rules + segments",
                           "FP-Growth · Apriori · KMeans · k-medoids · AGNES · DBSCAN", "RULES ≥ 1"),
            pipeline_stage(812, True, "07", "ANALYTICS", "Analytics", "build_analytics.py",
                           "artifacts/*", "17 tables",
                           "17 CSVs → DuckDB · analytics schema", "ALL FILES PRESENT"),
            pipeline_stage(1186, True, "08", "SERVE", "Validate + serve", "validate() + Streamlit",
                           "all tables", "localhost:8501",
                           "row counts · defaults · no post-loan rows · 6-page app", "FAIL-FAST"),
        ]
    )
    notebooks = "".join(
        [
            notebook_block(64, "N1", "01_preprocessing.ipynb", ["load 6 CSVs", "clean types, parse dates", "write data/clean snapshots"]),
            notebook_block(311, "N2", "02_features.ipynb", ["pre-loan aggregation", "18 model features", "write data/features CSV"]),
            notebook_block(558, "N3", "03_eda.ipynb", ["distributions", "risk quadrants", "save artifacts/figures"]),
            notebook_block(805, "N4", "04_modeling.ipynb", ["6 classifiers", "tuning + 50-fold CV", "save models + metrics"]),
            notebook_block(1052, "N5", "05_segmentation.ipynb", ["KMeans k=2", "segment profiles", "save segments"]),
            notebook_block(1299, "N6", "06_clustering_comparison.ipynb", ["K-medoids, AGNES", "DBSCAN + PCA", "compare clusterings"]),
        ]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Pipeline architecture — schematic</title>
<style>
{BASE_CSS}
{PIPELINE_CSS}
</style>
</head>
<body>
  <div class="page">
    <header class="header">
      <div class="running">Banking analytics data warehouse / pipeline</div>
      <h1 class="title">Pipeline architecture</h1>
      <div class="subtitle">Two tracks: notebooks explain the analysis; scripts/build_local.py is the reproducible path that rebuilds every table and artifact.</div>
      <div class="header-meta">
        <div><strong>FIG. 02</strong></div>
        <div>PKDD'99 · LOCAL BUILD</div>
        <div>8 STAGES · 6 NOTEBOOKS</div>
      </div>
    </header>
    <div class="header-rule"></div>

    <div class="orchestrator">
      <div class="orch-top"><span class="orch-name">scripts/build_local.py</span><span class="orch-note">ONE COMMAND · FIXED ORDER</span></div>
      <div class="orch-run">run_etl() → feature SQL → export_features() → build_advanced() → build_capacity() → build_patterns() → build_analytics() → validate()</div>
    </div>

    {row1}
    {row2}
    {PIPELINE_RAIL_SVG}

    <div class="nb-head"><span class="label">Notebook track / exploration only</span><span class="note">NOT IMPORTED BY THE BUILD</span></div>
    {notebooks}

    <div class="footnote">The production track is the reproducible path from raw CSV to the Streamlit app. Notebooks are optional and never imported by the build.</div>
    <div class="legend-row">
      <span class="legend-item"><span class="legend-line"></span>production order</span>
      <span class="legend-item"><span class="legend-line dashed"></span>notebook</span>
      <span class="legend-item"><span class="legend-gate"></span>validation gate</span>
    </div>

    <footer class="footer">
      <div>Source: scripts/build_local.py · notebooks/*.ipynb · app/streamlit_app.py</div>
      <div>FIG. 02 / 03 · 2400 × 1350</div>
    </footer>
  </div>
</body>
</html>"""


FEATURE_CSS = """
  .step {
    top: 180px; width: 350px; height: 96px;
    border: 1.5px solid var(--ink); background: var(--paper);
  }
  .step-head {
    height: 26px; background: var(--ink); color: var(--paper);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 9px;
  }
  .step-no { font-family: "Cascadia Mono", monospace; font-size: 13px; line-height: 1; }
  .step-tag {
    font-family: "Cascadia Mono", monospace; font-size: 6.5px;
    letter-spacing: 0.14em; color: var(--rule);
  }
  .step-body { padding: 7px 9px; }
  .step-title {
    font-family: Georgia, serif; font-size: 13px; line-height: 1.05;
    text-transform: uppercase; letter-spacing: 0.02em;
  }
  .step-detail {
    margin-top: 3px; font-family: "Cascadia Mono", monospace;
    font-size: 7px; line-height: 1.3; color: var(--muted);
  }
  .line-rail { left: 0; top: 0; z-index: 10; pointer-events: none; }
  .vector-head {
    left: 64px; top: 292px; width: 1472px;
    border-top: 2px solid var(--ink); border-bottom: 1px solid var(--rule);
    padding: 5px 0; display: flex; justify-content: space-between; align-items: baseline;
  }
  .vector-head .label {
    font-family: "Cascadia Mono", monospace; font-size: 8px;
    letter-spacing: 0.14em; text-transform: uppercase;
  }
  .vector-head .meta {
    font-family: "Cascadia Mono", monospace; font-size: 7px;
    color: var(--muted); display: flex; align-items: center; gap: 5px;
  }
  .sw { width: 8px; height: 8px; display: inline-block; }
  .sw.model { background: #f1e4e4; border: 1px solid var(--oxblood); }
  .sw.context { background: var(--panel); border: 1px solid var(--muted); }
  .group-label {
    top: 322px; text-align: center;
    font-family: "Cascadia Mono", monospace; font-size: 7px;
    letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted);
  }
  .brackets { left: 0; top: 0; z-index: 5; pointer-events: none; }
  .vector { display: flex; gap: 4px; }
  .cell {
    flex: 0 0 50px; height: 150px;
    display: flex; flex-direction: column; align-items: center;
    padding: 6px 3px;
  }
  .cell.model { background: #f1e4e4; border: 1px solid #d9b8b8; border-top: 3px solid var(--oxblood); }
  .cell.context { background: var(--panel); border: 1px solid var(--rule); border-top: 3px solid var(--muted); }
  .cell .idx { font-family: "Cascadia Mono", monospace; font-size: 6px; color: var(--muted); }
  .cell .fname {
    flex: 1; display: flex; align-items: center; text-align: center;
    font-family: "Cascadia Mono", monospace; font-size: 6.5px;
    line-height: 1.25; word-break: break-word;
  }
  .cell .mark { width: 6px; height: 6px; margin-bottom: 2px; }
  .cell.model .mark { background: var(--oxblood); }
  .cell.context .mark { border: 1px solid var(--muted); }
  .group-card {
    top: 524px; height: 80px;
    border-top: 1px solid var(--rule); padding: 8px 10px 0;
  }
  .gc-name {
    font-family: "Cascadia Mono", monospace; font-size: 7px;
    letter-spacing: 0.14em; text-transform: uppercase; color: var(--muted);
  }
  .gc-line { margin-top: 3px; display: flex; align-items: baseline; gap: 6px; }
  .gc-count { font-family: "Cascadia Mono", monospace; font-size: 22px; line-height: 1; }
  .gc-unit {
    font-family: "Cascadia Mono", monospace; font-size: 6.5px;
    text-transform: uppercase; color: var(--muted);
  }
  .gc-model {
    margin-left: 0; font-family: "Cascadia Mono", monospace;
    font-size: 7px; color: var(--oxblood); white-space: nowrap;
  }
  .gc-model.zero { color: var(--muted); }
  .gc-note { margin-top: 5px; font-size: 7px; line-height: 1.3; color: #454b45; }
  .guard {
    left: 64px; top: 628px; width: 1472px; height: 112px;
    border: 1.5px solid var(--oxblood); background: #f1e4e4;
  }
  .guard-head {
    height: 24px; border-bottom: 1px solid #d9b8b8; padding: 0 12px;
    display: flex; align-items: center; justify-content: space-between;
    font-family: "Cascadia Mono", monospace; font-size: 7.5px;
    letter-spacing: 0.14em; text-transform: uppercase; color: var(--oxblood);
  }
  .guard-head .ok { color: var(--green); letter-spacing: 0.06em; }
  .guard-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
    padding: 10px 12px 0;
  }
  .gi-no { font-family: "Cascadia Mono", monospace; font-size: 6.5px; color: var(--oxblood); }
  .gi-title {
    margin-top: 1px; font-family: "Cascadia Mono", monospace;
    font-size: 7.5px; text-transform: uppercase; letter-spacing: 0.06em;
  }
  .gi-detail {
    margin-top: 2px; font-family: "Cascadia Mono", monospace;
    font-size: 7px; line-height: 1.3; color: #5a3a3a;
  }
  .guard-foot {
    position: absolute; left: 12px; right: 12px; bottom: 7px;
    display: flex; justify-content: space-between;
    font-family: "Cascadia Mono", monospace; font-size: 7px;
  }
  .guard-foot .ok { color: var(--green); }
  .guard-foot .risk { color: var(--oxblood); }
  .footnote {
    left: 64px; top: 764px; width: 1472px;
    font-size: 7.5px; line-height: 1.4; color: var(--muted);
  }
"""


LINEAGE_SVG = """
<svg class="line-rail" width="1600" height="900" viewBox="0 0 1600 900" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="line-arrow" viewBox="0 0 10 10" refX="9" refY="5"
      markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#8e2f2f"/>
    </marker>
  </defs>
  <line x1="414" y1="228" x2="438" y2="228" stroke="#8e2f2f" stroke-width="2" marker-end="url(#line-arrow)"/>
  <line x1="788" y1="228" x2="812" y2="228" stroke="#8e2f2f" stroke-width="2" marker-end="url(#line-arrow)"/>
  <line x1="1162" y1="228" x2="1186" y2="228" stroke="#8e2f2f" stroke-width="2" marker-end="url(#line-arrow)"/>
</svg>
"""


def lineage_step(left: int, num: str, tag: str, title: str, line1: str, line2: str) -> str:
    return f"""
    <div class="step" style="left:{left}px">
      <div class="step-head"><span class="step-no">{esc(num)}</span><span class="step-tag">{esc(tag)}</span></div>
      <div class="step-body">
        <div class="step-title">{esc(title)}</div>
        <div class="step-detail">{esc(line1)}</div>
        <div class="step-detail">{esc(line2)}</div>
      </div>
    </div>"""


def feature_label(name: str) -> str:
    if len(name) > 8 and "_" in name:
        head, tail = name.split("_", 1)
        return f"{esc(head)}_<br>{esc(tail)}"
    return esc(name)


def vector_cell(index: int, name: str, model: bool) -> str:
    cls = "model" if model else "context"
    return f"""
      <div class="cell {cls}">
        <div class="idx">{index:02d}</div>
        <div class="fname">{feature_label(name)}</div>
        <div class="mark"></div>
      </div>"""


FEATURE_GROUPS = [
    {
        "name": "Identifiers",
        "count": 3,
        "model": 0,
        "note": "context only; never model inputs",
        "features": [("loan_id", False), ("account_id", False), ("client_id", False)],
    },
    {
        "name": "Loan record",
        "count": 7,
        "model": 3,
        "note": "amount, duration, payments are model inputs; date, status, target are context",
        "features": [
            ("amount", True), ("duration", True), ("payments", True),
            ("date", False), ("parsed_date", False), ("status", False), ("target", False),
        ],
    },
    {
        "name": "Behaviour, pre-loan",
        "count": 13,
        "model": 13,
        "note": "all 13 model · pre-loan only · LEFT JOIN + COALESCE keeps zero-txn loans",
        "features": [
            ("n_txn", True), ("n_deposit", True), ("n_withdrawal", True),
            ("sum_deposit", True), ("sum_withdrawal", True), ("avg_amount", True),
            ("std_amount", True), ("avg_balance", True), ("min_balance", True),
            ("max_balance", True), ("balance_at_loan", True), ("months_active", True),
            ("txn_per_month", True),
        ],
    },
    {
        "name": "Demographics",
        "count": 4,
        "model": 2,
        "note": "gender_bin and age are model inputs",
        "features": [("gender_bin", True), ("age", True), ("gender", False), ("district_id", False)],
    },
]


def render_features() -> str:
    vec_x = 73
    cell_w = 50
    cell_gap = 4
    pitch = cell_w + cell_gap

    start = 0
    for group in FEATURE_GROUPS:
        group["x1"] = vec_x + start * pitch
        group["x2"] = vec_x + (start + group["count"] - 1) * pitch + cell_w
        group["width"] = group["x2"] - group["x1"]
        start += group["count"]

    cells = []
    index = 0
    for group in FEATURE_GROUPS:
        for name, model in group["features"]:
            index += 1
            cells.append(vector_cell(index, name, model))
    cells_html = "".join(cells)

    labels = "".join(
        f'<div class="group-label" style="left:{g["x1"]}px;width:{g["width"]}px">'
        f'{esc(g["name"])} ({g["count"]})</div>'
        for g in FEATURE_GROUPS
    )

    card_parts = []
    for g in FEATURE_GROUPS:
        model_cls = "gc-model zero" if g["model"] == 0 else "gc-model"
        card_parts.append(
            f"""
    <div class="group-card" style="left:{g["x1"]}px;width:{g["width"]}px">
      <div class="gc-name">{esc(g["name"])}</div>
      <div class="gc-line"><span class="gc-count">{g["count"]}</span><span class="gc-unit">columns</span><span class="{model_cls}">{g["model"]} model</span></div>
      <div class="gc-note">{esc(g["note"])}</div>
    </div>"""
        )
    cards = "".join(card_parts)

    bracket_parts = []
    for g in FEATURE_GROUPS:
        x1, x2 = g["x1"], g["x2"]
        bracket_parts.append(
            f'<line x1="{x1}" y1="342" x2="{x2}" y2="342" stroke="#171a17" stroke-width="1"/>'
        )
        bracket_parts.append(
            f'<line x1="{x1}" y1="342" x2="{x1}" y2="348" stroke="#171a17" stroke-width="1"/>'
        )
        bracket_parts.append(
            f'<line x1="{x2}" y1="342" x2="{x2}" y2="348" stroke="#171a17" stroke-width="1"/>'
        )
    brackets = (
        '<svg class="brackets" width="1600" height="900" viewBox="0 0 1600 900" '
        'xmlns="http://www.w3.org/2000/svg">' + "".join(bracket_parts) + "</svg>"
    )

    lineage = "".join(
        [
            lineage_step(64, "01", "JOIN", "Join ownership",
                         "disp.type = OWNER · account_id → client_id", "district_id → branch"),
            lineage_step(438, "02", "FILTER", "Pre-loan window",
                         "t.date_id < loan.date_id", "strictly before the loan · same-day excluded"),
            lineage_step(812, "03", "AGGREGATE", "Aggregate per loan",
                         "counts · sums · averages · min/max balance", "months_active · txn_per_month"),
            lineage_step(1186, "04", "LABEL", "Label",
                         "status in (B, D) → target", "76 defaults / 682 = 11.14%"),
        ]
    )

    guard_items = "".join(
        [
            '<div class="guard-item"><div class="gi-no">01</div><div class="gi-title">Strict pre-loan</div><div class="gi-detail">t.date_id &lt; loan.date_id</div></div>',
            '<div class="guard-item"><div class="gi-no">02</div><div class="gi-title">Same-day excluded</div><div class="gi-detail">no post-loan rows enter the mart</div></div>',
            '<div class="guard-item"><div class="gi-no">03</div><div class="gi-title">Left join + coalesce</div><div class="gi-detail">zero-transaction loans survive with zeros</div></div>',
            '<div class="guard-item"><div class="gi-no">04</div><div class="gi-title">18 model features</div><div class="gi-detail">ids, raw dates, status and target excluded</div></div>',
        ]
    )

    model_total = sum(g["model"] for g in FEATURE_GROUPS)
    context_total = sum(g["count"] - g["model"] for g in FEATURE_GROUPS)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Feature vector — schematic</title>
<style>
{BASE_CSS}
{FEATURE_CSS}
</style>
</head>
<body>
  <div class="page">
    <header class="header">
      <div class="running">Banking analytics data warehouse / feature vector</div>
      <h1 class="title">Feature vector</h1>
      <div class="subtitle">One row per loan. 27 columns: 3 identifiers, 7 loan fields, 13 pre-loan behaviour aggregates, 4 demographics. 18 are model inputs.</div>
      <div class="header-meta">
        <div><strong>FIG. 03</strong></div>
        <div>PKDD'99 · LOCAL BUILD</div>
        <div>682 ROWS · 27 COLUMNS</div>
      </div>
    </header>
    <div class="header-rule"></div>

    {lineage}
    {LINEAGE_SVG}

    <div class="vector-head">
      <span class="label">Output vector / analytics.loan_features</span>
      <span class="meta"><span class="sw model"></span>MODEL {model_total} <span class="sw context"></span>CONTEXT {context_total} <span>·</span> 682 × 27</span>
    </div>

    {labels}
    {brackets}
    <div class="vector" style="left:{vec_x}px;top:352px;width:1454px">{cells_html}</div>
    {cards}

    <section class="guard">
      <div class="guard-head"><span>Leakage guard</span><span class="ok">AUDITED · 682 LOANS</span></div>
      <div class="guard-grid">{guard_items}</div>
      <div class="guard-foot"><span class="ok">AUDIT &nbsp;n_txn matches the pre-loan count for all 682 loans</span><span class="risk">TARGET &nbsp;status in (B, D) → 76 / 682 = 11.14%</span></div>
    </section>

    <div class="footnote">Column order is conceptual: identifiers, loan record, behaviour, demographics. The CSV stores the same 27 columns in a different physical order.</div>

    <footer class="footer">
      <div>Source: sql/local/03_feature_mart.sql · data/features/loan_features.csv · scripts/build_local.py</div>
      <div>FIG. 03 / 03 · 2400 × 1350</div>
    </footer>
  </div>
</body>
</html>"""


def capture(html_doc: str, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / f"{name}.png"
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / f"{name}.html"
        page.write_text(html_doc, encoding="utf-8")
        profile = Path(tmp) / "chrome-profile"
        subprocess.run(
            [
                str(CHROME),
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-extensions",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=1000",
                "--window-size=1600,900",
                "--force-device-scale-factor=1.5",
                f"--user-data-dir={profile}",
                f"--screenshot={target}",
                page.as_uri(),
            ],
            check=True,
            capture_output=True,
        )
    return target


def main() -> None:
    for doc, name in [
        (render_system(), "01_system_architecture"),
        (render_pipeline(), "02_pipeline_architecture"),
        (render_features(), "03_feature_vector"),
    ]:
        target = capture(doc, name)
        print(f"Wrote {target}")


if __name__ == "__main__":
    main()
