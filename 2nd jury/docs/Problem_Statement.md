# Problem Statement

## Loan Default Risk Prediction from Pre-Loan Transaction Behavior

**Problem Statement:**
Banks lose money when loans default, and the information that predicts default is usually already sitting in the customer's transaction history before the loan is granted. This project builds a classification system that predicts whether a loan application will be repaid or will default, using only transactions recorded before the loan date, drawn from the PKDD'99 Financial Dataset of a Czech bank (682 loans, roughly one million account transactions, 606 repaid against 76 defaulted, an 11.1 percent default rate). Thirteen behavioral features are engineered per loan by aggregating each account's pre-loan history (transaction counts, deposit and withdrawal totals, mean/minimum/maximum balance, balance at loan time, months active, transactions per month) and joining them with loan terms and demographics. Six classifiers (Decision Tree, Naïve Bayes, Random Forest, Support Vector Machine, K-Nearest Neighbors, Gradient Boosting) are each trained on both the raw imbalanced data and a SMOTE-balanced copy, tuned with a randomized hyperparameter search, and compared under repeated stratified cross-validation on F1-score, Average Precision, and ROC-AUC, with confusion matrices, ROC curves, precision-recall curves, and feature importance used to interpret the winner and identify the behavioral patterns that signal repayment risk.

**Concepts Covered**
- Data Preprocessing
- Feature Engineering
- Exploratory Data Analysis (EDA)
- Data Visualization
- Classification and Prediction
- Decision Tree
- Naïve Bayes
- Random Forest
- Support Vector Machine (SVM)
- K-Nearest Neighbors (KNN)
- Gradient Boosting
- Class Imbalance Handling (SMOTE)
- Model Evaluation and Selection
- Confusion Matrix
- Precision, Recall, F1-Score
- ROC Curve and ROC-AUC
- Precision-Recall Curve and Average Precision
- Cross Validation (repeated stratified k-fold)
- Hyperparameter Tuning (randomized search)
- Feature Importance
- Clustering (KMeans) for customer segmentation

---

## Deliverable Coverage

Each item below is the "Common Deliverables" list from the jury guidelines, mapped to where it is implemented and reported.

| # | Deliverable | Where it lives |
|---|---|---|
| 1 | Problem definition and objectives | `Problem_Statement.md` (above); `Jury2_Report.md` section 1 |
| 2 | Dataset description and source | `Jury2_Report.md` section 2 (PKDD'99, five tables, row counts, target encoding) |
| 3 | Data preprocessing pipeline | `notebooks/01_preprocessing.ipynb`, `notebooks/02_features.ipynb`; `Jury2_Report.md` section 3 |
| 4 | Exploratory Data Analysis and visualizations | `notebooks/03_eda.ipynb`; `Jury2_Report.md` section 4; `outputs/figures/` |
| 5 | Implementation of the selected algorithm(s) | `notebooks/04_modeling.ipynb` (six classifiers, two imbalance arms, tuning); `Jury2_Report.md` section 5 |
| 6 | Performance comparison using evaluation metrics | `outputs/metrics_comparison.csv`, `tuning_results.csv`, `cv_comparison.csv`, `confusion_matrices.png`, `roc_curves.png`, `pr_curves.png`, `cv_selection.png`; `Jury2_Report.md` section 6 |
| 7 | Conclusions and recommendations | `Jury2_Report.md` section 7; `SYNOPSIS.md` |
| 8 | Project report and presentation | `Jury2_Report.md` (this repository) and the executed notebooks |
| 9 | Association rule mining (Apriori, FP-Growth) | `tools/pattern_mining.py`; `outputs/pattern_itemsets.csv`, `pattern_rules.csv`; `Jury2_Report.md` section 6.1; app page 4 |

## Headline Result

Tuned Gradient Boosting on the unresampled data is the selected model, at repeated cross-validated F1 0.571 ± 0.120, Average Precision 0.654, and ROC-AUC 0.864. Tuned Random Forest ties it on F1 within the fold-to-fold spread and leads on Average Precision (0.661) and ROC-AUC (0.877), so the two form one leading group and the report says so rather than declaring a false winner. The lowest pre-loan balance and the balance at loan time are the strongest default signals in both the correlation ranking and the Random Forest importance list.

## Scope Note

The jury guidelines place Association Rule Mining (Apriori, FP-Growth) in Unit III. The core of this project is the Unit IV classification and prediction work, with the Unit III data preprocessing, feature engineering, EDA, and visualization outcomes covered in full. A supplementary pattern-mining step is included in `tools/pattern_mining.py` and reported in section 6.1; it is not used to select or tune the classifier.
