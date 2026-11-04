from datetime import date

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .survey import GENDER_CHOICES, MAJOR_CHOICES, STUDY_HOURS_CHOICES


# What students write when they have nothing to list (so it does not count as a chronic illness)
NO_CONDITION_WORDS = {'', 'none', 'no', 'n/a', 'na', 'nil', 'nothing', '-', '--', 'لا', 'لا يوجد', 'لايوجد'}


def age_from(dob, today=None):
    today = today or date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class StudentProfile(models.Model):
    """Everything about the student that is NOT a survey answer. The student can edit it any time on the profile page."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')

    # Primary (required before the student can use the app)
    name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    major = models.CharField(max_length=50, choices=MAJOR_CHOICES, blank=True)
    year_of_enrollment = models.PositiveSmallIntegerField(null=True, blank=True)
    # blank at the database level only because sign up creates the row before this page is filled in;
    # the profile form makes it required.
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)

    # Courses taken is a primary attribute too (null/blank only because sign up creates the row first;
    # the profile form makes it required).
    courses_taken = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(15)])
    # Average daily study hours is a primary attribute as well (same bins as the dataset)
    avg_daily_study_hours = models.CharField(max_length=3, choices=STUDY_HOURS_CHOICES, blank=True)

    # Secondary (optional)
    height_cm = models.FloatField(null=True, blank=True, validators=[MinValueValidator(100), MaxValueValidator(250)])
    weight_kg = models.FloatField(null=True, blank=True, validators=[MinValueValidator(25), MaxValueValidator(300)])
    chronic_illnesses = models.TextField(blank=True)

    # Consent for the AI-written Note of the Day. Off by default; the student turns it on in the profile.
    ai_opt_in = models.BooleanField(default=False)
    ai_opt_in_at = models.DateTimeField(null=True, blank=True)     # when they agreed (empty when it is off)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_complete(self):
        return bool(self.name and self.date_of_birth and self.major and self.year_of_enrollment
                    and self.gender and self.courses_taken and self.avg_daily_study_hours)

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        return age_from(self.date_of_birth)

    @property
    def has_chronic_condition(self):
        """True when the student listed something under chronic illnesses (only whether, never what)."""
        text = (self.chronic_illnesses or '').strip().strip('.!').strip().lower()
        return text not in NO_CONDITION_WORDS

    @property
    def years_enrolled(self):
        """Calculated from the year of enrollment (0 in the first year)."""
        if not self.year_of_enrollment:
            return None
        return max(0, date.today().year - self.year_of_enrollment)

    def __str__(self):
        return f'{self.name} ({self.user.get_username()})'


def likert():
    """1-5 answer that defaults to 3 (Neutral)."""
    return models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])


class Assessment(models.Model):
    """One row every time the student fills in the questionnaire: the survey answers plus the prediction."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assessments')
    created_at = models.DateTimeField(auto_now_add=True)

    # Reduced survey: 9 questions (1-5), all default to 3
    # Section B - academic factors
    b1_pressure_high_grades = likert()
    b2_workload_overwhelming = likert()
    b3_balance_difficult = likert()
    # Section C - psychological stress indicators
    c1_anxious_academics = likert()
    c2_concentration_hard = likert()
    c4_mentally_exhausted = likert()
    c5_worry_future = likert()
    # Section D - physical and behavioral symptoms
    d1_headaches_pain = likert()
    # Section E - self-evaluation
    e2_overall_stress = likert()

    # Prediction result
    stress_score = models.FloatField(null=True, blank=True)   # 0-100
    stress_level = models.CharField(max_length=20, blank=True)

    # The Note of the Day written by the AI (filled only when an API key is set up; see ai.py).
    # Empty means the hand-written note from notes.py is shown instead.
    ai_advice = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.get_username()} - {self.created_at:%Y-%m-%d %H:%M} - {self.stress_level or "n/a"}'


class ExamDate(models.Model):
    """A day the student marked as an exam day on the dashboard calendar."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_dates')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']
        constraints = [models.UniqueConstraint(fields=['user', 'date'], name='one_exam_mark_per_user_and_day')]

    def __str__(self):
        return f'{self.user.get_username()} - exam on {self.date}'
