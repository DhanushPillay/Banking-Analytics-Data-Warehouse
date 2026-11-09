"""Patterns and segments page."""

from components.common import *


def patterns_page() -> None:
    features = load_features()
    itemsets = load_output("pattern_itemsets.csv")
    rules = load_output("pattern_rules.csv")
    if itemsets is None or rules is None:
        st.error("Pattern outputs are missing. Run tools/pattern_mining.py.")
        return

    # Both files stack an Apriori and an FP-Growth run. The itemsets file also
    # ends with a six-row legend whose support cells are text, not numbers.
    itemsets = itemsets[itemsets["method"].notna()].copy()
    itemsets["support"] = pd.to_numeric(itemsets["support"], errors="coerce")
    itemsets = itemsets.drop_duplicates(subset=["itemsets"])
    rules = rules.drop_duplicates(subset=["antecedents", "consequents"])

    loans = len(features)
    page_header(
        "Patterns",
        f"{len(itemsets)} itemsets, {len(rules)} rules, one worth a second look",
        "FP-Growth and Apriori over pre-loan behaviour baskets. Support, confidence and lift "
        f"are measured against all {loans} loans.",
    )

    top = rules.sort_values("lift", ascending=False).iloc[0]
    kpi_row(
        [
            ("Itemsets", f"{len(itemsets)}", "Identical across both algorithms"),
            ("Default rules", f"{len(rules)}", "Consequence is default"),
            ("Top-rule support", percent(top["support"]), f"{round(top['support'] * loans)} loans"),
            ("Top-rule lift", f"{top['lift']:.2f}", f"Against the {percent(features['target'].mean())} base rate"),
        ]
    )

    section("The rule worth a second look", "Highest lift in the rule set")
    st.markdown(
        f'<div class="note"><b>Rule</b><span style="font-family:var(--serif);font-size:1.15rem">'
        f"{parse_itemset(top['antecedents'])} → {parse_itemset(top['consequents'])}</span></div>",
        unsafe_allow_html=True,
    )
    grid(
        pd.DataFrame(
            [
                ["Antecedent support", percent(top["antecedent support"])],
                ["Consequent support", percent(top["consequent support"])],
                ["Support", percent(top["support"])],
                ["Confidence", f"{top['confidence']:.2f}"],
                ["Lift", f"{top['lift']:.2f}"],
                ["Conviction", f"{top['conviction']:.1f}"],
            ],
            columns=["Measure", "Value"],
        )
    )
    cases = round(top["support"] * loans)
    note(
        f"All {cases} loans with a negative minimum balance defaulted. "
        f"Confidence 1.00 is a strong signal, but {cases} cases is a small base: the interval "
        "around it is wide. Use it as a screening flag, not an approval rule.",
        label="Reading it",
    )

    section("All rules", f"{len(rules)} rules pass the configured thresholds")
    table = rules.copy()
    table["If"] = table["antecedents"].map(parse_itemset)
    table["Then"] = table["consequents"].map(parse_itemset)
    table["Support %"] = (table["support"] * 100).round(2)
    table["Confidence %"] = (table["confidence"] * 100).round(1)
    grid(
        table[["If", "Then", "Support %", "Confidence %", "lift"]]
        .sort_values("lift", ascending=False)
        .rename(columns={"lift": "Lift"}),
        score_config("Support %", "Lift", places=2) | score_config("Confidence %", places=1),
    )
    st.caption("Both algorithms return the same rules; duplicates are collapsed.")

    cba = load_output("cba_rules.csv")
    if cba is not None and len(cba):
        section("Classifier rules", "CBA-style rules mined from binned behaviour")
        view = cba.copy()
        view["Coverage %"] = (view["coverage"] * 100).round(1)
        view["Confidence %"] = (view["confidence"] * 100).round(1)
        view["Coverage"] = (view["coverage"] * 100).round(1)
        view["Defaults"] = (view["coverage"] * loans).round().astype(int)
        view["Label"] = view["Defaults"].astype(str) + " defaults"
        view["Rule"] = view["antecedents"].map(parse_itemset).str.replace("_", " ")
        bars = (
            alt.Chart(view)
            .mark_bar()
            .encode(
                y=alt.Y("Rule:N", sort="-x", title=None, axis=alt.Axis(labelLimit=300, labelOverlap=False)),
                x=alt.X("Coverage:Q", title="Coverage (%)", scale=alt.Scale(domain=[0, float(view["Coverage"].max()) * 1.4])),
                color=alt.value(ACCENT),
                tooltip=[
                    "Rule",
                    alt.Tooltip("Coverage:Q", format=".1f"),
                    "Defaults",
                    alt.Tooltip("support:Q", format=".3f"),
                    alt.Tooltip("confidence:Q", format=".3f"),
                    alt.Tooltip("lift:Q", format=".2f"),
                ],
            )
        )
        labels = alt.Chart(view).mark_text(align="left", dx=6, color=INK, fontSize=9, clip=True).encode(
            y=alt.Y("Rule:N", sort="-x", title=None),
            x="Coverage:Q",
            text="Label:N",
        )
        show((bars + labels).properties(height=max(260, len(view) * 36)).interactive())
        grid(
            view[["antecedents", "support", "Confidence %", "lift", "Coverage %"]].rename(
                columns={
                    "antecedents": "If",
                    "support": "Support",
                    "lift": "Lift",
                }
            ),
            score_config("Support", places=3) | score_config("Lift", places=2),
        )
        st.caption(
            "Mined on the full modelling table with fixed, interpretable bins. "
            "Every rule fires on a negative minimum balance and has confidence 1.0 and lift 8.97, "
            "so coverage is the only differentiator. The label counts the defaulted loans each rule covers."
        )

    section("Itemsets", f"Apriori and FP-Growth return the same {len(itemsets)} sets")
    threshold = st.slider("Minimum support", 0, 100, 20, step=5)
    table = itemsets.copy()
    table["Support %"] = (table["support"] * 100).round(2)
    filtered = table[table["Support %"] >= threshold].sort_values("Support %", ascending=False)
    table_view = filtered.assign(Items=filtered["itemsets"].map(parse_itemset))[["Items", "Support %"]]
    top = table_view.head(12).assign(Items=lambda x: x["Items"].str.replace("_", " "))
    show(
        alt.Chart(top)
        .mark_bar()
        .encode(
            y=alt.Y("Items:N", sort="-x", title=None, axis=alt.Axis(labelLimit=300, labelOverlap=False)),
            x=alt.X("Support %:Q", title="Support (%)"),
            color=alt.value(ACCENT),
            tooltip=["Items", alt.Tooltip("Support %:Q", format=".1f")],
        )
        .properties(height=max(260, len(top) * 28))
        .interactive()
    )
    grid(table_view)
    st.caption(
        f"{len(filtered)} of {len(itemsets)} itemsets at support ≥ {threshold}%. "
        "Support counts the share of loans that contain the set."
    )

    profiles = load_output("cluster_profiles.csv")
    if profiles is not None and len(profiles):
        section(
            "Cluster comparison",
            "K-medoids, AGNES (Ward) and DBSCAN on the same standardised behaviour space",
        )
        names = METHOD_NAMES
        view = profiles.copy()
        view["Method"] = view["method"].map(names).fillna(view["method"])
        view["Segment"] = view["cluster"].map(lambda value: "noise" if value == -1 else str(value))
        view["Loans"] = view["size"]
        view["Share %"] = (view["size"] / loans * 100).round(1)
        view["Default %"] = (view["default_rate"] * 100).round(1)
        base_rate = float(features["target"].mean()) * 100
        x_min = float(view["avg_balance"].min())
        x_max = float(view["avg_balance"].max())
        base_rule = (
            alt.Chart(
                pd.DataFrame({"x": [x_min, x_max], "y": [base_rate, base_rate]})
            )
            .mark_line(color=MUTED, strokeDash=[3, 3], clip=True)
            .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"))
        )
        show(
            (
                base_rule
                + alt.Chart(view)
                .mark_circle(opacity=0.8)
                .encode(
                    x=alt.X("avg_balance:Q", title="Average balance (CZK)"),
                    y=alt.Y("Default %:Q", title="Default rate (%)"),
                    size=alt.Size(
                        "Loans:Q",
                        scale=alt.Scale(range=[60, 600], zero=False),
                        title="Loans",
                    ),
                    color=alt.Color(
                        "Method:N",
                        scale=alt.Scale(
                            domain=["K-medoids", "AGNES", "DBSCAN"],
                            range=[ACCENT, GOOD, RISK],
                        ),
                        title=None,
                    ),
                    tooltip=[
                        "Method",
                        "Segment",
                        "Loans",
                        alt.Tooltip("Default %:Q", format=".1f"),
                        alt.Tooltip("avg_balance:Q", format=",.0f"),
                    ],
                )
            )
            .properties(height=300)
            .interactive()
        )
        grid(
            view[
                [
                    "Method",
                    "Segment",
                    "Loans",
                    "Share %",
                    "Default %",
                    "avg_amount",
                    "avg_balance",
                    "avg_age",
                    "avg_n_txn",
                ]
            ].rename(
                columns={
                    "avg_amount": "Avg amount",
                    "avg_balance": "Avg balance",
                    "avg_age": "Avg age",
                    "avg_n_txn": "Avg transactions",
                }
            ),
            score_config("Avg amount", "Avg balance", places=0)
            | score_config("Avg age", "Avg transactions", places=1),
        )
        worst = profiles.sort_values("default_rate", ascending=False).iloc[0]
        worst_name = names.get(worst["method"], worst["method"])
        worst_segment = "noise" if worst["cluster"] == -1 else f"segment {worst['cluster']}"
        note(
            f"The highest default rate is {worst['default_rate']:.1%} in the "
            f"{worst_name} {worst_segment} ({worst['size']} loans). "
            "DBSCAN isolates a high-risk noise group; K-medoids and AGNES split the core "
            "book into broader behaviour bands.",
            label="Reading it",
        )

        section("Default rate by cluster", "Red bars sit above the portfolio base rate")
        show(cluster_rate_figure(profiles, features["target"].mean()))
        st.caption(
            "Each bar is one segment from the table. DBSCAN labels unassigned loans as noise."
        )

        labels = load_output("cluster_labels.csv")
        if labels is not None and len(labels):
            section("Cluster map", "PCA projection of the same standardised behaviour features")
            columns = st.columns(3)
            for column, (title, figure) in zip(columns, cluster_map_figures(features, labels)):
                column.markdown(f"**{title}**")
                with column:
                    show(figure)
            st.caption(
                "Nearby points have similar pre-loan behaviour. PCA compresses the feature "
                "space to two axes, so distances are approximate; exact numbers stay in the table."
            )


# ------------------------------------------------------------------ simulator
