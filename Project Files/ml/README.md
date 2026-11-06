# BalancED: model and data

This folder holds everything about the stress-prediction model: the data, the team's training code, the trained
model, and the scripts the website uses. The website itself is in the `core/` folder.

## What is here

| Path | What it is |
|---|---|
| `data/students_stress_dataset_reduced_15.csv` | Reduced dataset (15 columns plus the target). The model is trained on this file. |
| `data/students_stress_dataset_age_balanced.csv` | The larger, original version of the dataset (all survey questions). |
| `teammate_training/Student_Stress_ML_Reduced_15.ipynb` | The team's training notebook (Random Forest). |
| `teammate_training/train_student_stress_reduced.py` | The same training code as a script. |
| `teammate_training/student_stress_random_forest.joblib` | The trained model exactly as the team produced it (14 inputs, scikit-learn 1.8.0). |
| `train_model.py` | Trains the model the website uses (12 inputs). Writes `student_stress_model.joblib`. |
| `Stress_Model_Training_and_Evaluation.ipynb` | The same training and evaluation as a notebook, with the results saved in it. Runs in Google Colab. |
| `models/student_stress_model_website_12_inputs_sklearn-1.8.0.joblib` | A reference copy of the website's model (12 inputs), saved with scikit-learn 1.8.0. The website does not load this file. |
| `evaluate_model.py` | Re-runs the evaluation and writes `evaluation_report.txt`. |
| `evaluation_report.txt` | Results of the evaluation (see below). |

## The model

- **Target:** `Perceived_Stress_Index_0_100`, a 0-100 stress index. In this dataset the index is calculated from the
  survey answers, so the model learns that calculation. It is an estimate, not a clinical measurement.
- **Method:** Random Forest regression, 200 trees, `random_state=42` (Breiman, 2001), built with scikit-learn
  (Pedregosa et al., 2011). Missing numbers are filled with the median, missing categories with the most common value,
  and text categories are one-hot encoded.
- **Inputs used by the website (12):** Age, Gender, Field_of_Study, Avg_Daily_Study_Hours, and the questions
  B1, B2, B3, C1, C2, C4, C5, D1 (each answered 1-5).
- **Left out on purpose:** `E2_Overall_Stress` (the student's own stress rating, left out as a leakage precaution),
  and `Academic_Level` and `Institution_Type` (the website does not ask for them, and they did not improve accuracy).
  The team's original model (`teammate_training/`) also uses Academic_Level and Institution_Type (14 inputs).
- **Levels:** the score is turned into Normal (< 25), Mild (< 50), Moderate (< 75) and High Risk (>= 75). These cutoffs
  were chosen by the project team. The dataset has no official level labels.

## Results (`evaluation_report.txt`)

Evaluated for the website's 12 inputs. Created with scikit-learn 1.8.0. Re-run `evaluate_model.py` to reproduce it.

| Method | Test average error | Test R2 | Test level accuracy |
|---|---|---|---|
| 80/20 hold-out (800 / 200 rows) | 4.04 | 0.971 | 86.0% |
| 2/3 training, 1/3 test (666 / 334 rows) | 3.96 | 0.972 | 87.4% |
| 5-fold cross-validation | 4.42 +/- 0.24 | 0.967 +/- 0.003 | 86.6% +/- 1.1% |

Precision, recall and F1 for each level are in the report. Training accuracy is higher than test accuracy
(94.9% against 86.0% on the 80/20 split), which is normal for a Random Forest.

## Running it

```
pip install scikit-learn pandas joblib
python ml/train_model.py        # creates ml/student_stress_model.joblib for the website
python ml/evaluate_model.py     # creates ml/evaluation_report.txt
```

The notebook can be opened in Google Colab: upload it with `students_stress_dataset_reduced_15.csv` and choose Run all.
If it is run from inside this `ml/` folder, it finds the data in `data/` by itself.

Run `train_model.py` once on every machine that runs the website (your laptop, PythonAnywhere).
`teammate_training/student_stress_random_forest.joblib` was saved with scikit-learn 1.8.0, which needs
Python 3.11 or newer. The PythonAnywhere account used here runs Python 3.10, so that file cannot be loaded there.
That is why the website builds its own model file on each machine, and why `student_stress_model.joblib` is listed in
`.gitignore`.

To run the team's script, put `students_stress_dataset_reduced_15.csv` in the same folder as the script.

## References

- Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5-32.
- Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825-2830.

Dataset source: to be added by the team.
