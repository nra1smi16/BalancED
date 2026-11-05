"""
"Note of the Day" on the dashboard. All messages are written by hand (no outside service).

How a note is built:
  1. Before there is a prediction, one of the general messages is shown (each has a small activity).
  2. After a prediction, the note has up to three parts:
       opening   - a short sentence that fits the student's stress level
       activity  - a routine activity picked from a pool: the routines for their level, plus one activity
                   that matches their highest-rated concern in the questionnaire (when they rated it 4 or 5)
       support   - for High Risk only, a reminder that talking to someone can help
  3. The picks rotate with the date, so a student sees the same note all day and a new one tomorrow.
"""
from datetime import date

GENERAL = [   # no prediction yet
    "Small steps still count. Pick one task and give it 15 minutes.",
    "Rest is part of studying. Take a short break away from your screen.",
    "You don't have to feel ready to begin. Open your notes for five minutes.",
    "One hard week doesn't define your semester. Take a short walk today.",
    "Asking for help is a okay. Ask a classmate about one thing you're unsure of.",
    "Progress can be small. Write down one thing you finished today.",
    "Your worth isn't measured by your workload. Do one thing you enjoy today.",
]

OPENINGS = {
    'Normal': ["You're managing well.", "Things look steady right now."],
    'Mild': ["A little stress is normal.", "You're handling some pressure."],
    'Moderate': ["It's a heavy stretch, and that's okay.", "Things feel heavy right now, and that's okay."],
    'High Risk': ["Be gentle with yourself today.", "You don't have to handle everything alone."],
}

# Routine activities suited to each stress level
ROUTINES = {
    'Normal': [
        "Keep your usual sleep schedule tonight.",
        "Take a short walk after your next class.",
        "Spend ten minutes on something you enjoy.",
    ],
    'Mild': [
        "Plan tomorrow's study tasks tonight.",
        "Take a five-minute break every hour you study.",
        "Take a ten-minute walk between classes to reset.",
    ],
    'Moderate': [
        "Write down your three most important tasks and start with one.",
        "Set a fixed bedtime and keep screens out of the last hour.",
        "Try five minutes of slow breathing before you study.",
    ],
    'High Risk': [
        "Drink some water and rest for ten minutes.",
        "Write down what is weighing on you, then pick one thing to postpone.",
        "Step outside for ten minutes of fresh air.",
    ],
}

# Activity matching the student's highest-rated concern (field names from the Assessment model)
CONCERN_ACTIVITIES = {
    'b1_pressure_high_grades': "Set a 'good enough' goal for one task today.",
    'b2_workload_overwhelming': "List your tasks, then start with just one.",
    'b3_balance_difficult': "Plan one non-study activity today, even for 20 minutes.",
    'c1_anxious_academics': "Take five slow breaths before you start studying.",
    'c2_concentration_hard': "Try one 25-minute focus session, then a 5-minute break.",
    'c4_mentally_exhausted': "Take a 10-minute walk between study sessions.",
    'c5_worry_future': "Write down one worry and one small next step.",
    'd1_headaches_pain': "Drink water and rest your eyes away from screens for five minutes.",
}

SUPPORT_LINE = "Talking to someone you trust, or to the counseling service below, can help too."

# When the student has listed a chronic illness (only the fact that they did, never what it is),
# physical suggestions are swapped for quiet ones and a short reminder is added.
HEALTH_LINE = "Go at your own pace and do what feels right for your body."
GENTLE_SWAPS = {
    "Take a short walk today.": "Take a quiet break today.",
    "One hard week doesn't define your semester. Take a short walk today.":
        "One hard week doesn't define your semester. Take a quiet break today.",
    "Take a short walk after your next class.": "Take a quiet ten-minute break after your next class.",
    "Take a ten-minute walk between classes to reset.": "Take a quiet ten-minute break between classes to reset.",
    "Step outside for ten minutes of fresh air.": "Sit somewhere quiet for ten minutes and breathe slowly.",
    "Take a 10-minute walk between study sessions.": "Take a quiet 10-minute break between study sessions.",
}
HIGH_CONCERN = 4   # answers of 4 (agree) or 5 (strongly agree) count as a concern


def _top_concern_activity(assessment, day):
    """Activity for the highest-rated concern, or None when nothing was rated 4 or 5."""
    if assessment is None:
        return None
    scores = {field: getattr(assessment, field, 0) for field in CONCERN_ACTIVITIES}
    top = max(scores.values())
    if top < HIGH_CONCERN:
        return None
    tied = sorted(field for field, value in scores.items() if value == top)
    return CONCERN_ACTIVITIES[tied[day % len(tied)]]


def _gentle(text, gentle):
    return GENTLE_SWAPS.get(text, text) if gentle else text


def daily_note(level=None, assessment=None, gentle=False):
    day = date.today().toordinal()
    if level not in OPENINGS:
        note = _gentle(GENERAL[day % len(GENERAL)], gentle)
        return f'{note} {HEALTH_LINE}' if gentle else note

    pool = [_gentle(text, gentle) for text in ROUTINES[level]]
    concern = _top_concern_activity(assessment, day)
    if concern:
        pool.append(_gentle(concern, gentle))

    openings = OPENINGS[level]
    parts = [openings[(day // len(pool)) % len(openings)], pool[day % len(pool)]]
    if gentle:
        parts.append(HEALTH_LINE)
    if level == 'High Risk':
        parts.append(SUPPORT_LINE)
    return ' '.join(parts)
