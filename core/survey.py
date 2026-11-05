"""
Field names match the dataset columns so the saved rows can be put
straight into the scikit-learn pipeline later.
"""

AGREE = [(1, 'Strongly disagree'), (2, 'Disagree'), (3, 'Neutral'), (4, 'Agree'), (5, 'Strongly agree')]
FREQUENCY = [(1, 'Never'), (2, 'Rarely'), (3, 'Sometimes'), (4, 'Often'), (5, 'Always')]
LEVEL = [(1, 'Very low'), (2, 'Low'), (3, 'Moderate'), (4, 'High'), (5, 'Very high')]
YES_NO = [('True', 'Yes'), ('False', 'No')]

SECTIONS = [
    {
        'title': 'Academic factors',
        'intro': 'How much do you agree with each statement?',
        'questions': [
            ('b1_pressure_high_grades', 'I feel pressure to achieve high grades.', AGREE),
            ('b2_workload_overwhelming', 'My academic workload feels overwhelming.', AGREE),
            ('b3_balance_difficult', 'I find it difficult to balance study and personal life.', AGREE),
        ],
    },
    {
        'title': 'Psychological stress indicators',
        'intro': 'How much do you agree with each statement?',
        'questions': [
            ('c1_anxious_academics', 'I often feel anxious about my academic performance.', AGREE),
            ('c2_concentration_hard', 'I find it hard to concentrate on studies.', AGREE),
            ('c4_mentally_exhausted', 'I feel mentally exhausted after classes or study sessions.', AGREE),
            ('c5_worry_future', 'I worry excessively about the future.', AGREE),
        ],
    },
    {
        'title': 'Physical and behavioral symptoms',
        'intro': 'How much do you agree with the statement?',
        'questions': [
            ('d1_headaches_pain', 'I suffer from headaches or body pain during stressful periods.', AGREE),
        ],
    },
    {
        'title': 'Self-evaluation of stress level',
        'intro': '',
        'questions': [
            ('e2_overall_stress', 'How would you rate your overall stress level at present?', LEVEL),
        ],
    },
]

# Every 1-5 question (these default to 3 in the form and in the database)
LIKERT_FIELDS = [
    name for section in SECTIONS for name, _text, choices in section['questions'] if choices is not YES_NO
]
YES_NO_FIELDS = [
    name for section in SECTIONS for name, _text, choices in section['questions'] if choices is YES_NO
]
SURVEY_FIELDS = LIKERT_FIELDS + YES_NO_FIELDS

# No reverse-scored questions are left in the reduced survey.
REVERSE_KEYED = set()

# Same categories as the dataset's Avg_Daily_Study_Hours column
STUDY_HOURS_CHOICES = [('<2', 'Less than 2 hours'), ('2–4', '2–4 hours'), ('4–6', '4–6 hours'), ('>6', 'More than 6 hours')]
MAJOR_CHOICES = [(m, m) for m in (
    'Arts & Humanities', 'Business', 'Computer Science', 'Engineering',
    'Law', 'Medicine/Health', 'Science', 'Social Science',
)]
GENDER_CHOICES = [(v, v) for v in ('Female', 'Male', 'Other')]
