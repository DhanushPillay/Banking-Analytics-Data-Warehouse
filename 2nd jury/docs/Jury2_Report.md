# Project Report: Customer Behavioral Analysis and Loan Default Classification

## 1. Problem Definition and Objectives

The objective of this project is to run the complete data mining pipeline, from data preprocessing to model evaluation, on the PKDD'99 Financial Dataset. The task is to predict loan default risk from customer transaction behavior.

Each loan is classified into one of two outcomes: likely to repay (good loan) or likely to default (bad loan). The prediction uses only information available before the loan was granted, so the model reflects what the bank could have known at decision time. The business goal is to identify risky behavioral patterns early enough to reduce loan losses. This covers the classification and prediction outcomes of Units III and IV.

## 2. Dataset Description and Source

The project uses the PKDD'99 Financial Dataset, real anonymized records of a Czech bank covering 1993 to 1998. The same dataset was used for the Jury 1 data warehouse. Five tables are used:

- `loan.csv` (682 rows): one row per granted loan. Columns are loan id, account id, grant date, amount, duration in months, installment amount (`payments`), and status code. Status codes A (finished, no problems) and C (running, no problems) map to good loans (606). Codes B (finished, unpaid) and D (running, in debt) map to defaults (76). The default rate is 11.14 percent, so the classes are imbalanced.
- `trans.csv` (1,056,320 rows): one row per account transaction from 1993-01-01 to 1998-12-31. Types are PRIJEM (credit, 405,083 rows), VYDAJ (debit, 634,571 rows), and VYBER (cash withdrawal, 16,666 rows). The `operation`, `k_symbol`, `bank`, and `account` columns contain many nulls (183k to 783k), which is expected: they only apply to certain transaction modes. Only the type, amount, balance, account id, and date columns are used for features.
- `client.csv` (5,369 rows): client id, birth number, and district id. The birth number encodes date of birth and gender (month values above 50 indicate female clients). Derived split: 2,645 female, 2,724 male.
- `account.csv` (4,500 rows): account id, district id, statement frequency, and creation date. Listed for provenance; account-level features come from the transaction table instead.
- `disp.csv` (5,369 rows): links between clients and accounts. 4,500 OWNER relations and 869 DISPONENT relations. Only OWNER links are used, so each loan maps to exactly one client.

## 3. Data Preprocessing Pipeline

The pipeline is implemented in `notebooks/01_preprocessing.ipynb` and `notebooks/02_features.ipynb`.

**Data cleaning.** No duplicate rows exist in any of the five tables. All loan and transaction dates parse under the `%y%m%d` format with zero failures. The transaction mode columns with nulls were left untouched because they are not used. Derived ages were sanity checked to fall between 0 and 100.

**Feature engineering.** For each of the 682 loans, all transactions of the loan account dated strictly before the loan grant date were aggregated into 13 behavioral features: transaction count, deposit and withdrawal counts and totals, mean and standard deviation of amounts, mean/min/max balance, balance on the last transaction before the loan (`balance_at_loan`), months of account history, and transactions per month. Loan terms (amount, duration, installment) and demographics (age, gender as binary, district id) were joined to the same row. Every loan had prior transaction history (minimum 2 transactions), so all 682 rows were kept. The result is saved as `data/loan_features.csv` (682 rows, 27 columns).

**Transformation.** The 18 modeling features are all numeric. Gender is binary encoded. Continuous features are standardized with `StandardScaler` inside the modeling pipelines, fitted on the training split only, so no test information leaks into training.

## 4. Exploratory Data Analysis (EDA) and Visualizations

Implemented in `notebooks/03_eda.ipynb`. Figures are stored in `outputs/figures/`.

- **Target distribution** (`target_dist.png`): 606 good loans against 76 defaults. The imbalance motivates the baseline-versus-balanced comparison in modeling.
- **Correlation with default** (`corr_target.png`): the strongest signals are low `min_balance` (-0.26), low `balance_at_loan` (-0.20), and low `avg_balance` (-0.16). Larger loan `amount` (+0.17) and higher `payments` (+0.18) point modestly toward default. Age (+0.01) and gender (+0.02) carry almost no signal.
- **Behavior comparison** (`behavior_box.png`): median balance at loan time is about 39.5k for good loans versus 22.0k for defaulted loans; median average balance is 44.1k versus 37.0k. Transaction frequency is nearly identical (5.7 versus 5.6 per month), so balance levels separate the classes more than activity levels do.
- **Age distribution** (`age_hist.png`): defaults occur across all age groups with no visible concentration, consistent with the near-zero age correlation.
- **Data quality** (printed tables): no missing values or duplicates in `loan_features.csv`; skewed money columns and overdrafts (`min_balance` down to -17k) noted; `sum_deposit`/`sum_withdrawal` correlate at 0.997 and count features cluster together, so balance levels are preferred over raw volumes.
- **Full feature correlations** (`corr_full.png`): confirms multicollinearity among volume features; `amount`/`payments` move together, which is why importance is read jointly with correlation.
- **Categorical split**: female 11.8% vs male 10.5% default; `status` mapping A/C good, B/D default holds exactly.
- **Risk quadrant** (`risk_quadrant.png`): crossing the portfolio at the median pre-loan balance (38.5k) and the median loan amount (116.9k) separates the four quadrants cleanly. Default rates are 4.9% for high balance with low amount, 6.7% for high balance with high amount, 10.1% for low balance with low amount, and 23.3% for low balance with high amount. The two signals reinforce each other rather than overlapping, and the worst quadrant runs at twice the portfolio base rate.
- **Customer segments** (`segments_default.png`, `segments_scatter.png`, from `05_segmentation.ipynb`): KMeans on the 13 behavioral features, with the target excluded from clustering, selects k=2 by silhouette score (0.29, so the structure is modest and the segments are broad tendencies, not sharp groups). Segment 0 (421 borrowers) transacts less (median 54 transactions, average balance 37.2k) and defaults at 12.4 percent. Segment 1 (261 borrowers) is more active (median 116 transactions, average balance 52.4k) and defaults at 9.2 percent. The scatter of average balance versus transactions per month shows two overlapping clouds rather than separated groups, which matches the modest silhouette score. Activity and balance levels move together, and the quieter, thinner-balance group carries the higher risk.

## 5. Implementation of Classification Algorithms

Implemented in `notebooks/04_modeling.ipynb` with scikit-learn 1.7.0. The 18 modeling features are numeric. The data is split 75/25 with stratification (train 511 rows with 57 defaults; test 171 rows with 19 defaults; seed 42). `StandardScaler`, SMOTE, and the estimator all sit inside the pipeline, so every fit, including every cross-validation fold, learns scaling and resampling from training data only. Six classifiers are trained:

1. **Decision Tree**: captures nonlinear splits and stays interpretable.
2. **Naive Bayes** (Gaussian): probabilistic baseline.
3. **Random Forest** (200 trees): ensemble for accuracy and feature importance.
4. **SVM**: strong separator for small imbalanced data. Wrapped in `CalibratedClassifierCV(ensemble=False)`, because `SVC(probability=True)` is deprecated in scikit-learn 1.9 and removed in 1.11, and the ROC and precision-recall curves need probabilities.
5. **KNN** (k=5): distance baseline.
6. **Gradient Boosting**: boosted-tree alternative to Random Forest.

Each classifier runs in two imbalance settings, on the raw imbalanced training data (baseline) and on SMOTE-balanced training data, giving 12 configurations. Because a single split holds only 19 defaults and its ranking is not stable, selection does not use it. The evaluation protocol has four steps:

1. **Default hyperparameters on the held-out test set**, producing `outputs/metrics_comparison.csv`, the confusion matrices, the ROC curves and the precision-recall curves. This is a readable reference table, not the selection basis.
2. **Hyperparameter search.** `RandomizedSearchCV` runs once per model and setting (12 searches), scored on F1 by inner 5-fold stratified CV and fitted on the **training split only**, so nothing about the test set influences the search. Up to 30 candidates are drawn per search from a per-model grid that ranges from 9 combinations (Naive Bayes, which has only one tunable parameter) to 240 (Random Forest). Results, best parameters, and search time land in `outputs/tuning_results.csv`; `tuning_curves.png` shows inner-CV F1 against the decisive hyperparameter for the two strongest model families.
3. **Repeated cross-validation.** `RepeatedStratifiedKFold(5, 10)` gives 50 estimates per configuration and is run over all 24 combinations of 6 models x 2 imbalance settings x {default, tuned}. This produces `outputs/cv_comparison.csv`, which is the selection table, and `cv_selection.png`, which plots default against tuned F1 with the spread shown as error bars.
4. **Selection and persistence.** The winner is the configuration with the highest repeated-CV F1 mean. Its pipeline is refitted on the training split and saved to `outputs/models/best_GradientBoosting_baseline_tuned.pkl`, so the reported test metrics stay reproducible.

Random Forest remains the reference model for feature importance, read from the tuned baseline estimator produced in step 2 rather than from a separate refit.

## 6. Performance Comparison using Evaluation Metrics

Two tables are reported. The first is the single held-out split at default hyperparameters. The second is the repeated cross-validation that the selection actually rests on.

**Table 1. Held-out test set, 171 rows with 19 defaults, default hyperparameters** (`outputs/metrics_comparison.csv`):

| Model | Setting | Accuracy | Precision | Recall | F1 | Avg. Precision | ROC-AUC |
|---|---|---|---|---|---|---|---|
| RandomForest | baseline | 0.924 | 0.875 | 0.368 | 0.519 | 0.582 | 0.856 |
| DecisionTree | baseline | 0.895 | 0.529 | 0.474 | 0.500 | 0.309 | 0.711 |
| GradientBoosting | baseline | 0.912 | 0.700 | 0.368 | 0.483 | 0.583 | 0.816 |
| SVM | baseline | 0.918 | 0.857 | 0.316 | 0.462 | 0.551 | 0.771 |
| NaiveBayes | baseline | 0.807 | 0.150 | 0.158 | 0.154 | 0.171 | 0.634 |
| KNN | baseline | 0.895 | 1.000 | 0.053 | 0.100 | 0.220 | 0.668 |
| GradientBoosting | smote | 0.889 | 0.500 | 0.421 | 0.457 | 0.495 | 0.741 |
| DecisionTree | smote | 0.883 | 0.471 | 0.421 | 0.444 | 0.262 | 0.681 |
| RandomForest | smote | 0.895 | 0.538 | 0.368 | 0.438 | 0.532 | 0.826 |
| SVM | smote | 0.854 | 0.375 | 0.474 | 0.419 | 0.385 | 0.726 |
| KNN | smote | 0.743 | 0.195 | 0.421 | 0.267 | 0.156 | 0.645 |
| NaiveBayes | smote | 0.591 | 0.108 | 0.368 | 0.167 | 0.155 | 0.563 |

**Table 2. Repeated stratified 5-fold x 10 cross-validation, 50 estimates per row** (`outputs/cv_comparison.csv`, ranked by tuned F1):

| Model (setting) | F1 default | F1 tuned | AP tuned | AUC tuned |
|---|---|---|---|---|
| GradientBoosting (baseline) | 0.557 | **0.571** ± 0.120 | 0.654 | 0.864 |
| DecisionTree (baseline) | 0.491 | 0.557 ± 0.126 | 0.507 | 0.748 |
| RandomForest (baseline) | 0.557 | 0.556 ± 0.112 | **0.661** | **0.877** |
| RandomForest (smote) | 0.537 | 0.542 ± 0.103 | 0.638 | 0.872 |
| GradientBoosting (smote) | 0.542 | 0.536 ± 0.101 | 0.641 | 0.851 |
| SVM (baseline) | 0.421 | 0.498 ± 0.128 | 0.603 | 0.842 |
| DecisionTree (smote) | 0.452 | 0.464 ± 0.104 | 0.307 | 0.741 |
| SVM (smote) | 0.436 | 0.463 ± 0.084 | 0.608 | 0.848 |
| KNN (smote) | 0.336 | 0.367 ± 0.065 | 0.367 | 0.768 |
| NaiveBayes (baseline) | 0.325 | 0.325 ± 0.132 | 0.356 | 0.769 |
| NaiveBayes (smote) | 0.318 | 0.318 ± 0.055 | 0.338 | 0.729 |
| KNN (baseline) | 0.198 | 0.223 ± 0.129 | 0.249 | 0.628 |

Confusion matrices for all 12 single-split runs are in `confusion_matrices.png`, ROC curves in `roc_curves.png`, and precision-recall curves in `pr_curves.png`. Random Forest feature importance (`rf_importance.png`, from the tuned baseline estimator) ranks `min_balance` (0.261) and `balance_at_loan` (0.116) at the top, followed by `txn_per_month` (0.071), `payments` (0.062), `amount` (0.056), and `avg_balance` (0.051), while `age` (0.025) and `gender_bin` (0.005) sit at the bottom.

**What the added testing changed.** Four findings came out of the tuning and repeated cross-validation, and two of them revise what the single split suggested.

- **The top three are tied, not ranked.** Gradient Boosting wins on the stated criterion at F1 0.571 ± 0.120, but Decision Tree (0.557) and Random Forest (0.556) sit 0.014 and 0.015 behind, against a standard deviation of 0.11 to 0.13. No configuration in the leading group is reliably better than another on F1 at 682 loans and 76 defaults. Random Forest is in fact the better model on the metrics that measure ranking quality, leading Average Precision (0.661 vs 0.654) and ROC-AUC (0.877 vs 0.864). Decision Tree's third place is an artifact of fold luck: its Average Precision is 0.507 and its ROC-AUC 0.748, well behind both.
- **SMOTE does not help where it matters.** At tuned settings the baseline arm beats the SMOTE arm for five of the six models: Gradient Boosting 0.571 vs 0.536, Decision Tree 0.557 vs 0.464, Random Forest 0.556 vs 0.542, SVM 0.498 vs 0.463, Naive Bayes 0.325 vs 0.318. The single split made SMOTE look helpful for Random Forest and Decision Tree; repeated cross-validation shows the gain was noise, and that resampling costs accuracy and precision on the models that were already strong. The one real gain is KNN, from 0.223 to 0.367, and KNN stays the weakest model either way. So SMOTE is best read as a way to force a weak learner to catch more defaulters at a precision cost, not as an improvement to a strong ensemble.
- **Tuning is not what made the difference.** The gain from searching hyperparameters is large only for SVM (+0.077) and Decision Tree (+0.066). It is +0.014 for Gradient Boosting, -0.001 for Random Forest, and exactly zero for Naive Bayes, whose single parameter was already at its optimum. The 50-estimate protocol, not the search, is what made this comparison trustworthy.
- **Average Precision reorders the field.** With 11 percent prevalence, ROC-AUC flatters models that cannot find the positive class: Naive Bayes holds AUC 0.769 while its AP is 0.356, and baseline KNN drops from AUC 0.674 to AP 0.249. AP is reported alongside ROC-AUC throughout for this reason.

Three cautions belong with these numbers. First, 76 defaults is a small base, and F1 differences below roughly 0.05 fall inside the fold-to-fold spread, so the table should be read as tiers rather than as an ordering. Second, the hyperparameters were searched against the whole training split, so the tuned cross-validation scores are mildly optimistic; nested cross-validation would remove that bias, and at 682 rows it was judged not worth the extra runtime given that the bias is small next to the spread. Third, Naive Bayes underperforms clearly and serves only as a baseline.

### 6.1 Pattern mining with Apriori and FP-Growth

A supplementary Unit III step mines account-level baskets built from transactions dated before the first loan. Each transaction contributes independent labels for type (`PRIJEM`, `VYDAJ`, `VYBER`), high amount (above the pre-loan 75th percentile), and negative balance; an account's basket is the union of those labels. The target `default` is added as the rule consequent, not as a behavioral antecedent. Apriori and FP-Growth run at minimum support 0.03 and maximum itemset length 3 (`tools/pattern_mining.py`).

Both algorithms return the same 41 itemsets. After dropping rules at or below the base rate and removing redundant supersets, two default-oriented rules remain:

| Antecedent | Support | Confidence | Lift |
|---|---|---|---|
| `negative_balance` | 0.0396 (27/682) | 1.000 | 8.97 |
| `type_VYBER` | 0.0704 (48/682) | 0.130 | 1.17 |

The negative-balance rule is a high-precision, low-coverage screen: it flags 27 accounts, all 27 of which default, covering 35.5% of the 76 defaults. The cash-withdrawal rule is barely above the 11.1% base rate and is not actionable. The 27-case base is small, so the negative-balance rule should be read as a screening signal for the review queue, not as a causal claim or a replacement for the classifier. The two algorithms agree because the basket matrix is small and sparse; the comparison is a consistency check, not evidence that one is faster here.

## 7. Conclusions and Recommendations

**Selected model.** Tuned Gradient Boosting on the imbalanced baseline arm, at repeated cross-validated F1 0.571 ± 0.120, Average Precision 0.654, and ROC-AUC 0.864. It wins the stated selection rule, and the precision it held on the held-out split at default settings (0.700, Table 1) is what makes it usable: false alarms carry a cost, since every flagged good customer is a loan the bank might refuse. It should be read with the tie it belongs to. Random Forest scores the same on F1 within noise and beats it on both Average Precision (0.661) and ROC-AUC (0.877), so if the bank wants to rank applications by risk rather than make a yes-or-no call, Random Forest is the better choice, and switching to it means re-running the two search and cross-validation steps with the other model. Decision Tree's third place is not a real third place. The honest summary is that Gradient Boosting and Random Forest form one leading group and either is defensible, with Gradient Boosting taken as the headline because the protocol names repeated cross-validated F1 as the criterion.

**What the testing changed.** The single split originally ranked Random Forest first and made SMOTE balancing look beneficial. Neither held up. SMOTE lowers F1 for five of the six models and its only gain is on KNN, the weakest learner, so the recommended default is the unresampled baseline. Hyperparameter search mattered for SVM (+0.077) and Decision Tree (+0.066), the two models whose default settings were furthest from their own optimum, and barely at all for the ensembles. The real gain came from the evaluation design rather than the search: 50 repeated cross-validation estimates instead of one split is what made the comparison between the two ensembles defensible, and it is what exposed the SMOTE result.

**Key risk signals.** Low pre-loan account balances are the dominant warning sign. `min_balance` and `balance_at_loan` are the top two features in both the correlation ranking (-0.26 and -0.20) and the Random Forest importance list (0.261 and 0.116); average balance follows at -0.16 in the correlation ranking and transaction frequency follows third in the importance list at 0.071, both mild by comparison. Large loan amounts relative to the installment level add further risk. Age and gender do not separate defaulters from payers in this data. Customer segmentation agrees from the customer side: the quieter low-balance segment (421 borrowers) defaults at 12.4 percent versus 9.2 percent for the active segment, so review effort should skew toward thin-balance accounts.

**Recommendations for the bank.**

1. Add a balance check to loan review: accounts arriving with persistently low balances deserve closer scrutiny. As an illustrative starting point, the defaulter median balance at loan time is 22.0k against 39.5k for repaid loans. A single cut at "balance at loan time below 20k" would have flagged 97 of 682 applications (14.2 percent) and caught 34 of the 76 defaulters (44.7 percent), a precision of 35.1 percent against an 11.1 percent base rate. That is a screening rule, not a decision rule, and the threshold needs validation on recent data before use.
2. Weight loan amount against demonstrated balance capacity rather than income statements alone. The two signals reinforce each other, and the pairing is what matters: splitting the portfolio at the median loan amount and the median pre-loan balance gives a default rate of 4.9 percent for large-balance, small-amount loans, 6.7 percent for large-balance large-amount, 10.1 percent for small-balance small-amount, and 23.3 percent for small-balance large-amount. Balance alone is the weaker filter; balance combined with amount is the strongest pattern in the data.
3. Do not use age or gender in the decision: they show no predictive signal here and would add bias without accuracy.
4. Do not reach for resampling by default. SMOTE would have been adopted on the evidence of a single split and would have made the production model worse. Balance the classes only for models that cannot learn from an 11 percent positive rate on their own.
5. Retrain and revalidate on recent portfolio data before deployment, since these records end in 1998 and only 76 defaults support the estimates. The margin between the top models is smaller than the margin of error, so treat the choice between Gradient Boosting and Random Forest as open and re-decide it on newer data.

**Reproducibility.** All results regenerate by running the notebooks in order (01 to 05) with `requirements.txt` installed, for example: `py -m nbconvert --to notebook --execute notebooks/01_preprocessing.ipynb --output 01_preprocessing.ipynb`.
