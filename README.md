# BalancED: Student Stress Tracking & Support Platform

BalancED is a Django-based web application designed to help university students monitor their stress levels using Machine Learning (Random Forest regression) and receive tailored daily advice and optional AI-generated guidance.

> **Disclaimer:** The predicted stress score and level are dataset-defined estimates for self-reflection and are **not** clinical diagnoses or medical advice.

## Table of Contents

* [Features & System Overview](#features--system-overview)
* [Architecture & Data Flow](#architecture--data-flow)
* [Machine Learning Model](#machine-learning-model)
* [AI Note Generation (Groq Integration)](#ai-note-generation-groq-integration)
* [Project Directory Structure](#project-directory-structure)
* [Database Schema](#database-schema)
* [Installation & Setup](#installation--setup)
* [Limitations & Technical Considerations](#limitations--technical-considerations)

## Features & System Overview

### 1. Accounts & Privacy-First Security

* **Registration:** Students sign up with a name, username, and password. Usernames are case-insensitive (`Noura` and `noura` map to the same account).
* **Password Enforcement:** Leverages Django's native validators (minimum length, similarity check, common password check, non-numeric check).
* **Security:** Passwords are never stored in plain text. Django hashes them using **PBKDF2 with SHA256** (storing algorithm, iterations, salt, and hash).
* **Privacy Trade-off:** No email addresses are collected. This protects student identity, eliminates data leak risks involving personal emails, and speeds up account registration, though users cannot receive off-platform email alerts or automated password recovery links if login details are lost.

### 2. Student Profile

* **Required Fields:** Name, Date of Birth, Major (8 choices based on the dataset), Year of Enrollment, Gender, Courses Taken this Semester, Average Daily Study Hours (`<2`, `2-4`, `4-6`, `>6`).
* **Optional Fields:** Height, Weight, Chronic Illnesses (free-text), Weekly Reminder Toggle, and AI Opt-in setting.
* **Calculated Fields:** Age and Years Enrolled are automatically computed (Age serves as a core model input).
* **Profile Completion Guard:** Incomplete profiles redirect students to the profile page with targeted missing-field alerts.

### 3. Assessment & Questionnaire

* 9 statements rated on a 1–5 scale (default starting value of 3):
  * 8 core items covering grade pressure, workload, work-life balance, anxiety, concentration, exhaustion, future concern, and physical pain/headaches.
  * 1 item ($E_2$: self-rated overall stress) collected for tracking but excluded from model training to prevent data leakage.
* Flexible frequency: Weekly check-ins are recommended via an in-app banner (when the last check-in is $\ge 7$ days old), but users can complete check-ins at any time.

### 4. Interactive Dashboard & History

* **Stress Score Gauge:** Visual representation of the latest score, qualitative risk level, and date.
* **Exam Calendar:** Interactive calendar letting students mark exam dates.
* **SVG Stress Trend Line Chart:** A custom SVG rendering of historical check-ins with color-coded risk bands, interactive tooltips, and non-overlapping external legend.
* **Check-in Management:** Full history view with itemized records and hard deletion options.
* **Counseling Card:** Quick contact access for the UAEU Counseling and Wellbeing Service (dynamically highlighted during Moderate and High Risk states).

## Architecture & Data Flow

```
[ Student Questionnaire Input ]
               │
               ▼
   [ Profile Data (Age, Gender, Major, Study Hours) ]
               │
               ▼
    [ predictor.py (Preprocessing & One-Hot Encoding) ]
               │
               ▼
 [ Random Forest Regressor (student_stress_model.joblib) ]
               │
               ├─────────────────────────┐
               ▼                         ▼
   [ Numerical Score: 0-100 ]   [ Categorical Level ]
               │                         │
               └────────────┬────────────┘
                            ▼
           [ Save Assessment Record to SQLite ]
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
 [ Hand-Written Note Engine ]      [ Optional AI Note Engine ]
   (Always executed locally)        (Groq: gpt-oss-20b via JSON)
            │                               │
            └───────────────┬───────────────┘
                            ▼
                  [ Render Dashboard UI ]
```

## Machine Learning Model

* **Target Variable:** `Perceived_Stress_Index_0_100` (Continuous scale $0 - 100$).
* **Algorithm:** Random Forest Regression ($200$ trees, `random_state=42`) using `scikit-learn`.
* **Inputs (12):** `Age`, `Gender`, `Field_of_Study`, `Avg_Daily_Study_Hours`, and 8 questionnaire indicators ($B_1, B_2, B_3, C_1, C_2, C_4, C_5, D_1$).
* **Excluded Features:** $E_2$ (leakage precaution), `Academic_Level`, and `Institution_Type` (did not improve accuracy and omitted from website collection).
* **Preprocessing:** Median imputation for missing numeric values, mode imputation for categorical values, and one-hot encoding for string categories.
* **Risk Level Cutoffs:**
  * **Normal:** $< 25$
  * **Mild:** $25 - 49.9$
  * **Moderate:** $50 - 74.9$
  * **High Risk:** $\ge 75$

### Model Performance Metrics (`evaluation_report.txt`)

| Evaluation Split | Mean Absolute Error (MAE) | $R^2$ Score | Level Classification Accuracy |
| --- | --- | --- | --- |
| **80 / 20 Hold-out** (800 / 200 rows) | 4.04 | 0.971 | 86.0% |
| **2/3 Train, 1/3 Test** (666 / 334 rows) | 3.96 | 0.972 | 88.0% |
| **5-Fold Cross-Validation** | 4.41 $\pm$ 0.25 | 0.967 $\pm$ 0.003 | 86.8% $\pm$ 0.9% |

## AI Note Generation (Groq Integration)

When a student opts in via their profile or at questionnaire submission, an extra AI-generated insight card appears on their dashboard:

* **Provider & Model:** Groq API running `openai/gpt-oss-20b`.
* **Data Transmitted:** Anonymized text summary (age, gender, major, study hours, 8 scaled ratings, stress level, and chronic illness presence flag). **Never sent:** Name, username, password, height, weight, or specific medical conditions.
* **Constraints & Safety:**
  * Structured JSON response format.
  * Strict length limits: Opening ($\le 10$ words), Routine Activity ($\le 18$ words), Support Sentence (High Risk only).
  * Explicit prohibitions against medical diagnoses, clinical advice, displaying numeric scores, or including links/phone numbers.
* **Fallback Behavior:** If the API request times out or fails validation, the system cleanly fails back to the primary hand-written note engine without crashing the request.

## Project Directory Structure

```
BalancED/
├── core/                               # Main Django Web Application
│   ├── templates/core/                 # HTML UI Templates (Dashboard, History, etc.)
│   ├── static/                         # CSS, JavaScript, and SVG Assets
│   ├── models.py                       # User Profile & Assessment DB Schema
│   ├── views.py                        # Application Routing & Request Logic
│   ├── predictor.py                    # Real-time ML Model Execution
│   ├── notes.py                        # Rule-Based Hand-written Note Generator
│   ├── ai_notes.py                     # Groq LLM Integration & Payload Handler
│   └── charts.py                       # Dynamic SVG Trend Line Chart Builder
├── ml/                                 # Machine Learning Workspace
│   ├── data/                           # CSV Training Datasets
│   │   ├── students_stress_dataset_reduced_15.csv
│   │   └── students_stress_dataset_age_balanced.csv
│   ├── models/                         # Serialized Model Artifacts (.joblib)
│   ├── teammate_training/              # Original Exploratory Jupyter Notebooks
│   ├── train_model.py                  # Model Build Script for Local/Server Runtimes
│   ├── evaluate_model.py               # Evaluation Script generating report text
│   └── evaluation_report.txt           # Model Performance Benchmark Log
├── manage.py                           # Django CLI Tool
└── requirements.txt                    # Python Dependencies
```

## Database Schema

The SQLite database (`db.sqlite3`) uses the following core relational models:

```
┌───────────────────────────┐         ┌───────────────────────────┐
│        User (Auth)        │ 1     1 │      StudentProfile       │
├───────────────────────────┤─────────├───────────────────────────┤
│ id (PK)                   │         │ id (PK)                   │
│ username                  │         │ user_id (FK)              │
│ password (PBKDF2 SHA256)  │         │ full_name                 │
└───────────────────────────┘         │ date_of_birth             │
                                      │ gender, major, study_hrs  │
                                      │ ai_opt_in (Boolean)       │
                                      └───────────────────────────┘
                                                    │ 1
                                                    │
                                                    │ *
                                      ┌───────────────────────────┐
                                      │        Assessment         │
                                      ├───────────────────────────┤
                                      │ id (PK)                   │
                                      │ profile_id (FK)           │
                                      │ created_at                │
                                      │ b1..d1 (Question ratings) │
                                      │ stress_score (Float 0-100)│
                                      │ stress_level (Category)   │
                                      │ ai_note (Text, optional)  │
                                      └───────────────────────────┘
```

## Installation & Setup

### 1. Prerequisites

* Python 3.10 or higher
* `pip` and `virtualenv`

### 2. Environment Setup

```bash
# Clone repository
git clone https://github.com/your-org/BalancED.git
cd BalancED

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Model Generation

Train the local `.joblib` model binary for your environment:

```bash
python ml/train_model.py
```

### 4. Database Setup & Static Assets

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 5. Running the Application

```bash
# Optional: Set Groq API Key for AI Notes
export GROQ_API_KEY="your-groq-api-key" # On Windows: set GROQ_API_KEY="your-groq-api-key"

python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## Limitations & Technical Considerations

1. **Non-Clinical Index:** The stress score is a dataset-derived statistical estimate, not a diagnostic clinical instrument.
2. **Dataset Scope:** Trained on a single university survey dataset; predictions may not generalize across all academic or demographic populations.
3. **Custom Cutoffs:** Qualitative risk levels (Normal, Mild, Moderate, High Risk) are team-defined operational boundaries rather than standardized medical ranges.
4. **AI Dependencies:** AI-generated notes rely on a third-party service (Groq API); responses may vary, fail, or be affected by service latency/rate limits (free tier cap of \~30 requests/min).
5. **Static Advice per Check-in:** AI advice cards are generated at the time of assessment submission and remain fixed until the subsequent check-in.
6. **Auxiliary Metrics:** Height, weight, and chronic illness flags are stored for contextual advice adjustment (e.g., swapping active tasks for quiet routines) but do not manipulate the underlying ML stress score.
7. **Testing:** The project relies on manual testing on PythonAnywhere rather than automated tests.
8. **No Email:** Skipping email collection protects student identity, eliminates data leak risks involving personal emails, and speeds up account registration, though users cannot receive off-platform alerts or automated password recovery links if login details are lost.
