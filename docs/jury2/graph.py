"""Render an AWS-architecture-style diagram for the loan-default project."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


OUTPUT = Path(__file__).with_name("loan_default_system_architecture.png")


def service(ax, x, y, label, subtitle, color, width=0.13, height=0.09):
    """Draw a compact architecture service tile."""
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.004,rounding_size=0.008",
            facecolor="#ffffff",
            edgecolor="#a7adb4",
            linewidth=0.9,
        )
    )
    ax.add_patch(
        FancyBboxPatch(
            (x + 0.008, y + height - 0.032),
            0.028,
            0.024,
            boxstyle="round,pad=0.002,rounding_size=0.004",
            facecolor=color,
            edgecolor=color,
        )
    )
    ax.text(
        x + 0.022,
        y + height - 0.020,
        "●",
        ha="center",
        va="center",
        color="white",
        fontsize=7,
        fontweight="bold",
    )
    ax.text(
        x + 0.043,
        y + height - 0.019,
        label,
        color="#252a30",
        fontsize=7.2,
        fontweight="bold",
        va="center",
    )
    ax.text(
        x + width / 2,
        y + 0.020,
        subtitle,
        color="#4e565e",
        fontsize=6.6,
        ha="center",
        va="center",
        linespacing=1.15,
    )


def arrow(ax, start, end, label=None, color="#606870", dashed=False):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=9,
            linewidth=0.9,
            linestyle="--" if dashed else "-",
            color=color,
            connectionstyle="arc3,rad=0",
        )
    )
    if label:
        x = (start[0] + end[0]) / 2
        y = (start[1] + end[1]) / 2 + 0.012
        ax.text(x, y, label, color="#606870", fontsize=6.2, ha="center")


def boundary(ax, x, y, width, height, title, color):
    ax.add_patch(
        Rectangle(
            (x, y),
            width,
            height,
            facecolor="#fbfcfd",
            edgecolor=color,
            linewidth=1.0,
            linestyle=(0, (3, 2)),
        )
    )
    ax.text(
        x + 0.008,
        y + height - 0.015,
        title,
        color=color,
        fontsize=7.5,
        fontweight="bold",
        va="top",
    )


def main():
    fig, ax = plt.subplots(figsize=(16, 9), dpi=180)
    fig.patch.set_facecolor("#eee8ff")
    ax.set_facecolor("#ffffff")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.5,
        0.965,
        "Loan Default Classification — System Architecture",
        ha="center",
        va="top",
        color="#17202a",
        fontsize=17,
        fontweight="bold",
    )
    ax.text(
        0.5,
        0.935,
        "Offline data mining and model training with a Streamlit decision-support layer",
        ha="center",
        va="top",
        color="#59636d",
        fontsize=8.5,
    )

    # Main architecture zones, styled like cloud region/VPC boundaries.
    boundary(ax, 0.035, 0.56, 0.28, 0.29, "DATA INGESTION ZONE", "#4d9ac5")
    boundary(ax, 0.35, 0.56, 0.30, 0.29, "FEATURE ENGINEERING ZONE", "#6aa84f")
    boundary(ax, 0.67, 0.56, 0.295, 0.29, "MODEL TRAINING ZONE", "#8e6bb8")
    boundary(ax, 0.10, 0.12, 0.80, 0.30, "PERSISTENCE AND SERVING ZONE", "#e47d35")

    # Ingestion.
    service(ax, 0.055, 0.70, "Raw banking CSVs", "loan • trans • client\naccount • disp", "#4d9ac5", 0.16)
    service(ax, 0.055, 0.59, "Data validation", "schema checks\nmissing values", "#4d9ac5", 0.16)
    service(ax, 0.235, 0.70, "Notebook 01", "preprocessing\nloan target labels", "#4d9ac5", 0.095)
    service(ax, 0.235, 0.59, "Source archive", "historical PKDD'99\nread-only inputs", "#4d9ac5", 0.095)

    # Features.
    service(ax, 0.37, 0.70, "Relational join", "client ↔ account ↔ loan", "#6aa84f", 0.13)
    service(ax, 0.515, 0.70, "Temporal filter", "transactions before\nloan date only", "#6aa84f", 0.13)
    service(ax, 0.37, 0.59, "Behavior features", "balance, counts,\ncredit/debit metrics", "#6aa84f", 0.13)
    service(ax, 0.515, 0.59, "Feature table", "682 loans • 27 columns\nloan_features.csv", "#6aa84f", 0.13)

    # Training.
    service(ax, 0.69, 0.70, "EDA", "risk signals\ncorrelations", "#8e6bb8", 0.115)
    service(ax, 0.82, 0.70, "Model training", "6 classifiers\nbaseline + SMOTE", "#8e6bb8", 0.13)
    service(ax, 0.69, 0.59, "Tuning + CV", "stratified split\nrepeated validation", "#8e6bb8", 0.115)
    service(ax, 0.82, 0.59, "Pattern mining", "K-Means • Apriori\nFP-Growth", "#8e6bb8", 0.13)

    # Storage and serving.
    service(ax, 0.14, 0.28, "Dataset store", "data/loan_features.csv", "#e47d35", 0.15)
    service(ax, 0.32, 0.28, "Model registry", "best Gradient Boosting\npipeline (.pkl)", "#e47d35", 0.15)
    service(ax, 0.50, 0.28, "Results store", "metrics • figures\nsegments • rules", "#e47d35", 0.15)
    service(ax, 0.68, 0.28, "Streamlit app", "reads persisted artifacts\nlocalhost:8501", "#e47d35", 0.15)
    service(ax, 0.82, 0.28, "Human review", "risk simulator\nrecommendations", "#e47d35", 0.13)

    # Flows.
    arrow(ax, (0.215, 0.745), (0.235, 0.745), "load")
    arrow(ax, (0.283, 0.70), (0.37, 0.745), "clean")
    arrow(ax, (0.50, 0.745), (0.515, 0.745))
    arrow(ax, (0.45, 0.70), (0.435, 0.68))
    arrow(ax, (0.58, 0.70), (0.58, 0.68))
    arrow(ax, (0.58, 0.59), (0.69, 0.635), "features")
    arrow(ax, (0.69, 0.745), (0.82, 0.745))
    arrow(ax, (0.755, 0.70), (0.755, 0.68))
    arrow(ax, (0.885, 0.70), (0.885, 0.68))

    # Cross-zone artifact flows.
    arrow(ax, (0.58, 0.59), (0.215, 0.37), "persist", dashed=True)
    arrow(ax, (0.755, 0.59), (0.395, 0.37), dashed=True)
    arrow(ax, (0.885, 0.59), (0.575, 0.37), dashed=True)
    arrow(ax, (0.745, 0.28), (0.82, 0.325), "serve")
    arrow(ax, (0.82, 0.28), (0.89, 0.28), "review")

    ax.text(
        0.5,
        0.075,
        "Dashed arrows = persisted artifacts    |    Solid arrows = runtime/data flow    |    Human approval remains outside the model",
        ha="center",
        color="#626a72",
        fontsize=7.5,
    )
    fig.savefig(OUTPUT, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    main()
