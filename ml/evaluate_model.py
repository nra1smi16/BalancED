"""
Evaluates the website's model setup and writes ml/evaluation_report.txt.

It reports, for the same 12 inputs the website uses:
  - an 80/20 hold-out split (what the team's notebook does)
  - a 2/3 train, 1/3 test split
  - 5-fold cross-validation
For each split: error and R2 on the training and the test data, plus accuracy, precision, recall and F1.

The model predicts a number (0-100), so precision/recall/F1 are computed after turning scores into the four
levels with the website's cutoffs: Normal < 25, Mild < 50, Moderate < 75, High Risk >= 75.
These cutoffs were chosen by the project team. The dataset has no official level labels.

Run from the project folder:   python ml/evaluate_model.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (accuracy_score, confusion_matrix, make_scorer, mean_absolute_error,
                             mean_squared_error, precision_recall_fscore_support, r2_score)
from sklearn.model_selection import KFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / 'data' / 'students_stress_dataset_reduced_15.csv'
REPORT_PATH = HERE / 'evaluation_report.txt'
TARGET = 'Perceived_Stress_Index_0_100'
DROP_FROM_INPUT = ['Resp_ID', 'E2_Overall_Stress', 'Academic_Level', 'Institution_Type']
LEVELS = ['Normal', 'Mild', 'Moderate', 'High Risk']

df = pd.read_csv(DATA_PATH)
X = df.drop(columns=[TARGET] + DROP_FROM_INPUT)
y = df[TARGET]
lines = []


def out(text=''):
    print(text)
    lines.append(text)


def to_level(scores):
    return pd.cut(np.asarray(scores), [-1, 25, 50, 75, 101], right=False, labels=LEVELS)


def make_pipeline():
    numeric_cols = X.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = X.select_dtypes(exclude=np.number).columns.tolist()
    preprocessor = ColumnTransformer([
        ('num', Pipeline([('imputer', SimpleImputer(strategy='median'))]), numeric_cols),
        ('cat', Pipeline([('imputer', SimpleImputer(strategy='most_frequent')),
                          ('onehot', OneHotEncoder(handle_unknown='ignore'))]), categorical_cols),
    ])
    return Pipeline([('preprocessor', preprocessor),
                     ('model', RandomForestRegressor(n_estimators=200, random_state=42))])


def evaluate_split(title, test_size):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
    model = make_pipeline().fit(X_train, y_train)
    out(f'=== {title}: {len(X_train)} training rows / {len(X_test)} test rows ===')
    for name, features, target in (('Training', X_train, y_train), ('Test', X_test, y_test)):
        predicted = model.predict(features)
        out(f'{name:8s}: MAE {mean_absolute_error(target, predicted):.2f}  '
            f'RMSE {np.sqrt(mean_squared_error(target, predicted)):.2f}  R2 {r2_score(target, predicted):.3f}  '
            f'level accuracy {accuracy_score(to_level(target), to_level(predicted)):.3f}')
    actual, predicted = to_level(y_test), to_level(model.predict(X_test))
    precision, recall, f1, support = precision_recall_fscore_support(actual, predicted, labels=LEVELS, zero_division=0)
    out('Test set, per level:')
    for level, p, r, f, n in zip(LEVELS, precision, recall, f1, support):
        out(f'  {level:10s} precision {p:.2f}  recall {r:.2f}  F1 {f:.2f}  (n={n})')
    for average in ('macro', 'weighted'):
        p, r, f, _ = precision_recall_fscore_support(actual, predicted, labels=LEVELS, average=average, zero_division=0)
        out(f'  {average:8s} average: precision {p:.3f}  recall {r:.3f}  F1 {f:.3f}')
    matrix = pd.DataFrame(confusion_matrix(actual, predicted, labels=LEVELS), index=LEVELS, columns=LEVELS)
    out('Confusion matrix (rows = actual level, columns = predicted level):')
    out(matrix.to_string())
    out()


out(f'Model evaluation (scikit-learn {sklearn.__version__}, pandas {pd.__version__})')
out(f'Data: {len(df)} rows. Inputs ({X.shape[1]}): {", ".join(X.columns)}')
out('Level counts in the data: ' + ', '.join(f'{k} {v}' for k, v in pd.Series(to_level(y)).value_counts().reindex(LEVELS).items()))
out()
evaluate_split('80/20 hold-out split', 0.2)
evaluate_split('2/3 training, 1/3 test split', 1 / 3)

accuracy = make_scorer(lambda actual, predicted: accuracy_score(to_level(actual), to_level(predicted)))
cv = cross_validate(make_pipeline(), X, y, cv=KFold(5, shuffle=True, random_state=42),
                    scoring={'mae': 'neg_mean_absolute_error', 'r2': 'r2', 'accuracy': accuracy})
out('=== 5-fold cross-validation (mean +/- standard deviation over the 5 test folds) ===')
out(f"MAE {-cv['test_mae'].mean():.2f} +/- {cv['test_mae'].std():.2f}   "
    f"R2 {cv['test_r2'].mean():.3f} +/- {cv['test_r2'].std():.3f}   "
    f"level accuracy {cv['test_accuracy'].mean():.3f} +/- {cv['test_accuracy'].std():.3f}")

REPORT_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(f'\nSaved {REPORT_PATH.name}')
