# System Requirements and Reproduction Guide

## Hardware
Any 64-bit laptop or lab machine with at least 4 GB RAM and 1 GB free disk space. The full transaction table (about one million rows) processes in memory in under a minute. Modeling runs multi-threaded, so more cores shorten the tuning step. No GPU is needed. A complete end-to-end run of all five notebooks takes under two minutes on a 2023-class laptop, with roughly 80 of those seconds in notebook 04 (hyperparameter search and repeated cross-validation).

## Software (pinned in `requirements.txt`)
- Python 3.13.5
- pandas 2.2.3, numpy 2.2.4
- scikit-learn 1.7.0
- matplotlib 3.10.3, seaborn 0.13.2
- imbalanced-learn 0.14.2 (SMOTE comparison arm)
- Jupyter 1.1.1 + nbconvert 7.17.1 (notebook execution and verification)

Install everything with `pip install -r requirements.txt` from the `2nd jury/` folder. The pins are exact on purpose: the saved model pickle and every reported number were produced with this set, and scikit-learn refuses to load a pickle written by a different minor version.

## Data Required
Place these PKDD'99 files in `2nd jury/data/` (already present): `loan.csv`, `trans.csv`, `client.csv`, `account.csv`, `disp.csv`. All files use `;` as the separator.

## Reproduce (in order)
Run from the `2nd jury/` folder:

```bash
py -m nbconvert --to notebook --execute notebooks/01_preprocessing.ipynb --output 01_preprocessing.ipynb
py -m nbconvert --to notebook --execute notebooks/02_features.ipynb --output 02_features.ipynb
py -m nbconvert --to notebook --execute notebooks/03_eda.ipynb --output 03_eda.ipynb
py -m nbconvert --to notebook --execute notebooks/04_modeling.ipynb --output 04_modeling.ipynb
py -m nbconvert --to notebook --execute notebooks/05_segmentation.ipynb --output 05_segmentation.ipynb
```

Expected artifacts: `data/loan_features.csv` (682 rows, 27 columns), `outputs/metrics_comparison.csv` (12 model runs, single split), `outputs/tuning_results.csv` (12 randomized hyperparameter searches), `outputs/cv_comparison.csv` (24 rows, repeated stratified 5-fold x 10), `outputs/segment_profiles.csv` (2 KMeans segments), `outputs/models/best_GradientBoosting_baseline_tuned.pkl`, and 14 PNGs in `outputs/figures/`. Each notebook ends with assert cells; a clean run with no errors is the pass condition.
