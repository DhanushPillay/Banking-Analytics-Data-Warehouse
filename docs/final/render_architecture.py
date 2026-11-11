"""Render the detailed architecture diagrams used in docs/final.

Outputs (PNG + SVG), overwriting the previous 1900x900 images:
  docs/final/images/architecture/01_system_architecture.*
  docs/final/images/architecture/02_pipeline_architecture.*
  docs/final/images/architecture/03_feature_vector.*

Run with: venv\\Scripts\\python.exe docs\\final\\render_architecture.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "final" / "images" / "architecture"

PAPER = "#fbfaf7"
INK = "#191b1f"
MUTED = "#6b6f76"
RULE = "#e4e1d8"
ACCENT = "#1f4e6b"
GOOD = "#2f6b4f"
RISK = "#b23a3a"
FILL = "#f3f0e9"
BLUE = "#e8eef2"
GREEN = "#e9f0eb"
RED = "#f5e8e8"
WHITE = "#ffffff"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "axes.facecolor": PAPER,
        "figure.facecolor": PAPER,
        "savefig.facecolor": PAPER,
    }
)


def canvas(title: str, subtitle: str):
    fig, ax = plt.subplots(figsize=(16, 9), dpi=150)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_xlim(0, 160)
    ax.set_ylim(0, 90)
    ax.set_axis_off()
    ax.text(2, 87.4, title, fontsize=15, fontweight="bold", color=INK, va="top")
    ax.text(2, 83.6, subtitle, fontsize=9, color=MUTED, va="top")
    return fig, ax


def _spec(line):
    if isinstance(line, tuple):
        text = line[0]
        color = line[1] if len(line) > 1 else INK
        weight = line[2] if len(line) > 2 else "normal"
        size = line[3] if len(line) > 3 else None
        return text, color, weight, size
    return line, INK, "normal", None


def box(
    ax,
    x,
    y,
    w,
    h,
    title="",
    lines=(),
    *,
    edge=ACCENT,
    fill=BLUE,
    title_color=INK,
    body_size=7.0,
    title_size=8.8,
    lw=1.15,
    ls="-",
    radius=0.55,
    pad=0.18,
    badge=None,
    badge_color=ACCENT,
):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle=f"round,pad={pad},rounding_size={radius}",
            linewidth=lw,
            edgecolor=edge,
            facecolor=fill,
            linestyle=ls,
            zorder=2,
        )
    )
    if title:
        ax.text(
            x + 0.8,
            y + h - 1.1,
            title,
            fontsize=title_size,
            fontweight="bold",
            color=title_color,
            va="top",
            ha="left",
            zorder=3,
        )
    if badge:
        ax.text(
            x + w - 0.8,
            y + h - 1.1,
            badge,
            fontsize=6.2,
            color=badge_color,
            va="top",
            ha="right",
            zorder=3,
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor=PAPER,
                edgecolor=badge_color,
                linewidth=0.5,
            ),
        )
    step = body_size * 0.19
    ty = y + h - (3.2 if title else 1.4)
    for line in lines:
        text, color, weight, size = _spec(line)
        ax.text(
            x + 0.8,
            ty,
            text,
            fontsize=size or body_size,
            color=color,
            fontweight=weight,
            va="top",
            ha="left",
            zorder=3,
        )
        ty -= step


def zone(ax, x, y, w, h, label, *, color=RULE, ls=(0, (4, 3)), label_color=MUTED):
    ax.add_patch(
        Rectangle(
            (x, y),
            w,
            h,
            fill=False,
            edgecolor=color,
            linewidth=1.0,
            linestyle=ls,
            zorder=1,
        )
    )
    ax.text(
        x + 0.8,
        y + h - 0.6,
        label,
        fontsize=7.2,
        fontweight="bold",
        color=label_color,
        va="top",
        ha="left",
        zorder=1,
        bbox=dict(facecolor=PAPER, edgecolor="none", pad=0.4),
    )


def arrow(
    ax,
    start,
    end,
    *,
    color=MUTED,
    lw=1.3,
    ls="-",
    rad=0.0,
    label=None,
    label_size=6.6,
    label_offset=(0, 0),
    style="-|>",
    ms=9,
):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle=style,
            mutation_scale=ms,
            linewidth=lw,
            color=color,
            linestyle=ls,
            connectionstyle=f"arc3,rad={rad}",
            zorder=4,
            shrinkA=0,
            shrinkB=0,
        )
    )
    if label:
        mx = (start[0] + end[0]) / 2 + label_offset[0]
        my = (start[1] + end[1]) / 2 + label_offset[1]
        ax.text(
            mx,
            my,
            label,
            fontsize=label_size,
            color=MUTED,
            ha="center",
            va="center",
            zorder=5,
            bbox=dict(facecolor=PAPER, edgecolor="none", pad=0.5),
        )


def gate(ax, x, y, w, h, text, *, color=GOOD, fill=GREEN):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.12,rounding_size=0.4",
            linewidth=1.0,
            edgecolor=color,
            facecolor=fill,
            zorder=2,
        )
    )
    ax.text(
        x + 0.7,
        y + h / 2,
        "✓",
        fontsize=7.0,
        color=color,
        va="center",
        ha="left",
        fontweight="bold",
        zorder=3,
    )
    ax.text(
        x + 2.0,
        y + h / 2,
        text,
        fontsize=6.4,
        color=color,
        va="center",
        ha="left",
        zorder=3,
    )


def pill(ax, x, y, w, h, text, *, fill=ACCENT, color=WHITE, edge=None, size=7.2):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.12,rounding_size=0.4",
            linewidth=1.0,
            edgecolor=edge or fill,
            facecolor=fill,
            zorder=3,
        )
    )
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        fontsize=size,
        color=color,
        fontweight="bold",
        ha="center",
        va="center",
        zorder=4,
    )


def legend(ax, items, *, x=2.0, y=4.2):
    cursor = x
    for kind, label in items:
        if kind in {"solid", "dashed", "dotted"}:
            ls = {"solid": "-", "dashed": "--", "dotted": ":"}[kind]
            ax.add_line(
                Line2D(
                    [cursor, cursor + 4.2],
                    [y, y],
                    color=MUTED,
                    lw=1.4,
                    ls=ls,
                    zorder=5,
                )
            )
            cursor += 5.0
        elif kind == "gate":
            ax.add_patch(
                FancyBboxPatch(
                    (cursor, y - 0.7),
                    2.2,
                    1.4,
                    boxstyle="round,pad=0.1,rounding_size=0.3",
                    edgecolor=GOOD,
                    facecolor=GREEN,
                    lw=0.8,
                    zorder=5,
                )
            )
            cursor += 2.8
        else:
            color = {"accent": ACCENT, "muted": MUTED, "risk": RISK}[kind]
            ax.add_line(
                Line2D([cursor, cursor + 1.6], [y, y], color=color, lw=3.2, zorder=5)
            )
            cursor += 2.2
        ax.text(cursor, y, label, fontsize=6.8, color=MUTED, va="center", ha="left")
        cursor += len(label) * 0.46 + 3.0


def footer(ax, text):
    ax.text(2, 1.2, text, fontsize=6.5, color=MUTED, va="bottom", ha="left")


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.png", dpi=150, facecolor=PAPER)
    fig.savefig(OUT / f"{name}.svg", facecolor=PAPER)
    plt.close(fig)


def render_system():
    fig, ax = canvas(
        "Banking analytics data warehouse — system architecture",
        "Local-first build: six source CSVs -> DuckDB galaxy schema -> leakage-safe feature mart -> models, patterns and a six-page review app.",
    )

    zone(ax, 2, 47, 27, 33, "SOURCES — PKDD'99 CSVs")
    zone(ax, 31, 47, 96, 33, "BUILD PLANE — scripts/build_local.py")
    zone(ax, 130, 24, 28, 56, "SERVING — Streamlit")
    zone(ax, 31, 24, 96, 20, "PERSISTED ARTIFACTS — read by the app, never retrained")
    zone(ax, 2, 7, 27, 15, "OPTIONAL CLOUD PATH")

    sources = [
        (
            3.2,
            68.0,
            "loan.csv",
            ["682 rows", "loan_id, account_id", "date, amount, duration,", "payments, status"],
        ),
        (
            16.2,
            68.0,
            "trans.csv",
            ["1,056,320 rows", "trans_id, account_id", "date, type, amount,", "balance, operation"],
        ),
        (3.2, 57.5, "client.csv", ["5,369 rows", "client_id, birth_number,", "district_id"]),
        (16.2, 57.5, "account.csv", ["4,500 rows", "account_id, district_id,", "frequency, date"]),
        (3.2, 47.8, "disp.csv", ["owner mapping", "disp_id, client_id,", "account_id, type"]),
        (16.2, 47.8, "district.csv", ["77 branches", "district_id, A2, A3,", "A4, A10, A11"]),
    ]
    for x, y, title, lines in sources:
        box(ax, x, y, 12.4, 9.2, title, lines, edge=RULE, fill=FILL, title_size=8.2, body_size=6.5)

    box(
        ax,
        32.5,
        72.8,
        93.0,
        4.8,
        "",
        [
            ("scripts/build_local.py — one command, fixed order", WHITE, "bold", 8.6),
            ("python scripts\\build_local.py", "#c9d8e2", "normal", 7.0),
        ],
        edge=ACCENT,
        fill=ACCENT,
    )

    stages = [
        (
            32.5,
            "1 · Extract + transform",
            "etl_pipeline.py",
            [
                "in: data/*.csv",
                "extract 6 CSVs (sep=';')",
                "parse dates + birth numbers",
                "map owners and branches",
                "out: mart.* + data/clean",
            ],
            "gate: no unmapped loans",
        ),
        (
            56.6,
            "2 · Warehouse",
            "data/banking_dw.duckdb",
            [
                "in: clean frames",
                "mart schema",
                "2 facts + 5 dimensions",
                "dim_date 2,191 days",
                "out: data/banking_dw.duckdb",
            ],
            "gate: counts > 0",
        ),
        (
            80.7,
            "3 · Feature mart",
            "03_feature_mart.sql",
            [
                "in: mart.*",
                "transactions before loan date",
                "same-day rows excluded",
                "682 loans × 27 columns",
                "out: analytics.loan_features",
            ],
            "gate: n_txn matches",
        ),
        (
            104.8,
            "4 · Models + patterns",
            "build_advanced_models.py",
            [
                "in: loan_features",
                "MLP + CBA rules",
                "capacity-aware GB",
                "FP-Growth / Apriori",
                "out: artifacts/*",
            ],
            "gate: scores = 682",
        ),
    ]
    for x, title, subtitle, lines, gate_text in stages:
        box(
            ax,
            x,
            57.5,
            21.6,
            14.0,
            title,
            [(subtitle, MUTED, "normal", 7.0), *lines],
            edge=ACCENT,
            fill=BLUE,
            title_size=8.8,
            body_size=7.0,
        )
        gate(ax, x, 49.0, 21.6, 4.6, gate_text)

    artifacts = [
        (
            32.5,
            "artifacts/models",
            ["4 .pkl", "baseline tuned", "capacity-aware", "MLP classifier"],
        ),
        (
            51.9,
            "artifacts/metrics",
            ["8 .csv", "model_scores", "cv_comparison", "advanced_metrics"],
        ),
        (
            71.3,
            "artifacts/rules",
            ["3 .csv", "cba_rules", "pattern_rules", "pattern_itemsets"],
        ),
        (
            90.7,
            "artifacts/segments",
            ["4 .csv", "loan_segments", "cluster_labels", "cluster_profiles"],
        ),
        (
            110.1,
            "data/features",
            ["loan_features.csv", "682 × 27", "Snowflake upload", "notebook input"],
        ),
    ]
    for x, title, lines in artifacts:
        box(
            ax,
            x,
            28.5,
            17.2,
            12.5,
            title,
            lines,
            edge=ACCENT,
            fill=WHITE,
            ls=(0, (3, 2)),
            title_size=8.2,
            body_size=6.6,
        )

    box(
        ax,
        131.5,
        26.5,
        25.0,
        51.0,
        "6-page review app",
        [
            ("Executive overview", INK, "normal", 7.4),
            ("  threshold trade-off", MUTED, "normal", 6.8),
            ("Data & leakage", INK, "normal", 7.4),
            ("  provenance audit", MUTED, "normal", 6.8),
            ("Models", INK, "normal", 7.4),
            ("  CV + held-out checks", MUTED, "normal", 6.8),
            ("Patterns", INK, "normal", 7.4),
            ("  rules + segments", MUTED, "normal", 6.8),
            ("Simulator", INK, "normal", 7.4),
            ("  score one application", MUTED, "normal", 6.8),
            ("Data model card", INK, "normal", 7.4),
            ("  galaxy schema", MUTED, "normal", 6.8),
            ("", INK, "normal", 4.0),
            ("READS", MUTED, "bold", 6.8),
            ("mart.fact_loans", INK, "normal", 7.0),
            ("mart.fact_transactions", INK, "normal", 7.0),
            ("analytics.loan_features", INK, "normal", 7.0),
            ("analytics.model_scores", INK, "normal", 7.0),
            ("artifacts/*.csv + *.pkl", INK, "normal", 7.0),
            ("optional Snowflake MART", INK, "normal", 7.0),
            ("", INK, "normal", 4.0),
            ("RUNS", MUTED, "bold", 6.8),
            ("streamlit run app/streamlit_app.py", INK, "normal", 7.0),
            ("DATA_SOURCE=duckdb | snowflake", INK, "normal", 7.0),
            ("cache ttl 600s", INK, "normal", 7.0),
            ("", INK, "normal", 4.0),
            ("MODES", MUTED, "bold", 6.8),
            ("local: DuckDB mart + artifacts", INK, "normal", 7.0),
            ("hybrid: Snowflake MART + local artifacts", INK, "normal", 7.0),
            ("", INK, "normal", 4.0),
            ("GUARDS", MUTED, "bold", 6.8),
            ("read-only · never retrains", GOOD, "bold", 7.0),
            ("cache ttl 600s · localhost:8501", MUTED, "normal", 6.8),
        ],
        edge=ACCENT,
        fill=BLUE,
        title_size=9.4,
        body_size=7.4,
    )

    box(
        ax,
        3.2,
        16.0,
        24.8,
        4.4,
        "",
        [("upload_to_snowflake.py", WHITE, "bold", 7.2)],
        edge=ACCENT,
        fill=ACCENT,
    )
    box(
        ax,
        3.2,
        11.2,
        24.8,
        3.6,
        "",
        [("Snowflake RAW / MART", INK, "bold", 7.0)],
        edge=ACCENT,
        fill=WHITE,
    )
    box(
        ax,
        3.2,
        7.6,
        24.8,
        2.8,
        "",
        [("Power BI report", INK, "bold", 7.0)],
        edge=ACCENT,
        fill=WHITE,
    )
    arrow(ax, (15.6, 16.0), (15.6, 14.8), ls=":", lw=1.0)
    arrow(ax, (15.6, 11.2), (15.6, 10.4), ls=":", lw=1.0)
    arrow(
        ax,
        (15.6, 47.0),
        (15.6, 22.2),
        ls=":",
        lw=1.2,
        label="upload raw + features",
        label_offset=(0, 0),
    )

    arrow(ax, (29.2, 64.0), (32.3, 64.0))
    arrow(ax, (54.1, 64.0), (56.4, 64.0))
    arrow(ax, (78.2, 64.0), (80.5, 64.0))
    arrow(ax, (102.3, 64.0), (104.6, 64.0))
    arrow(ax, (115.6, 57.5), (115.6, 53.8))
    arrow(ax, (79.0, 49.0), (79.0, 44.4), label="persist")
    arrow(
        ax,
        (126.0, 51.3),
        (131.3, 51.3),
        label="tables",
        label_offset=(0, 1.2),
        label_size=6.0,
    )
    arrow(
        ax,
        (127.2, 34.7),
        (131.3, 34.7),
        label="artifacts",
        label_offset=(-1.6, 1.2),
        label_size=6.0,
    )

    legend(
        ax,
        [
            ("solid", "runtime data flow"),
            ("dashed", "persisted artifact"),
            ("dotted", "optional cloud path"),
            ("gate", "validation gate"),
        ],
        x=31.0,
        y=8.6,
    )
    footer(
        ax,
        "Source: scripts/build_local.py · sql/local/03_feature_mart.sql · artifacts/* · app/streamlit_app.py",
    )
    save(fig, "01_system_architecture")


def render_pipeline():
    fig, ax = canvas(
        "Pipeline architecture — notebooks and production build",
        "Two tracks: notebooks explain the analysis; scripts/build_local.py is the reproducible path that rebuilds every table and artifact.",
    )

    zone(ax, 2, 58, 156, 22, "NOTEBOOK TRACK — exploration and narrative (not imported by the build)")
    zone(ax, 2, 26, 156, 28, "PRODUCTION TRACK — scripts/build_local.py runs these in order")

    notebooks = [
        (
            "01_preprocessing.ipynb",
            ["load 6 CSVs", "clean types, parse dates", "write data/clean snapshots"],
        ),
        (
            "02_features.ipynb",
            ["pre-loan aggregation", "18 model features", "write data/features CSV"],
        ),
        ("03_eda.ipynb", ["distributions", "risk quadrants", "save artifacts/figures"]),
        ("04_modeling.ipynb", ["6 classifiers", "tuning + 50-fold CV", "save models/metrics"]),
        ("05_segmentation.ipynb", ["KMeans k=2", "segment profiles", "save segments"]),
        (
            "06_clustering_comparison.ipynb",
            ["K-medoids, AGNES", "DBSCAN + PCA", "compare clusterings"],
        ),
    ]
    nb_x = [3.0, 28.7, 54.4, 80.1, 105.8, 131.5]
    for x, (title, lines) in zip(nb_x, notebooks):
        box(
            ax,
            x,
            64.0,
            23.8,
            11.0,
            title,
            lines,
            edge=MUTED,
            fill=WHITE,
            ls=(0, (3, 2)),
            title_size=7.6,
            body_size=6.8,
        )

    stages = [
        (
            3.0,
            "1 · Extract",
            "extract_data()",
            [
                "input: data/*.csv",
                "6 CSVs, sep=';'",
                "loan, trans, client,",
                "account, disp, district",
                "out: 6 DataFrames",
            ],
            "files exist",
        ),
        (
            22.5,
            "2 · Transform",
            "transform_dimensions()",
            [
                "input: raw frames",
                "parse birth numbers",
                "owner + branch mapping",
                "5 dims + 2 facts",
                "out: clean frames",
            ],
            "no unknown codes",
        ),
        (
            42.0,
            "3 · Warehouse",
            "load_data()",
            [
                "input: clean frames",
                "DuckDB mart",
                "2 facts + 5 dimensions",
                "data/clean snapshots",
                "out: banking_dw.duckdb",
            ],
            "counts > 0",
        ),
        (
            61.5,
            "4 · Feature mart",
            "03_feature_mart.sql",
            [
                "input: mart.*",
                "pre-loan transactions",
                "682 loans × 27 cols",
                "target B/D = 76",
                "out: loan_features",
            ],
            "no post-loan rows",
        ),
        (
            81.0,
            "5 · Models",
            "build_advanced_models.py",
            [
                "input: loan_features",
                "MLP + CBA rules",
                "capacity-aware GB",
                "50-fold CV",
                "out: metrics + models",
            ],
            "scores = 682",
        ),
        (
            100.5,
            "6 · Patterns + segments",
            "tools/pattern_mining.py",
            [
                "input: loan_features",
                "FP-Growth / Apriori",
                "KMeans, k-medoids",
                "AGNES, DBSCAN",
                "out: rules + segments",
            ],
            "rules >= 1",
        ),
        (
            120.0,
            "7 · Analytics",
            "build_analytics.py",
            [
                "input: artifacts/*",
                "17 CSVs -> DuckDB",
                "analytics schema",
                "artifact check",
                "out: 17 tables",
            ],
            "all files present",
        ),
        (
            139.5,
            "8 · Validate + serve",
            "validate() + Streamlit",
            [
                "input: all tables",
                "row counts, defaults",
                "no post-loan rows",
                "6-page review app",
                "out: localhost:8501",
            ],
            "fail-fast",
        ),
    ]

    for x, title, subtitle, lines, gate_text in stages:
        box(
            ax,
            x,
            36.5,
            17.5,
            13.5,
            title,
            [(subtitle, MUTED, "bold", 6.8), *lines],
            edge=ACCENT,
            fill=BLUE,
            title_size=7.6,
            body_size=6.6,
        )
        gate(ax, x, 31.2, 17.5, 3.6, gate_text)
        if x < 139.5:
            arrow(ax, (x + 17.5, 43.5), (x + 19.5, 43.5), ms=7)

    box(
        ax,
        2.5,
        17.0,
        155.0,
        6.2,
        "",
        [
            ("scripts/build_local.py — one command, fixed order", WHITE, "bold", 8.4),
            (
                "run_etl() -> feature SQL -> export_features() -> build_advanced() -> build_capacity() -> build_patterns() -> build_analytics() -> validate()",
                "#c9d8e2",
                "normal",
                7.0,
            ),
        ],
        edge=ACCENT,
        fill=ACCENT,
    )

    legend(
        ax,
        [
            ("solid", "production order"),
            ("dashed", "notebook exploration"),
            ("gate", "validation gate"),
        ],
        x=3.0,
        y=10.0,
    )
    footer(
        ax,
        "Notebooks are optional. The production track is the reproducible path from raw CSV to the Streamlit app.",
    )
    save(fig, "02_pipeline_architecture")


def render_features():
    fig, ax = canvas(
        "Feature vector — one row per loan, 27 columns",
        "The leakage-safe modelling table: join ownership, keep only pre-loan transactions, aggregate, then label the loan outcome.",
    )

    zone(ax, 2, 47, 38, 33, "SOURCE TABLES — PKDD'99")
    zone(ax, 42, 47, 40, 33, "JOIN + FILTER + AGGREGATE")
    zone(ax, 85, 18, 73, 62, "OUTPUT — analytics.loan_features, 682 × 27")

    sources = [
        (
            3.0,
            68.0,
            "loan.csv",
            ["682 rows", "loan_id, account_id", "date, amount, duration,", "payments, status"],
        ),
        (
            21.5,
            68.0,
            "trans.csv",
            ["1,056,320 rows", "trans_id, account_id", "date, type, amount,", "balance"],
        ),
        (3.0, 57.5, "client.csv", ["5,369 rows", "client_id, birth_number,", "district_id"]),
        (21.5, 57.5, "account.csv", ["4,500 rows", "account_id, district_id,", "frequency, date"]),
        (3.0, 47.8, "disp.csv", ["owner mapping", "disp_id, client_id,", "account_id, type"]),
        (21.5, 47.8, "district.csv", ["77 branches", "district_id, A2, A3,", "A4, A10, A11"]),
    ]
    for x, y, title, lines in sources:
        box(ax, x, y, 17.2, 9.2, title, lines, edge=RULE, fill=FILL, title_size=8.2, body_size=6.5)

    flow = [
        (
            43.5,
            70.5,
            "1 · Join ownership",
            ["disp.type = OWNER", "account_id -> client_id", "account.district_id -> branch"],
        ),
        (
            43.5,
            62.6,
            "2 · Pre-loan window",
            ["t.date_id < loan.date_id", "strictly before the loan", "same-day rows excluded"],
        ),
        (
            43.5,
            54.7,
            "3 · Aggregate per loan",
            ["counts, sums, averages", "min/max balance", "months_active, txn_per_month"],
        ),
        (
            43.5,
            46.8,
            "4 · Label",
            ["status in (B, D) -> target", "76 defaults / 682 = 11.14%"],
        ),
    ]
    for x, y, title, lines in flow:
        box(ax, x, y, 37.0, 6.7, title, lines, edge=ACCENT, fill=BLUE, title_size=8.0, body_size=6.6)

    arrow(ax, (40.2, 65.0), (43.3, 65.0), label="keys", label_offset=(0, 1.0))
    arrow(ax, (62.0, 70.5), (62.0, 69.3), ms=7)
    arrow(ax, (62.0, 62.6), (62.0, 61.4), ms=7)
    arrow(ax, (62.0, 54.7), (62.0, 53.5), ms=7)

    box(
        ax,
        86.5,
        72.0,
        70.0,
        6.0,
        "",
        [("one row per loan · 27 columns · 18 model features", WHITE, "bold", 8.2)],
        edge=ACCENT,
        fill=ACCENT,
    )

    box(
        ax,
        86.5,
        63.0,
        70.0,
        7.4,
        "Identifiers (3)",
        [
            ("loan_id · account_id · client_id", MUTED, "normal", 7.0),
            ("context only; never model inputs", MUTED, "normal", 6.4),
        ],
        edge=RULE,
        fill=FILL,
        badge="0 model",
        badge_color=MUTED,
        title_size=8.4,
        body_size=7.0,
    )
    box(
        ax,
        86.5,
        52.0,
        70.0,
        9.6,
        "Loan record (7)",
        [
            ("amount · duration · payments", ACCENT, "bold", 7.2),
            ("date · parsed_date · status · target", MUTED, "normal", 7.0),
            ("3 of 7 are model features", MUTED, "normal", 6.4),
        ],
        edge=ACCENT,
        fill=BLUE,
        badge="3 model",
        title_size=8.4,
        body_size=7.0,
    )
    box(
        ax,
        86.5,
        32.5,
        70.0,
        18.0,
        "Behaviour, pre-loan (13)",
        [
            ("n_txn · n_deposit · n_withdrawal", ACCENT, "bold", 7.2),
            ("sum_deposit · sum_withdrawal", ACCENT, "bold", 7.2),
            ("avg_amount · std_amount", ACCENT, "bold", 7.2),
            ("avg_balance · min_balance · max_balance", ACCENT, "bold", 7.2),
            ("balance_at_loan · months_active · txn_per_month", ACCENT, "bold", 7.2),
            ("all 13 are model features", MUTED, "normal", 6.4),
        ],
        edge=ACCENT,
        fill=BLUE,
        badge="13 model",
        title_size=8.4,
        body_size=7.0,
    )
    box(
        ax,
        86.5,
        22.0,
        70.0,
        9.0,
        "Demographics (4)",
        [
            ("gender_bin · age", ACCENT, "bold", 7.2),
            ("gender · district_id", MUTED, "normal", 7.0),
            ("2 of 4 are model features", MUTED, "normal", 6.4),
        ],
        edge=ACCENT,
        fill=BLUE,
        badge="2 model",
        title_size=8.4,
        body_size=7.0,
    )

    box(
        ax,
        3.0,
        25.0,
        78.0,
        17.0,
        "LEAKAGE GUARD",
        [
            ("Every transaction is filtered by t.date_id < loan.date_id.", INK, "normal", 7.0),
            ("Post-loan and same-day rows never enter the feature mart.", INK, "normal", 7.0),
            ("Zero-transaction loans survive: LEFT JOIN + COALESCE to 0.", INK, "normal", 7.0),
            ("18 model features exclude ids, raw dates, status and target.", INK, "normal", 7.0),
            ("27 columns = 3 ids + 7 loan + 13 behaviour + 4 demographics.", MUTED, "normal", 6.8),
            ("", INK, "normal", 4.0),
            ("Audit: n_txn equals the pre-loan count for all 682 loans.", GOOD, "normal", 7.0),
            ("Target: status in (B, D) -> 76 defaults (11.14%).", RISK, "bold", 7.0),
        ],
        edge=RISK,
        fill=RED,
        title_color=RISK,
        title_size=9.0,
        body_size=7.0,
    )

    legend(
        ax,
        [
            ("accent", "model feature"),
            ("muted", "identifier / context"),
            ("risk", "target or guard"),
        ],
        x=3.0,
        y=10.0,
    )
    footer(
        ax,
        "Source: sql/local/03_feature_mart.sql · data/features/loan_features.csv · scripts/build_local.py",
    )
    save(fig, "03_feature_vector")


def main():
    render_system()
    render_pipeline()
    render_features()
    print(f"Wrote diagrams to {OUT}")


if __name__ == "__main__":
    main()
