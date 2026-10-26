"""
Turns a saved questionnaire into a stress score using the trained scikit-learn pipeline.

The model file is NOT in GitHub (it must be trained with the scikit-learn version installed on the
machine that uses it). Create it once per machine with:
    python core/ml/train_model.py
"""
from pathlib import Path

from .survey import LIKERT_FIELDS

MODEL_PATH = Path(__file__).resolve().parent / 'ml' / 'student_stress_model.joblib'
_model = None


def _load_model():
    global _model
    if _model is None:
        import joblib
        _model = joblib.load(MODEL_PATH)
    return _model


def _dataset_name(field):
    """'b1_pressure_high_grades' -> 'B1_Pressure_High_Grades' (the dataset's column name)."""
    return '_'.join(part.capitalize() for part in field.split('_'))


def build_row(profile, assessment):
    """The values the model is given, named exactly like the training columns."""
    row = {
        'Age': profile.age,
        'Gender': profile.gender,
        'Field_of_Study': profile.major,
        'Avg_Daily_Study_Hours': profile.avg_daily_study_hours,
    }
    for field in LIKERT_FIELDS:
        row[_dataset_name(field)] = getattr(assessment, field)
    return row


def predict_stress(profile, assessment):
    """Predicted stress index, 0-100 (rounded to 1 decimal)."""
    import pandas as pd

    model = _load_model()
    row = build_row(profile, assessment)
    expected = list(model.feature_names_in_)
    missing = [column for column in expected if column not in row]
    if missing:
        raise ValueError(f'The model needs columns the website does not collect: {missing}')

    score = float(model.predict(pd.DataFrame([row])[expected])[0])
    return round(min(100.0, max(0.0, score)), 1)


def level_for_score(score):
    if score < 25:
        return 'Normal'
    if score < 50:
        return 'Mild'
    if score < 75:
        return 'Moderate'
    return 'High Risk'
