"""
Asks Claude (through the Anthropic API) to write the student's Note of the Day.

What is sent: the 12 values the stress model uses, written as one short paragraph (age, gender, field of study,
study hours and 8 questionnaire ratings), plus the stress level the trained model gave. Never the name, username,
height, weight or chronic illnesses.

What comes back: the same three parts as the hand-written notes (see notes.py):
    opening   - a short sentence that fits the stress level
    activity  - one routine activity that suits the level and the student's highest-rated concerns
    support   - High Risk only: a reminder that talking to someone can help

The reply is checked before it is used. If the key is missing, the call fails, or the reply does not pass the
checks, the dashboard simply shows the hand-written note instead.

The API key is read from the ANTHROPIC_API_KEY environment variable. Never write the key in the code or push it
to GitHub. When the variable is not set, this feature is switched off.
"""
import json
import logging
import os
import re

try:
    import requests
except ImportError:          # the website still starts without it; the AI feature just stays off
    requests = None

from .notes import SUPPORT_LINE
from .survey import STUDY_HOURS_CHOICES

logger = logging.getLogger(__name__)

API_URL = 'https://api.anthropic.com/v1/messages'
DEFAULT_MODEL = 'claude-haiku-5-5'          # small and cheap; change with the ANTHROPIC_MODEL variable
TIMEOUT_SECONDS = 25

# The 8 questionnaire answers the model uses, in plain words (E2 is left out, like in the trained model)
CONCERN_LABELS = {
    'b1_pressure_high_grades': 'pressure to achieve high grades',
    'b2_workload_overwhelming': 'an overwhelming workload',
    'b3_balance_difficult': 'difficulty balancing study and personal life',
    'c1_anxious_academics': 'anxiety about academic performance',
    'c2_concentration_hard': 'trouble concentrating on studies',
    'c4_mentally_exhausted': 'mental exhaustion after classes or study',
    'c5_worry_future': 'worry about the future',
    'd1_headaches_pain': 'headaches or body pain during stressful periods',
}

SYSTEM_PROMPT = (
    "You write the short 'Note of the Day' for BalancED, a support tool for university students.\n\n"
    "You are given a description of one student and the stress level (Normal, Mild, Moderate or High Risk) "
    "that the app's model estimated for them. Write the note in three parts:\n"
    "- opening: one short sentence (at most 10 words) that fits the stress level and sounds warm.\n"
    "- activity: one routine activity (at most 18 words) that suits the stress level and the concerns the student "
    "rated highest. Use small, practical things such as a walk, a break, slow breathing, planning the next day, "
    "sleep habits or a short focus session.\n"
    "- support: only when the level is High Risk, one short sentence saying that talking to someone they trust or "
    "to the university counseling service can help. For every other level use an empty string.\n\n"
    "Rules: do not diagnose, do not give medical or medication advice, do not mention scores, numbers, ratings or "
    "AI, and do not write phone numbers, emails, links or names of organizations. If the description says the "
    "student lives with a long-term health condition, keep the activity gentle and flexible, avoid anything "
    "physically demanding, and do not mention the condition itself.\n\n"
    'Reply with ONLY a JSON object and nothing else: {"opening": "...", "activity": "...", "support": "..."}'
)

# Caps for each part, and a check that no contact details were invented
MAX_LENGTH = {'opening': 120, 'activity': 200, 'support': 200}
CONTACT_DETAILS = re.compile(r'https?://|www\.|@|\d{5,}', re.IGNORECASE)


def is_enabled():
    return bool(os.getenv('ANTHROPIC_API_KEY'))


def allowed_for(profile):
    """True only for a student who turned the AI note on in their profile (it is off by default)."""
    return bool(profile.ai_opt_in)


def build_prompt(profile, assessment):
    """The 12 values as one short paragraph, followed by the stress level from the trained model."""
    age = profile.age
    article = 'an' if age in (8, 11, 18) or 80 <= age <= 89 else 'a'
    who = {'Female': 'female student', 'Male': 'male student'}.get(profile.gender, 'student')
    hours = dict(STUDY_HOURS_CHOICES)[profile.avg_daily_study_hours].lower()
    ratings = '; '.join(f'{label} {getattr(assessment, field)}' for field, label in CONCERN_LABELS.items())
    # Only the fact that a condition was listed is shared, never what it is
    health = ' They live with a long-term health condition (the details are not shared).' if getattr(profile, 'has_chronic_condition', False) else ''
    return (
        f'The student is {article} {age}-year-old {who} studying {profile.major}, '
        f'who studies {hours} a day on average.{health} '
        f'On a scale from 1 (strongly disagree) to 5 (strongly agree), they rated these statements: {ratings}. '
        f'The app\'s model estimates their stress level as {assessment.stress_level}.'
    )


def _parse(text, level):
    """Pull the JSON object out of the reply, check it, and return the finished note (one string)."""
    if '{' not in text or '}' not in text:
        raise ValueError('The AI reply did not contain a JSON object')
    data = json.loads(text[text.index('{'): text.rindex('}') + 1])

    parts = {key: str(data.get(key) or '').strip() for key in MAX_LENGTH}
    if not parts['opening'] or not parts['activity']:
        raise ValueError('The AI reply was missing the opening or the activity')
    # Only High Risk gets the support sentence, and it always has one
    parts['support'] = (parts['support'] or SUPPORT_LINE) if level == 'High Risk' else ''
    for key, limit in MAX_LENGTH.items():
        if len(parts[key]) > limit:
            raise ValueError(f'The AI reply was too long ({key})')

    note = ' '.join(part for part in (parts['opening'], parts['activity'], parts['support']) if part)
    if CONTACT_DETAILS.search(note):
        raise ValueError('The AI reply contained contact details')
    return note


def ask_ai(profile, assessment):
    """Returns the note as one string; raises an exception if anything goes wrong."""
    if requests is None:
        raise RuntimeError("The 'requests' package is not installed (pip install requests)")

    # 1. Set your API key and endpoint
    api_key = os.getenv("ANTHROPIC_API_KEY")
    url = API_URL                                  # https://api.anthropic.com/v1/messages

    # 2. Define headers required by Anthropic API
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    # 3. Build the payload (the student's attributes, written as a paragraph, are the prompt)
    payload = {
        "model": os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL),
        "max_tokens": 2000,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": build_prompt(profile, assessment)}],
    }

    # 4. Send the POST request
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=TIMEOUT_SECONDS)

    # 5. Parse the response
    if response.status_code == 200:
        result = response.json()
        # the reply is a list of blocks; keep the text ones (other kinds, such as thinking, are skipped)
        text = "".join(block.get("text", "") for block in result.get("content", []) if block.get("type") == "text")
        return _parse(text, assessment.stress_level)
    raise RuntimeError(f"Error {response.status_code}: {response.text[:300]}")
