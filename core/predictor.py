"""
Prediction + recommendations.

predict_stress() is a PLACEHOLDER. In this dataset the stress index is an exact
function of the 20 scale answers (B1-E2, with B4 and B6 reverse-scored), so this
function reproduces it. When the scikit-learn model is ready, replace the body
of predict_stress() with something like:

    model = joblib.load(settings.BASE_DIR / 'model.pkl')
    return float(model.predict([[getattr(assessment, f) for f in LIKERT_FIELDS]])[0])
"""
from .survey import LIKERT_FIELDS, REVERSE_KEYED


def predict_stress(assessment):
    total = 0
    for field in LIKERT_FIELDS:
        value = getattr(assessment, field)
        total += (6 - value) if field in REVERSE_KEYED else value
    n = len(LIKERT_FIELDS)
    return round((total - n) / (4 * n) * 100, 1)


def level_for_score(score):
    if score < 25:
        return 'Normal'
    if score < 50:
        return 'Mild'
    if score < 75:
        return 'Moderate'
    return 'High Risk'


MEANINGS = {
    'Normal': 'Your answers suggest a low level of academic stress right now. Keep doing what works for you.',
    'Mild': 'Your answers suggest some stress, but it looks manageable. Small adjustments can help it stay that way.',
    'Moderate': 'Your answers suggest a noticeable level of stress. It is a good time to adjust your routine and workload.',
    'High Risk': 'Your answers suggest a high level of stress. It is important to take action and look after your well-being.',
}

GENERAL = {
    'Normal': [
        'Keep the routines that are working for you.',
        'Check in with yourself before busy exam periods.',
    ],
    'Mild': [
        'Plan your study week so deadlines do not pile up.',
        'Take short, regular breaks while studying.',
    ],
    'Moderate': [
        'Manage your time with a weekly plan and realistic daily goals.',
        'Take regular breaks and protect your sleep.',
        'Talk to a friend, family member, or academic advisor about your workload.',
    ],
    'High Risk': [
        'Manage your time and cut back on what you can postpone.',
        'Take regular breaks and get enough sleep.',
        'Talk to someone you trust about how you are feeling.',
        'Seek professional help if needed, such as a counselor.',
    ],
}

# (condition, tip) - shown when the student's own answers point to it
TAILORED = [
    (lambda a: a.b4_sufficient_sleep <= 2 or a.d3_sleep_trouble >= 4,
     'Sleep: try a fixed bedtime and keep screens out of the last hour of your evening.'),
    (lambda a: a.b6_physical_activity <= 2,
     'Movement: even a 15-minute walk most days can ease stress.'),
    (lambda a: a.b5_procrastination >= 4,
     'Procrastination: break tasks into small steps and start with 10 minutes.'),
    (lambda a: a.b7_excessive_social_media >= 4,
     'Screen time: set limits on social media during study sessions.'),
    (lambda a: a.b3_balance_difficult >= 4,
     'Balance: schedule free time in your week the same way you schedule classes.'),
    (lambda a: a.d4_isolation >= 4 or a.c6_hopelessness_sadness >= 4,
     'Connection: reach out to someone you trust, or to a counselor, rather than carrying this alone.'),
]


def recommendations_for(assessment, level):
    tips = list(GENERAL[level])
    tips += [text for condition, text in TAILORED if condition(assessment)]
    return tips
