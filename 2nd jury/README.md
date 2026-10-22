# Customer Behavioral Analysis & Loan Default Classification

## Overview
This repository folder contains the code, data, and documentation for the Jury 2 project, fulfilling the requirements for Units III & IV (Data Mining, Preprocessing, and Classification).

The project applies machine learning algorithms to the PKDD'99 Financial Dataset to classify and predict **Loan Default Risk** based on customer transaction behavior.

## Pipeline

```mermaid
flowchart LR
    RAW["raw CSVs<br/>loan, trans, client,<br/>account, disp"] --> N01["01_preprocessing<br/>clean + target<br/>606 good / 76 default"]
    N01 --> N02["02_features<br/>13 pre-loan features<br/>loan_features.csv"]
    N02 --> N03["03_eda<br/>target, corr,<br/>boxplots, age"]
    N02 --> N04["04_modeling<br/>6 models x baseline/SMOTE<br/>+ tuning + repeated CV"]
    N02 --> N05["05_segmentation<br/>KMeans k=2<br/>12.4% vs 9.2%"]
    N03 --> FIG["figures/<br/>14 PNGs"]
    N04 --> FIG
    N04 --> MET["metrics_comparison.csv<br/>tuning_results.csv<br/>cv_comparison.csv<br/>best GB pipe"]
    N05 --> SEG["segment_profiles.csv"]
    MET --> REP["Jury2_Report.md"]
    FIG --> REP
    SEG --> REP
```

## Directory Structure
- `/data/`: Raw PKDD'99 CSV files (`trans.csv`, `loan.csv`, `client.csv`, etc.) plus the engineered `loan_features.csv` (682 loans, 27 columns).
- `/docs/`: `Problem_Statement.md` (the jury problem statement), `Jury2_Report.md` (final report), `jury2_requirements.md` (task checklist), `SYNOPSIS.md`, `SYSTEM_REQUIREMENTS.md` (reproduction guide), `REFERENCES.md`.
- `/notebooks/`: Executed Jupyter notebooks, run in order:
  1. `01_preprocessing.ipynb` (cleaning, target definition: 606 good vs 76 default)
  2. `02_features.ipynb` (pre-loan behavioral features, leakage-checked)
  3. `03_eda.ipynb` (target balance, correlations, behavior comparisons, risk quadrant)
  4. `04_modeling.ipynb` (Decision Tree, Naive Bayes, Random Forest, SVM, KNN, Gradient Boosting; baseline vs SMOTE, randomized hyperparameter search, repeated 5-fold x 10 cross-validation, model selection, persisted best pipe)
  5. `05_segmentation.ipynb` (KMeans behavior segments: quieter low-balance vs active; default rate per segment)
- `/outputs/`: `metrics_comparison.csv` (12 runs, single split), `tuning_results.csv` (12 hyperparameter searches), `cv_comparison.csv` (24 rows, 50 estimates each, the selection table), `segment_profiles.csv`, `models/best_GradientBoosting_baseline_tuned.pkl`, and `figures/` (14 PNGs: target distribution, target correlations, full feature correlations, boxplots, age histogram, risk quadrant, confusion matrices, ROC curves, precision-recall curves, CV selection, tuning curves, RF importance, segment default rates, segment scatter).

## Project Objectives
1. Perform complete data preprocessing and feature engineering.
2. Conduct Exploratory Data Analysis (EDA) on customer transaction behaviors.
3. Train classification models (Decision Tree, Naïve Bayes, Random Forest, SVM, KNN, Gradient Boosting).
4. Tune hyperparameters and select the final model by repeated cross-validation.
5. Evaluate model performance using Accuracy, Precision, Recall, F1-Score, Average Precision, and ROC-AUC.

## Headline Result
Tuned Gradient Boosting on unresampled data is the selected model: repeated cross-validated F1 0.571 ± 0.120, Average Precision 0.654, ROC-AUC 0.864. Tuned Random Forest ties it on F1 and leads on Average Precision (0.661) and ROC-AUC (0.877), so the two are one leading group. Two findings from the testing: SMOTE lowered F1 for five of the six models, and hyperparameter search mattered mainly for SVM and Decision Tree. Low pre-loan balances (`min_balance`, `balance_at_loan`) are the strongest default signals, and crossing pre-loan balance with loan amount separates the portfolio from 4.9% to 23.3% default. Behavior segmentation finds two groups: a quieter low-balance segment defaulting at 12.4 percent versus 9.2 percent for the active segment. Details in `docs/Jury2_Report.md`.

## How to Run
Install dependencies with `pip install -r requirements.txt`, then execute the notebooks in order (01 to 05). Each notebook is self-contained and runs top to bottom, for example:

```bash
py -m nbconvert --to notebook --execute notebooks/01_preprocessing.ipynb --output 01_preprocessing.ipynb
```
