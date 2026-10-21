"""
"A note for today" on the dashboard.
Messages are written by hand for each stress level (no outside service needed), and one of them is picked per day.
The level comes from the saved assessment (stress_level), so it starts using these automatically
once the prediction model fills that column in.
"""
from datetime import date

MESSAGES = {
    'default': [   # no prediction yet
        "Small steps still count. Do the next thing, not everything.",
        "Rest is part of studying, not a break from it.",
        "You don't have to feel ready to begin.",
        "One hard week doesn't define your semester.",
        "Asking for help is a skill. Use it early.",
        "Progress today can be as small as opening your notes.",
        "Your worth isn't measured by your workload.",
    ],
    'Normal': [
        "You seem to be managing well right now. Keep the habits that are working for you.",
        "A steady routine is doing its job. Remember to rest even when things feel easy.",
        "Good balance takes effort, and it shows. Keep checking in with yourself.",
        "Notice what is going right this week and do a little more of it.",
    ],
    'Mild': [
        "A little stress is normal. A short break or a walk can help you reset.",
        "Try planning tomorrow tonight. A small plan can make the day feel lighter.",
        "Keep pacing yourself. You are doing better than you might think.",
        "Take it one task at a time. You don't have to do everything today.",
    ],
    'Moderate': [
        "Things may feel heavy right now, and that is okay. Pick the one task that matters most today.",
        "Protect your sleep this week. It makes everything else easier.",
        "Talking to a friend or an advisor about your workload can make it feel lighter.",
        "It is fine to slow down. Rest is part of getting things done.",
    ],
    'High Risk': [
        "You don't have to carry this alone. Please consider talking to someone you trust today.",
        "Be gentle with yourself today. One small step is enough.",
        "If things feel like too much, reaching out to a counselor is a good step to take.",
        "Your well-being matters more than any deadline. Take a breath, then take the next small step.",
    ],
}


def daily_note(level=None):
    pool = MESSAGES.get(level) or MESSAGES['default']
    return pool[date.today().toordinal() % len(pool)]
