"""
Train the stress model on the reduced student-stress dataset and save it next to this file.

Based on the team's script (train_student_stress_reduced.py): same Random Forest, same preprocessing,
same train/test split. Only the input columns changed so they match what the website collects:
  - E2_Overall_Stress is not used (leakage precaution, same as the team's script)
  - Academic_Level and Institution_Type are not used (the website does not ask for them,
    and in testing they did not improve accuracy)

Run it once on every machine that runs the website (laptop, PythonAnywhere):
    python core/ml/train_model.py
The model has to be trained with the scikit-learn version installed on THAT machine,
which is why the .joblib file is not shared through GitHub.
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / 'students_stress_dataset_reduced_15.csv'
MODEL_PATH = HERE / 'student_stress_model.joblib'
TARGET = 'Perceived_Stress_Index_0_100'
DROP_FROM_INPUT = ['Resp_ID', 'E2_Overall_Stress', 'Academic_Level', 'Institution_Type']

df = pd.read_csv(DATA_PATH)
X = df.drop(columns=[TARGET] + DROP_FROM_INPUT)
y = df[TARGET]
print('Input features:', X.columns.tolist())

numeric_cols = X.select_dtypes(include=np.number).columns.tolist()
categorical_cols = X.select_dtypes(exclude=np.number).columns.tolist()
preprocessor = ColumnTransformer(transformers=[
    ('num', Pipeline([('imputer', SimpleImputer(strategy='median'))]), numeric_cols),
    ('cat', Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore')),
    ]), categorical_cols),
])
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', RandomForestRegressor(n_estimators=200, random_state=42)),
])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)
print(f'MAE:  {mean_absolute_error(y_test, y_pred):.3f}')
print(f'RMSE: {np.sqrt(mean_squared_error(y_test, y_pred)):.3f}')
print(f'R2:   {r2_score(y_test, y_pred):.3f}')

joblib.dump(pipeline, MODEL_PATH)
print(f'Saved {MODEL_PATH.name} (scikit-learn {sklearn.__version__})')
