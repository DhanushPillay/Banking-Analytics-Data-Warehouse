# Power BI Build Guide — Banking DW (user builds PBIX manually)

Source: `docs/` here + CSVs in `data/` / `outputs/`. No Snowflake connection from repo side.

## 1. Files to upload to Snowflake (you do this in Snowsight)

| CSV | Target table | Rows |
|---|---|---|
| `data/loan.csv` | RAW.LOAN | 682 |
| `data/trans.csv` | RAW.TRANS (~68 MB) | 1,056,320 |
| `outputs/loan_risk_dashboard.csv` | MART.LOAN_RISK | 682 |
| `outputs/loan_segments.csv` | MART.LOAN_SEGMENT | 682 |

Run `sql/ddl_snowflake.sql` in order (warehouse → DB/schemas → file formats → tables → COPY → views → grants → validation).

## 2. Power BI: Get Data → Snowflake

Server `<org>-<acct>.snowflakecomputing.com`, Warehouse `PBI_WH`, Role `PBI_READER`, Database `LOAN_DEFAULT_DW`. Import mode. Load `MART.LOAN_RISK`, `MART.LOAN_SEGMENT`, `MART.V_LOAN_PERF`, `MART.V_TRANS_MONTHLY`.

## 3. Model relationships

- `LOAN_SEGMENT[loan_id]` 1—1 `LOAN_RISK[loan_id]` (or merge into one table)
- `V_TRANS_MONTHLY[account_id]` *—1 `LOAN_RISK[account_id]`
- Single direction, star. Keep `target`, `prob_default`, `segment` as columns.

## 4. Measures (DAX)

```
Loans N = COUNTROWS(LOAN_RISK)
Defaults N = CALCULATE([Loans N], LOAN_RISK[target]=1)
Default Rate = DIVIDE([Defaults N],[Loans N])        // baseline 11.14%
Avg Prob = AVERAGE(LOAN_RISK[prob_default])
```

What-if threshold: Modeling → New parameter → Numeric 0.05–0.95 step 0.01 default 0.50 (creates `Threshold` table). Then:

```
Threshold Value = SELECTEDVALUE('Threshold'[ThresholdValue], 0.5)
TP = SUMX(LOAN_RISK, IF(LOAN_RISK[prob_default] >= [Threshold Value] && LOAN_RISK[target]=1, 1, 0))
FP = SUMX(LOAN_RISK, IF(LOAN_RISK[prob_default] >= [Threshold Value] && LOAN_RISK[target]=0, 1, 0))
FN = SUMX(LOAN_RISK, IF(LOAN_RISK[prob_default] <  [Threshold Value] && LOAN_RISK[target]=1, 1, 0))
TN = SUMX(LOAN_RISK, IF(LOAN_RISK[prob_default] <  [Threshold Value] && LOAN_RISK[target]=0, 1, 0))
Precision = DIVIDE([TP],[TP]+[FP])
Recall    = DIVIDE([TP],[TP]+[FN])
F1        = DIVIDE(2*[Precision]*[Recall],[Precision]+[Recall])
Flagged Rate = DIVIDE([TP]+[FP],[Loans N])
```

Predicted label must stay a measure (never a calculated column — a column would freeze the threshold).

## 5. Pages (5)

1. **Overview** — KPIs (Loans N, Defaults N, Default Rate vs 11.14%, Avg Prob). Default-rate-by-year bar, gender/age bars, top-region table. Slicers: year, gender, age_group, segment.
2. **Transactions** — monthly deposit/withdrawal line (`V_TRANS_MONTHLY`), balance boxplot by target, txn/month histogram.
3. **Model lab** — Threshold slider + TP/FP/TN/FN cards, Precision/Recall/F1 live cards, prob histogram (good vs default overlap). Static note: GB baseline repeated-CV F1 0.571 ± 0.120; top-4 configs overlap within std bars, winner not clearly separated.
4. **Segments** — Seg0 421 @12.4% vs Seg1 261 @9.2% bar, avg_balance-vs-txn/month scatter, profile table. Note silhouette 0.29 = overlapping clouds.
5. **Loan drill-through** — target page on `loan_id`: customer, dates, amount/duration/payments, target, prob_default, predicted label at current threshold, segment, 13 behavior features. Right-click any loan_id → Drill through.

## 6. Publish + refresh

Publish to workspace (Pro license min). Dataset Settings → Data source credentials → Schedule refresh (Pro: up to 8/day). No gateway needed (Snowflake is a cloud source).
