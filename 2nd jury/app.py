from ast import literal_eval
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"

# Existing page palette, kept so charts sit inside the CSS rather than fight it.
BLUE = "#3a86ff"
CORAL = "#ff595e"
INK = "#202124"
MUTED = "#6b7075"
PAPER = "#f7f7f2"
RULE = "#e4e3db"


def styled(chart: alt.Chart, height: int = 280) -> alt.Chart:
    """Apply the page's ink and paper so Altair matches the hand-written CSS."""
    return (
        chart.properties(height=height)
        .configure_view(strokeWidth=0, fill=PAPER)
        .configure_title(color=INK, fontSize=13, fontWeight=600, anchor="start", offset=8)
        .configure_axis(
            labelColor=MUTED,
            titleColor=INK,
            titleFontSize=11,
            gridColor=RULE,
            domain=False,
            tickSize=0,
        )
        .configure_legend(labelColor=MUTED, titleColor=INK, orient="top", symbolType="square")
    )


st.set_page_config(
    page_title="Loan Default Intelligence",
    page_icon="◧",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --ink: #202124; --blue: #3a86ff; --coral: #ff595e; --citrus: #ffca3a; --paper: #f7f7f2; }
    [data-testid="stAppViewContainer"] { background: var(--paper); color: var(--ink); }
    [data-testid="stSidebar"] { background: #202124; border-right: 4px solid var(--coral); }
    [data-testid="stSidebar"] * { color: #f7f7f2; }
    [data-testid="stMetricValue"] { color: var(--ink); font-size: 1.55rem; letter-spacing: -0.01em; }
    [data-testid="stMetricLabel"] { color: #6b7075; }
    h1, h2, h3 { color: var(--ink); letter-spacing: 0; }
    .block-container { max-width: 1320px; padding-top: 2.2rem; }
    .hero { padding: 0.4rem 0 0.8rem; }
    .eyebrow { color: var(--blue); font-size: 0.75rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; }
    .muted { color: #5c6268; font-size: 1rem; }
    .signal { background: #eef4ff; border-left: 4px solid var(--blue); padding: 0.85rem 1rem; margin: 0.5rem 0 1.2rem; }
    .sidebar-title { color: var(--citrus); font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; font-size: 0.72rem; }
    .sidebar-note { color: #d6dde0; font-size: 0.82rem; line-height: 1.45; }
    [data-testid="stSidebar"] [role="radiogroup"] label p { color: #f7f7f2; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(OUTPUTS / name)


@st.cache_data
def load_features() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "loan_features.csv")


def load_optional_csv(name: str) -> pd.DataFrame | None:
    path = OUTPUTS / name
    return pd.read_csv(path) if path.exists() else None


def format_metric(value: float) -> str:
    return f"{value:.3f}"


def show_header(eyebrow: str, title: str, description: str) -> None:
    st.markdown(
        f'<div class="hero"><div class="eyebrow">{eyebrow}</div>'
        f"<h1>{title}</h1><p class='muted'>{description}</p></div>",
        unsafe_allow_html=True,
    )


def show_project_pulse() -> None:
    st.sidebar.markdown('<div class="sidebar-title">Project pulse</div>', unsafe_allow_html=True)
    st.sidebar.metric("Applications", "682")
    pulse_left, pulse_right = st.sidebar.columns(2)
    pulse_left.metric("Defaults", "76")
    pulse_right.metric("Base rate", "11.1%")
    st.sidebar.markdown(
        '<div class="sidebar-note">Historical PKDD\'99 banking data<br>Pre-loan behavioral evidence only</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.divider()


def comparison_page() -> None:
    metrics = load_csv("metrics_comparison.csv")
    cv = load_csv("cv_comparison.csv")
    segments = load_csv("segment_profiles.csv")

    show_header(
        "01 / Model comparison",
        "Which model earns the review seat?",
        "A single held-out split is shown alongside repeated cross-validation, so model choice is not driven by one lucky test split.",
    )

    metric_options = {
        "F1 score": ("cv_f1_mean", "cv_f1_std"),
        "Average precision": ("cv_ap_mean", "cv_ap_std"),
        "ROC-AUC": ("cv_auc_mean", "cv_auc_std"),
    }
    controls = st.columns([1.2, 1, 1])
    metric_label = controls[0].selectbox("Rank models by", list(metric_options))
    setting = controls[1].selectbox("Balance treatment", ["baseline", "smote"], format_func=str.title)
    variant = controls[2].selectbox("Model state", ["tuned", "default"], format_func=str.title)
    metric_column, spread_column = metric_options[metric_label]
    selected = cv[(cv["setting"] == setting) & (cv["variant"] == variant)].copy()
    ranking = selected.sort_values(metric_column, ascending=False).reset_index(drop=True)
    best = ranking.iloc[0]
    runner_up = ranking.iloc[1]
    margin = best[metric_column] - runner_up[metric_column]
    spread = best[spread_column]
    st.caption("Scores are repeated stratified 5-fold x 10 cross-validation.")

    lead = st.columns([1, 2.4])
    lead[0].metric(f"Best on {metric_label}", f"{best['model']}")
    lead[1].caption(
        f"{best[metric_column]:.3f} ± {spread:.3f} on {setting} / {variant}. "
        f"Average precision {best['cv_ap_mean']:.3f}, ROC-AUC {best['cv_auc_mean']:.3f}. "
        f"Margin over {runner_up['model']} is {margin:.3f}. "
        "Scores are repeated stratified 5-fold x 10 cross-validation."
    )
    st.markdown(
        f'<div class="signal"><b>Is the margin real?</b> The whisker on each bar is the spread across '
        f'repeated folds, not a confidence interval. {best["model"]} leads {runner_up["model"]} by '
        f'{margin:.3f} and carries a spread of {spread:.3f} on its own score, so the two are '
        f'{"separated" if margin > spread else "not separated"} by the variation this dataset shows.</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Pick a run, then read it in the charts below")
    runs_view = selected.copy()
    runs_view["configuration"] = runs_view["setting"] + " / " + runs_view["variant"]
    sorted_view = runs_view.sort_values("cv_f1_mean", ascending=False)
    readable = sorted_view[
        ["model", "configuration", "cv_f1_mean", "cv_f1_std", "cv_ap_mean", "cv_auc_mean"]
    ].rename(
        columns={
            "model": "Model",
            "configuration": "Configuration",
            "cv_f1_mean": "F1 mean",
            "cv_f1_std": "F1 spread",
            "cv_ap_mean": "Average precision",
            "cv_auc_mean": "ROC-AUC",
        }
    )
    runs = st.dataframe(
        readable.style.format(
            {column: "{:.3f}" for column in ["F1 mean", "F1 spread", "Average precision", "ROC-AUC"]}
        ),
        on_select="rerun",
        selection_mode="single-row",
        key="run_pick",
        width="stretch",
        hide_index=True,
    )
    picked_rows = runs.selection.rows if runs and runs.selection else []
    picked_model = sorted_view.iloc[picked_rows[0]]["model"] if picked_rows else None
    st.caption(
        f"{picked_model} is picked out in both charts." if picked_model
        else "Select a row to pick that model out in both charts."
    )

    left, right = st.columns(2)
    with left:
        st.subheader(f"Which model leads on {metric_label.lower()}?")
        bars = ranking.rename(columns={metric_column: "score", spread_column: "spread"}).copy()
        bars["low"] = (bars["score"] - bars["spread"]).clip(lower=0)
        bars["high"] = bars["score"] + bars["spread"]
        bars["hot"] = bars["model"] == picked_model
        bars["dim"] = bars["model"] != picked_model if picked_model else False
        leaderboard = (
            alt.Chart(bars)
            .mark_bar(cornerRadiusEnd=2)
            .encode(
                y=alt.Y("model:N", sort=alt.SortField("score", order="descending"), title=None),
                x=alt.X(
                    "score:Q",
                    title=f"{metric_label}, whisker = fold spread",
                    scale=alt.Scale(domain=[0, float(bars["high"].max()) * 1.06]),
                ),
                color=alt.condition("datum.hot", alt.value(CORAL), alt.value(BLUE)),
                opacity=alt.condition("datum.dim", alt.value(0.4), alt.value(1)),
                tooltip=[
                    alt.Tooltip("model:N", title="Model"),
                    alt.Tooltip("score:Q", title=metric_label, format=".3f"),
                    alt.Tooltip("spread:Q", title="Fold spread", format=".3f"),
                    alt.Tooltip("cv_ap_mean:Q", title="Average precision", format=".3f"),
                    alt.Tooltip("cv_auc_mean:Q", title="ROC-AUC", format=".3f"),
                ],
            )
        )
        whiskers = (
            alt.Chart(bars)
            .mark_tick(color=INK, strokeWidth=1.3, size=70)
            .encode(
                y=alt.Y("model:N", sort=alt.SortField("score", order="descending"), title=None),
                x="low:Q",
                x2="high:Q",
            )
        )
        st.altair_chart(styled(alt.layer(leaderboard, whiskers), height=300), width="stretch")
    with right:
        st.subheader("Does the F1 leader also rank borrowers best?")
        tuned_baseline = cv[(cv["setting"] == "baseline") & (cv["variant"] == "tuned")].copy()
        tuned_baseline["hot"] = tuned_baseline["model"] == picked_model
        tuned_baseline["dim"] = tuned_baseline["model"] != picked_model if picked_model else False
        dots = (
            alt.Chart(tuned_baseline)
            .mark_circle(opacity=0.9)
            .encode(
                x=alt.X("cv_f1_mean:Q", title="Tuned F1 mean", scale=alt.Scale(zero=False)),
                y=alt.Y("cv_auc_mean:Q", title="Tuned ROC-AUC mean", scale=alt.Scale(zero=False)),
                color=alt.condition("datum.hot", alt.value(CORAL), alt.value(BLUE)),
                opacity=alt.condition("datum.dim", alt.value(0.4), alt.value(1)),
                tooltip=[
                    alt.Tooltip("model:N", title="Model"),
                    alt.Tooltip("cv_f1_mean:Q", title="F1 mean", format=".3f"),
                    alt.Tooltip("cv_f1_std:Q", title="F1 spread", format=".3f"),
                    alt.Tooltip("cv_ap_mean:Q", title="Average precision", format=".3f"),
                    alt.Tooltip("cv_auc_mean:Q", title="ROC-AUC", format=".3f"),
                ],
            )
        )
        labelled = tuned_baseline.nlargest(2, "cv_f1_mean")
        names = (
            alt.Chart(labelled)
            .mark_text(dy=-16, fontSize=11, color=INK, align="left")
            .encode(x="cv_f1_mean:Q", y="cv_auc_mean:Q", text="model:N")
        )
        st.altair_chart(styled(alt.layer(dots, names), height=300), width="stretch")

    with st.expander("See the held-out default-setting table"):
        st.dataframe(
            metrics.rename(
                columns={
                    "model": "Model",
                    "setting": "Balance treatment",
                    "accuracy": "Accuracy",
                    "precision": "Precision",
                    "recall": "Recall",
                    "f1": "F1",
                    "average_precision": "Average precision",
                    "roc_auc": "ROC-AUC",
                }
            ).style.format(
                {column: "{:.3f}" for column in ["Accuracy", "Precision", "Recall", "F1", "Average precision", "ROC-AUC"]}
            ),
            width="stretch",
            hide_index=True,
        )

    st.subheader("Behavior segments")
    segment_cards = st.columns(len(segments))
    for card, (_, segment) in zip(segment_cards, segments.iterrows()):
        card.metric(f"Segment {int(segment['segment'])} default rate", f"{segment['default_rate']:.1%}")
        card.caption(f"{int(segment['size'])} loans | {segment['n_txn']:.0f} average transactions")

    st.subheader("Portfolio risk lens")
    st.caption("Adjust the review cutoffs to see how balance capacity and loan size divide the portfolio. This is a screening view, not a lending rule.")
    features = load_features()
    balance_median = round(float(features["balance_at_loan"].median()) / 1000) * 1000.0
    amount_median = round(float(features["amount"].median()) / 1000) * 1000.0
    balance_min = round(float(features["balance_at_loan"].quantile(0.10)) / 1000) * 1000.0
    balance_max = round(float(features["balance_at_loan"].quantile(0.90)) / 1000) * 1000.0
    amount_min = round(float(features["amount"].quantile(0.10)) / 1000) * 1000.0
    amount_max = round(float(features["amount"].quantile(0.90)) / 1000) * 1000.0
    risk_controls = st.columns(2)
    balance_cutoff = risk_controls[0].slider(
        "Balance-at-loan cutoff",
        min_value=balance_min,
        max_value=balance_max,
        value=balance_median,
        step=1000.0,
    )
    amount_cutoff = risk_controls[1].slider(
        "Loan amount cutoff",
        min_value=amount_min,
        max_value=amount_max,
        value=amount_median,
        step=1000.0,
    )
    features = features.copy()
    features["risk_quadrant"] = (
        features["balance_at_loan"].ge(balance_cutoff).map({True: "Higher balance", False: "Lower balance"})
        + " / "
        + features["amount"].ge(amount_cutoff).map({True: "Higher loan", False: "Lower loan"})
    )
    risk_table = (
        features.groupby("risk_quadrant", as_index=False)
        .agg(loans=("target", "size"), defaults=("target", "sum"), default_rate=("target", "mean"))
        .sort_values("default_rate", ascending=False)
    )
    risk_table = risk_table.assign(
        worst=risk_table["default_rate"] == risk_table["default_rate"].max()
    )
    portfolio_rate = float(features["target"].mean())
    quadrant_chart = (
        alt.Chart(risk_table)
        .mark_bar(cornerRadiusEnd=2)
        .encode(
            y=alt.Y("risk_quadrant:N", sort=alt.SortField("default_rate", order="descending"), title=None),
            x=alt.X("default_rate:Q", title="Default rate", axis=alt.Axis(format=".0%")),
            color=alt.condition("datum.worst", alt.value(CORAL), alt.value(BLUE)),
            tooltip=[
                alt.Tooltip("risk_quadrant:N", title="Quadrant"),
                alt.Tooltip("loans:Q", title="Loans"),
                alt.Tooltip("defaults:Q", title="Defaulted"),
                alt.Tooltip("default_rate:Q", title="Default rate", format=".1%"),
            ],
        )
    )
    base_line = (
        alt.Chart(pd.DataFrame({"rate": [portfolio_rate]}))
        .mark_rule(color=INK, strokeDash=[4, 3], strokeWidth=1.2)
        .encode(x="rate:Q")
    )
    st.altair_chart(
        styled(alt.layer(quadrant_chart, base_line), height=220),
        width="stretch",
    )
    st.caption(f"Dashed line is the portfolio default rate of {portfolio_rate:.1%}.")
    highest_risk = risk_table.iloc[0]
    st.markdown(
        f'<div class="signal"><b>Highest observed quadrant:</b> {highest_risk["risk_quadrant"]} '
        f'with {highest_risk["default_rate"]:.1%} default rate across {int(highest_risk["loans"])} loans. '
        "Use this to prioritize investigation, not to automate approval decisions.</div>",
        unsafe_allow_html=True,
    )


def best_model_page() -> None:
    cv = load_csv("cv_comparison.csv")
    metrics = load_csv("metrics_comparison.csv")
    tuned_baseline = cv[(cv["setting"] == "baseline") & (cv["variant"] == "tuned")].copy()
    best = tuned_baseline.sort_values("cv_f1_mean", ascending=False).iloc[0]
    model_metrics = metrics[metrics["model"] == best["model"]]

    show_header(
        "02 / Model rationale",
        f"Why {best['model']} is the headline model",
        "The selection is grounded in repeated validation, then checked against precision, ranking quality, imbalance handling, and business cost.",
    )

    st.info(
        f"The selected configuration is tuned {best['model']} with the unresampled baseline arm. "
        f"It leads on repeated-CV F1 at {best['cv_f1_mean']:.3f} ± {best['cv_f1_std']:.3f}."
    )

    rf = tuned_baseline[tuned_baseline["model"] == "RandomForest"].iloc[0]
    lead_gap = best["cv_f1_mean"] - rf["cv_f1_mean"]
    st.markdown(
        f'<div class="signal"><b>Decision boundary:</b> Gradient Boosting leads Random Forest by only '
        f'{lead_gap:.3f} F1 points, while Random Forest leads on Average Precision and ROC-AUC. '
        "Use Gradient Boosting as the headline classifier and keep Random Forest as the ranking challenger.</div>",
        unsafe_allow_html=True,
    )

    reasons = st.columns(3)
    reasons[0].metric("F1", f"{best['cv_f1_mean']:.3f} ± {best['cv_f1_std']:.3f}")
    reasons[1].metric("Average precision", f"{best['cv_ap_mean']:.3f}")
    reasons[2].metric("ROC-AUC", f"{best['cv_auc_mean']:.3f}")

    st.subheader("The decision in plain language")
    st.markdown(
        """
        - **Repeated validation:** Gradient Boosting is the top configuration on the stated F1 selection rule.
        - **No automatic SMOTE:** the unresampled arm is stronger for the leading ensemble; repeated validation is more reliable than the original single split.
        - **A close alternative:** Random Forest is a defensible ranking model because it leads on Average Precision and ROC-AUC. The margin is smaller than the fold-to-fold spread.
        - **Business signal:** low `min_balance` and `balance_at_loan` are the strongest observed default signals, so the model complements a balance-capacity review rather than replacing it.
        """
    )

    figure = FIGURES / "rf_importance.png"
    if figure.exists():
        st.image(str(figure), caption="Reference feature importance from the tuned Random Forest model.", width="stretch")

    st.subheader("Selected model on the held-out split")
    st.dataframe(model_metrics, width="stretch", hide_index=True)
    st.caption("The held-out table is a reference check. The model selection itself uses repeated cross-validation.")

    with st.expander("What would change the decision?"):
        st.markdown(
            "Use a recent portfolio, nested cross-validation, and an explicit cost matrix before deployment. "
            "If ranking quality becomes more important than F1 classification, Random Forest is the natural challenger."
        )


def as_item_set(value: str) -> frozenset:
    """mlxtend writes itemsets as frozenset({...}), which literal_eval alone will not read."""
    inner = str(value).strip()
    if inner.startswith("frozenset(") and inner.endswith(")"):
        inner = inner[len("frozenset(") : -1]
    return frozenset(literal_eval(inner))


def parse_itemset(value: str) -> str:
    try:
        parsed = literal_eval(value)
        return ", ".join(sorted(str(item) for item in parsed))
    except (ValueError, SyntaxError):
        return value


BEHAVIOUR = [
    "n_txn", "n_deposit", "n_withdrawal", "sum_deposit", "sum_withdrawal",
    "avg_amount", "std_amount", "avg_balance", "min_balance", "max_balance",
    "balance_at_loan", "months_active", "txn_per_month",
]

TERMS_AND_DEMOGRAPHICS = ["amount", "duration", "payments", "age", "gender_bin"]


def borrower_page() -> None:
    loans = load_csv("loan_risk_dashboard.csv").sort_values("prob_default", ascending=False)
    n_loans, n_default = len(loans), int(loans["target"].sum())

    show_header(
        "03 / Review queue",
        "Set a cutoff. See who gets caught.",
        "Probabilities come from stratified 5-fold cross-validation, so every loan is scored by a model "
        "that never trained on it. A cutoff decides which loans a reviewer opens first; it does not decide "
        "who gets a loan.",
    )

    st.subheader("What a cutoff costs")
    cutoff = st.slider(
        "Flag a loan when its default probability is at or above",
        0.0, 1.0, 0.50, 0.01,
    )
    flagged = loans["prob_default"] >= cutoff
    tp = int((flagged & (loans["target"] == 1)).sum())
    fp = int((flagged & (loans["target"] == 0)).sum())
    fn = int((~flagged & (loans["target"] == 1)).sum())
    tn = int((~flagged & (loans["target"] == 0)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    matrix = pd.DataFrame(
        [[tp, fn], [fp, tn]],
        index=pd.Index(["Actually defaulted", "Actually repaid"], name=""),
        columns=["Flagged for review", "Not flagged"],
    )
    left, right = st.columns([1.1, 1])
    with left:
        st.dataframe(matrix, width="stretch")
        st.caption(
            f"{precision:.1%} of flagged loans really defaulted. "
            f"{recall:.1%} of the {n_default} real defaulters were caught. F1 {f1:.3f}."
        )
    with right:
        sweep = [0.05 + step * 0.01 for step in range(91)]
        curve = pd.DataFrame({"cutoff": sweep})
        curve["predicted"] = [int((loans["prob_default"] >= c).sum()) for c in sweep]
        curve["caught"] = [
            int(((loans["prob_default"] >= c) & (loans["target"] == 1)).sum()) for c in sweep
        ]
        long_curve = curve.rename(
            columns={"predicted": "Flagged for review", "caught": "Actually defaulted"}
        ).melt(
            id_vars="cutoff",
            value_vars=["Flagged for review", "Actually defaulted"],
            var_name="series",
            value_name="loans",
        )
        y_max = max(int(curve["predicted"].max()), n_loans * 0.25)
        nearest = alt.selection_point(nearest=True, on="pointerover", fields=["cutoff"], empty=False)

        x_axis = alt.X("cutoff:Q", title="Probability cutoff", scale=alt.Scale(domain=[0.05, 0.95]))
        gap_band = (
            alt.Chart(curve)
            .mark_area(color=CORAL, opacity=0.18)
            .encode(x=x_axis, y=alt.Y("caught:Q", title="Loans"), y2=alt.Y2("predicted:Q"))
        )
        lines = (
            alt.Chart(long_curve)
            .mark_line(strokeWidth=2.2)
            .encode(
                x=x_axis,
                y=alt.Y("loans:Q", title="Loans", scale=alt.Scale(domain=[0, y_max])),
                color=alt.Color(
                    "series:N",
                    scale=alt.Scale(
                        domain=["Flagged for review", "Actually defaulted"],
                        range=[MUTED, CORAL],
                    ),
                    legend=alt.Legend(title=None, orient="top-left"),
                ),
                tooltip=[
                    alt.Tooltip("cutoff:Q", title="Cutoff", format=".2f"),
                    alt.Tooltip("series:N"),
                    alt.Tooltip("loans:Q", title="Loans"),
                ],
            )
            .add_params(nearest)
        )
        marker = (
            alt.Chart(pd.DataFrame({"cutoff": [cutoff]}))
            .mark_rule(color=BLUE, strokeWidth=1.6, strokeDash=[5, 3])
            .encode(x=alt.X("cutoff:Q", scale=alt.Scale(domain=[0.05, 0.95])))
        )
        st.altair_chart(
            styled(alt.layer(gap_band, lines, marker), height=300),
            width="stretch",
        )
        st.caption(
            "Shaded area is the gap between the two lines: loans flagged for review that did not default. "
            "Hover the curve for a readout, dashed line is the cutoff currently selected."
        )

    if tp + fp == 0:
        st.info(
            f"At a cutoff of {cutoff:.2f} no loan is flagged, so precision and recall are undefined. "
            "Lower the cutoff until at least one loan crosses it."
        )
    elif recall < 0.6:
        st.warning(
            f"{fn} of the {n_default} defaulters sit below {cutoff:.2f} and will not be seen. "
            "Lowering the cutoff finds them at the cost of more false alarms."
        )

    st.subheader("The queue a reviewer would open")
    queue = loans[loans["prob_default"] >= cutoff].sort_values("prob_default", ascending=False).copy()
    queue["outcome"] = queue["target"].map({1: "Defaulted", 0: "Repaid"})
    queue["segment"] = queue["segment"].map(lambda value: f"Segment {int(value)}")
    queue["flagged"] = queue["prob_default"] >= cutoff
    if len(queue):
        st.caption(
            f"{len(queue)} loans cross {cutoff:.2f}, of which {tp} defaulted. "
            "Click any row to inspect that loan below."
        )
    else:
        queue = loans.sort_values("prob_default", ascending=False).copy()
        queue["outcome"] = queue["target"].map({1: "Defaulted", 0: "Repaid"})
        queue["segment"] = queue["segment"].map(lambda value: f"Segment {int(value)}")
        queue["flagged"] = queue["prob_default"] >= cutoff
        st.caption(
            f"No loan crosses {cutoff:.2f}, so the whole portfolio is listed instead. "
            "Click any row to inspect that loan below."
        )

    picker = st.dataframe(
        queue[["loan_id", "prob_default", "outcome", "segment", "flagged", "amount", "balance_at_loan", "months_active", "n_txn"]]
        .style.format({"prob_default": "{:.3f}", "amount": "{:,.0f}", "balance_at_loan": "{:,.0f}"}),
        on_select="rerun",
        selection_mode="single-row",
        key="loan_pick",
        width="stretch",
        hide_index=True,
        height=320,
    )
    picked_rows = picker.selection.rows if picker and picker.selection else []
    chosen = int(queue.iloc[picked_rows[0]]["loan_id"]) if picked_rows else int(queue.iloc[0]["loan_id"])

    st.subheader(f"Loan {chosen} in full")
    st.caption(
        "Every loan here was granted in the 1999 PKDD'99 data, so the outcome is known. "
        "Use this to check whether the score agrees with what the account actually did."
    )
    row = loans[loans["loan_id"] == chosen].iloc[0]

    detail = st.columns(4)
    detail[0].metric("Default probability", f"{row['prob_default']:.3f}")
    detail[1].metric("Outcome", "Defaulted" if row["target"] else "Repaid")
    detail[2].metric("Segment", f"{int(row['segment'])}")
    detail[3].metric("Months of history", f"{row['months_active']:.0f}")

    st.markdown(
        f'<div class="signal"><b>Loan {int(row["loan_id"])}:</b> {int(row["amount"]):,} over '
        f'{int(row["duration"])} months, {int(row["payments"]):,} a month. Flagged at a cutoff of '
        f'{cutoff:.2f}: {"yes" if row["prob_default"] >= cutoff else "no"}. '
        f'It {"defaulted" if row["target"] else "was repaid"} in the source data.</div>',
        unsafe_allow_html=True,
    )

    st.caption("Where this loan sits against the other 681, by percentile. 50 is the middle borrower.")
    correlations = loans[BEHAVIOUR + TERMS_AND_DEMOGRAPHICS].corrwith(loans["target"])
    profile = []
    for column in BEHAVIOUR + TERMS_AND_DEMOGRAPHICS:
        series = loans[column]
        percentile = float((series < row[column]).mean() * 100)
        leans_risk = bool(correlations[column] > 0) == (percentile > 50)
        profile.append(
            {
                "feature": column,
                "value": row[column],
                "median": series.median(),
                "percentile": percentile,
                "leans_risk": leans_risk,
                "correlation": float(correlations[column]),
            }
        )
    profile = pd.DataFrame(profile)

    profile_chart = (
        alt.Chart(profile)
        .mark_bar(cornerRadiusEnd=2)
        .encode(
            y=alt.Y(
                "feature:N",
                sort=alt.SortField("percentile", order="descending"),
                title=None,
            ),
            x=alt.X(
                "percentile:Q",
                title="Percentile among the 682 loans",
                scale=alt.Scale(domain=[0, 100]),
            ),
            color=alt.condition("datum.leans_risk", alt.value(CORAL), alt.value(BLUE)),
            tooltip=[
                alt.Tooltip("feature:N", title="Feature"),
                alt.Tooltip("value:Q", title="This loan", format=",.1f"),
                alt.Tooltip("median:Q", title="Population median", format=",.1f"),
                alt.Tooltip("percentile:Q", title="Percentile", format=".0f"),
                alt.Tooltip("correlation:Q", title="Correlation with default", format="+.2f"),
            ],
        )
    )
    middle = (
        alt.Chart(pd.DataFrame({"p": [50]}))
        .mark_rule(color=INK, strokeWidth=1)
        .encode(x="p:Q")
    )
    st.altair_chart(
        styled(alt.layer(profile_chart, middle), height=460),
        width="stretch",
    )
    st.caption(
        "Coral marks a trait whose value here leans toward default, blue one that leans away. "
        "Direction comes from each feature's correlation with the target, so it can differ per feature."
    )


def patterns_page() -> None:
    itemsets = load_optional_csv("pattern_itemsets.csv")
    rules = load_optional_csv("pattern_rules.csv")

    show_header(
        "04 / Pattern recognition",
        "What recurring behaviors travel together?",
        "FP-Growth and Apriori turn pre-loan account activity into interpretable baskets and default-oriented association rules.",
    )

    if itemsets is None or rules is None:
        st.warning("Pattern outputs have not been generated yet. The dashboard is ready, but the mining script still needs to run.")
        st.code("python tools/pattern_mining.py", language="powershell")
        st.markdown("Run the command from the repository root, then reload this page to populate the tables.")
        return

    cards = st.columns(3)
    cards[0].metric("FP-Growth itemsets", int((itemsets["method"] == "fpgrowth").sum()))
    cards[1].metric("Apriori itemsets", int((itemsets["method"] == "apriori").sum()))
    cards[2].metric("Default-oriented rules", len(rules))

    mined = itemsets.copy()
    mined["item_set"] = mined["itemsets"].map(as_item_set)
    mined = mined.drop_duplicates(subset="item_set")
    support_lookup = dict(zip(mined["item_set"], mined["support"]))
    default_item = (
        "default" if frozenset({"default"}) in support_lookup else "default_before_loan"
    )
    base_rate = float(
        support_lookup.get(frozenset({default_item}), float("nan"))
    )

    candidates = []
    for _, row in mined.iterrows():
        if default_item not in row["item_set"]:
            continue
        antecedent = frozenset(row["item_set"] - {default_item})
        antecedent_support = support_lookup.get(antecedent)
        if not antecedent or not antecedent_support:
            continue
        confidence = float(row["support"]) / float(antecedent_support)
        candidates.append(
            {
                "antecedent": " + ".join(sorted(antecedent)),
                "confidence": confidence,
                "lift": confidence / base_rate if base_rate else float("nan"),
            }
        )
    candidates = pd.DataFrame(candidates).sort_values("confidence", ascending=False).head(12)

    st.subheader(
        "Default-oriented association rules"
        if not candidates.empty
        else "Why did mining return no default rules?"
    )
    if candidates.empty:
        st.info(
            f"The mining output has no itemset containing {default_item}, so there is nothing "
            "to compare against the threshold. Re-run tools/pattern_mining.py to regenerate it."
        )
    else:
        best_confidence = float(candidates["confidence"].max())
        x_max = 1.0 if best_confidence > 0.45 else 0.45
        confidence_chart = (
            alt.Chart(candidates)
            .mark_bar(cornerRadiusEnd=2, color=CORAL)
            .encode(
                y=alt.Y("antecedent:N", sort=alt.SortField("confidence", order="descending"), title=None),
                x=alt.X(
                    "confidence:Q",
                    title="Confidence that default follows the antecedent",
                    scale=alt.Scale(domain=[0, x_max]),
                ),
                tooltip=[
                    alt.Tooltip("antecedent:N", title="Antecedent"),
                    alt.Tooltip("confidence:Q", title="Confidence", format=".3f"),
                    alt.Tooltip("lift:Q", title="Lift", format=".2f"),
                ],
            )
        )
        threshold_rule = (
            alt.Chart(pd.DataFrame({"c": [0.40]}))
            .mark_rule(color=INK, strokeWidth=1.4, strokeDash=[5, 3])
            .encode(x="c:Q")
        )
        base_rule = (
            alt.Chart(pd.DataFrame({"b": [base_rate]}))
            .mark_rule(color=MUTED, strokeWidth=1.2)
            .encode(x="b:Q")
        )
        st.altair_chart(
            styled(alt.layer(confidence_chart, base_rule, threshold_rule), height=320),
            width="stretch",
        )
        st.caption(
            f"The strongest candidate reaches {best_confidence:.3f} confidence against a 0.40 "
            f"threshold. The grey line is the portfolio default rate of {base_rate:.1%}. "
            "The table below lists the rules retained by the mining script; Apriori and "
            "FP-Growth return the same rules on this dataset."
        )

    itemsets = itemsets.copy()
    itemsets["items"] = itemsets["itemsets"].map(parse_itemset)
    st.subheader("Most frequent patterns")
    st.dataframe(
        itemsets[["method", "items", "support"]].sort_values("support", ascending=False).head(20),
        width="stretch",
        hide_index=True,
    )

    rules = rules.copy()
    rules["if_behavior"] = rules["antecedents"].map(parse_itemset)
    st.subheader("Rules whose consequence is default")
    if rules.empty:
        st.info("No rule reaches the configured confidence threshold. This is a finding, not a dashboard error.")
        st.caption("Try a lower confidence threshold in tools/pattern_mining.py only as a sensitivity analysis; do not compare thresholds as if they were the same experiment.")
    else:
        st.dataframe(
            rules[["method", "if_behavior", "support", "confidence", "lift"]].sort_values("lift", ascending=False),
            width="stretch",
            hide_index=True,
        )


page = st.sidebar.radio(
    "Explore",
    ["Model comparison", "Why the best model", "Review queue", "FP-Growth & patterns"],
)
show_project_pulse()
st.sidebar.divider()
st.sidebar.caption("PKDD'99 loan default classification\nPre-loan behavioral evidence")

if page == "Model comparison":
    comparison_page()
elif page == "Why the best model":
    best_model_page()
elif page == "Review queue":
    borrower_page()
else:
    patterns_page()