# Jury 2 Requirements & Tasks

Based on the university guidelines for Units III & IV, here is the complete checklist of everything we need to accomplish for Jury 2.

## Core Objective
Perform the complete data mining pipeline: **Data Collection $\rightarrow$ Preprocessing $\rightarrow$ Visualization $\rightarrow$ Model Building $\rightarrow$ Evaluation** using Python and Scikit-learn.

## Task Checklist (Common Deliverables)

### 1. Problem Definition and Objectives
- [x] Define the classification problem: Predict **Loan Default Risk** based on customer transaction behavior.
- [x] Set objectives: Identify risky behaviors to help the bank mitigate loan defaults.

### 2. Dataset Description and Source
- [x] Copy PKDD'99 Financial Dataset to the `data/` folder.
- [x] Document the specific tables used (`loan.csv`, `trans.csv`, `client.csv`, `account.csv`). See `Jury2_Report.md` section 2.

### 3. Data Preprocessing Pipeline (Unit III)
- [x] **Data Cleaning:** No duplicates in any table, all dates parse, ages sanity checked (`01_preprocessing.ipynb`).
- [x] **Feature Engineering:** 13 behavioral features per loan from pre-loan transactions only, saved to `data/loan_features.csv` (`02_features.ipynb`).
- [x] **Transformation:** Gender binary encoded, continuous features standardized with `StandardScaler` inside training-only pipelines (`04_modeling.ipynb`).

### 4. Exploratory Data Analysis (EDA) and Visualizations (Unit III)
- [x] Visualize the distribution of the target variable (606 good vs 76 default, 11.14 percent).
- [x] Create a correlation matrix heatmap (top signals: `min_balance` -0.26, `balance_at_loan` -0.20) plus full feature-feature matrix (`corr_full.png`: volume features collinear, e.g. `sum_deposit`/`sum_withdrawal` 0.997).
- [x] Data-quality tables (no missing/duplicates in `loan_features.csv`, skew + overdrafts noted) and categorical splits (gender/status vs default).
- [x] Plot visualizations (boxplots, stacked histogram) comparing defaulted vs non-defaulted behaviors. Figures in `outputs/figures/` (14 PNGs).
- [x] Additional (title scope): customer segmentation with KMeans on behavioral features (k=2 by silhouette 0.29 + inertia), with default rate per segment (`05_segmentation.ipynb`, `outputs/segment_profiles.csv`).
- [x] Additional: risk quadrant crossing pre-loan balance against loan amount (`risk_quadrant.png`).

### 5. Implementation of Classification Algorithms (Unit IV)
Implemented in `04_modeling.ipynb` using `scikit-learn`:
- [x] **Decision Tree**
- [x] **Naïve Bayes**
- [x] **Random Forest** (feature importance from the tuned baseline estimator)
- [x] **SVM** (`CalibratedClassifierCV`, since `SVC(probability=True)` is deprecated)
- [x] **KNN** (k=5 distance baseline)
- [x] **Gradient Boosting** (boosted-tree alternative; selected model at repeated-CV F1 0.571)

### 6. Performance Comparison using Evaluation Metrics (Unit IV)
Default hyperparameters on the held-out 171-row test set (`outputs/metrics_comparison.csv`, 12 runs), then hyperparameter search (`outputs/tuning_results.csv`, 12 `RandomizedSearchCV` runs) and repeated cross-validation (`outputs/cv_comparison.csv`, 5-fold x 10 = 50 estimates per configuration). The selected pipeline is `outputs/models/best_GradientBoosting_baseline_tuned.pkl`.
- [x] Accuracy
- [x] Precision
- [x] Recall
- [x] F1-score
- [x] Confusion Matrix (2x6 grid figure)
- [x] ROC-AUC curve (side-by-side baseline/SMOTE figure)
- [x] Average Precision / precision-recall curve (`pr_curves.png`), the honest metric at 11% prevalence
- [x] Cross Validation: 5-fold inner search plus `RepeatedStratifiedKFold(5, 10)` as the selection table (`cv_selection.png`)
- [x] Hyperparameter Tuning: `RandomizedSearchCV` per model and setting, fitted on the training split only, with sensitivity curves (`tuning_curves.png`)
- [x] Model evaluation and selection: winner chosen on repeated-CV F1, with the tie to Random Forest and the small-n limitation stated in the report

### 7. Conclusions and Recommendations
- [x] Determine the best-performing classification model (tuned Gradient Boosting, baseline arm: repeated-CV F1 0.571 ± 0.120, AP 0.654, AUC 0.864, tied with tuned Random Forest on F1).
- [x] Write down business recommendations based on feature importance (balance checks, amount-vs-balance weighting, no age/gender use, do not resample by default). See `Jury2_Report.md` section 7.

### 8. Project Report and Presentation
- [x] Complete the `Jury2_Report.md` document with the findings from all steps above.
- [ ] Create a presentation (or prepare to present the Jupyter Notebooks/Report).

---

## Suggested Technology Stack
- **Language:** Python
- **Libraries:** `pandas` (preprocessing), `numpy` (math), `scikit-learn` (modeling/evaluation), `matplotlib` & `seaborn` (visualization), `imbalanced-learn` (SMOTE comparison).
- **Environment:** Jupyter Notebooks (`.ipynb`) for interactive execution and visualization.
