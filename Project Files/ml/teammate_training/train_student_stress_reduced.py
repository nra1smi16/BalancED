"""Train a Random Forest Regressor on the reduced student-stress dataset."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

DATA_PATH = Path(__file__).with_name('students_stress_dataset_reduced_15.csv')
TARGET = 'Perceived_Stress_Index_0_100'
DROP_FROM_INPUT = ['Resp_ID', 'E2_Overall_Stress']

df = pd.read_csv(DATA_PATH)
print('Dataset shape:', df.shape)
print('Missing values:', df.isna().sum().sum())
print('Duplicate rows:', df.duplicated().sum())
print('Columns:', df.columns.tolist())
print('Target distribution:\n', df[TARGET].describe())

X = df.drop(columns=[TARGET] + DROP_FROM_INPUT)
y = df[TARGET]
print('Input feature count:', X.shape[1])
print('Features:', X.columns.tolist())

numeric_cols = X.select_dtypes(include=np.number).columns.tolist()
categorical_cols = X.select_dtypes(exclude=np.number).columns.tolist()
preprocessor = ColumnTransformer(transformers=[
    ('num', Pipeline([('imputer', SimpleImputer(strategy='median'))]), numeric_cols),
    ('cat', Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ]), categorical_cols)
])
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', RandomForestRegressor(n_estimators=200, random_state=42))
])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)
print(f'MAE: {mae:.3f}\nMSE: {mse:.3f}\nRMSE: {rmse:.3f}\nR2: {r2:.3f}')

output_dir = DATA_PATH.parent
joblib.dump(pipeline, output_dir / 'student_stress_random_forest.joblib')
plt.figure(figsize=(6, 5))
plt.scatter(y_test, y_pred, alpha=0.55)
plt.plot([0, 100], [0, 100], linestyle='--', color='gray')
plt.xlabel('Actual stress index')
plt.ylabel('Predicted stress index')
plt.title('Actual vs Predicted Stress Index')
plt.tight_layout()
plt.savefig(output_dir / 'stress_prediction_plot.png', dpi=160)
plt.close()
print('Saved model and chart.')
