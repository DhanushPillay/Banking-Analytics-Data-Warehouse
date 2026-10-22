# Jury 2 Presentation

## 1. Project Title
Customer Behavioral Analysis and Loan Default Classification

## 2. Problem Statement
Banks lose money when loan applicants default. The project predicts whether a loan will be repaid or default by analyzing pre-loan transaction behavior.

## 3. Dataset
- Source: PKDD'99 Financial Dataset
- Tables used: loan, trans, client, account, disp
- Total loans: 682
- Good loans: 606
- Default loans: 76
- Default rate: 11.14%

## 4. Architecture Diagram
- Raw CSV files
- Preprocessing and cleaning
- Feature engineering from pre-loan history
- EDA and behavior profiling
- Classification modeling
- Validation and comparison
- Final recommendation

## 5. Input / Output
Input:
- Transaction history before loan grant date
- Loan amount, duration, payment details
- Customer demographics and account metadata

Output:
- Default risk label: good / default
- Model probabilities and rankings
- Evaluation metrics and visual outputs

## 6. Class Labels
- Good loan: repaid / no problems
- Default loan: unpaid / in debt

## 7. Pattern Matching and Association Mining
To satisfy the judging matrix, the project also reviews transaction behavior as recurring behavioral patterns.

- Pattern mining is used to detect repeated co-occurrence in transaction behavior
- Apriori identifies frequent itemsets and association rules
- FP-Growth is used as a faster alternative for dense transaction data
- These patterns support the interpretation of risky customer behavior, even though the final prediction task remains classification
- Implemented in `tools/pattern_mining.py`; outputs are `outputs/pattern_itemsets.csv` and `outputs/pattern_rules.csv`

## 8. Classification Algorithms
- Decision Tree
- Naive Bayes
- Random Forest
- SVM
- K-Nearest Neighbors
- Gradient Boosting

## 9. Validation Strategy
- Stratified train/test split
- Hyperparameter tuning
- Repeated stratified cross-validation
- Comparison across baseline and SMOTE settings

## 10. Performance Metrics
- Accuracy
- Precision
- Recall
- F1-score
- ROC-AUC
- Average Precision
- Confusion Matrix

## 11. Key Result
The selected model is tuned Gradient Boosting on the unresampled data, with strong repeated cross-validation performance.

## 12. Conclusion
Low pre-loan balances and low balance-at-loan values are the main signals of default. The model recommends a stronger review focus on low-balance, high-amount applicants rather than relying on age or gender.
