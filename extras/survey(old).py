"""
Single source of truth for the survey.
Field names match the dataset columns (lower-cased) so the saved rows can be fed
straight into the scikit-learn pipeline later.
"""

AGREE = [(1, 'Strongly disagree'), (2, 'Disagree'), (3, 'Neutral'), (4, 'Agree'), (5, 'Strongly agree')]
FREQUENCY = [(1, 'Never'), (2, 'Rarely'), (3, 'Sometimes'), (4, 'Often'), (5, 'Always')]
LEVEL = [(1, 'Very low'), (2, 'Low'), (3, 'Moderate'), (4, 'High'), (5, 'Very high')]
YES_NO = [('True', 'Yes'), ('False', 'No')]

SECTIONS = [
    {
        'title': 'Academic and lifestyle factors',
        'intro': 'How much do you agree with each statement?',
        'questions': [
            ('b1_pressure_high_grades', 'I feel pressure to achieve high grades.', AGREE),
            ('b2_workload_overwhelming', 'My academic workload feels overwhelming.', AGREE),
            ('b3_balance_difficult', 'I find it difficult to balance study and personal life.', AGREE),
            ('b4_sufficient_sleep', 'I get sufficient sleep on most nights.', AGREE),
            ('b5_procrastination', 'I often procrastinate on academic tasks.', AGREE),
            ('b6_physical_activity', 'I engage in regular physical activity.', AGREE),
            ('b7_excessive_social_media', 'I spend excessive time on social media or online entertainment.', AGREE),
        ],
    },
    {
        'title': 'How you have been feeling',
        'intro': 'How much do you agree with each statement?',
        'questions': [
            ('c1_anxious_academics', 'I often feel anxious about my academic performance.', AGREE),
            ('c2_concentration_hard', 'I find it hard to concentrate on my studies.', AGREE),
            ('c3_mood_swings', 'I experience frequent mood swings.', AGREE),
            ('c4_mentally_exhausted', 'I feel mentally exhausted after classes or study sessions.', AGREE),
            ('c5_worry_future', 'I worry excessively about the future.', AGREE),
            ('c6_hopelessness_sadness', 'I experience feelings of hopelessness or sadness.', AGREE),
        ],
    },
    {
        'title': 'Physical and behavioral symptoms',
        'intro': 'How much do you agree with each statement?',
        'questions': [
            ('d1_headaches_pain', 'I suffer from headaches or body pain during stressful periods.', AGREE),
            ('d2_appetite_change', 'I experience changes in appetite (eating more or less than usual).', AGREE),
            ('d3_sleep_trouble', 'I have trouble sleeping or wake up frequently at night.', AGREE),
            ('d4_isolation', 'I tend to isolate myself when feeling stressed.', AGREE),
            ('d5_unhealthy_coping', 'I engage in unhealthy coping mechanisms (e.g., smoking, overeating).', AGREE),
        ],
    },
    {
        'title': 'Self-evaluation of stress',
        'intro': '',
        'questions': [
            ('e1_stress_frequency', 'How often do you feel stressed during your academic routine?', FREQUENCY),
            ('e2_overall_stress', 'How would you rate your overall stress level at present?', LEVEL),
            ('e3_sought_professional_help', 'Have you ever sought professional help or counseling for stress?', YES_NO),
            ('e4_affects_academic_performance', 'Do you believe stress significantly affects your academic performance?', YES_NO),
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

# "Positive" statements: a high agreement means LESS stress, so they are reverse-scored.
REVERSE_KEYED = {'b4_sufficient_sleep', 'b6_physical_activity'}

STUDY_HOURS_CHOICES = [('<2', 'Less than 2 hours'), ('2–4', '2–4 hours'), ('4–6', '4–6 hours'), ('>6', 'More than 6 hours')]
MAJOR_CHOICES = [(m, m) for m in (
    'Arts & Humanities', 'Business', 'Computer Science', 'Engineering',
    'Law', 'Medicine/Health', 'Science', 'Social Science',
)]
GENDER_CHOICES = [(v, v) for v in ('Female', 'Male', 'Other')]
