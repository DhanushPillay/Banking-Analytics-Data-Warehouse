"""Join notebook outputs into one dashboard-ready table. Run after 04 + 05."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

feat = pd.read_csv(ROOT / "data" / "loan_features.csv")
scores = pd.read_csv(OUT / "model_scores.csv")
seg = pd.read_csv(OUT / "loan_segments.csv")

assert len(feat) == len(scores) == len(seg) == 682
assert (scores["prob_default"].between(0, 1)).all()

risk = feat.merge(scores[["loan_id", "prob_default"]], on="loan_id", how="left")
risk = risk.merge(seg, on="loan_id", how="left")
assert risk["prob_default"].notna().all() and risk["segment"].notna().all()

risk.to_csv(OUT / "loan_risk_dashboard.csv", index=False)
print(risk.shape, "mean prob:", round(float(risk["prob_default"].mean()), 4))
print("saved loan_risk_dashboard.csv")
