from datetime import date

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .survey import GENDER_CHOICES, MAJOR_CHOICES


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

    # Secondary (optional)
    height_cm = models.FloatField(null=True, blank=True, validators=[MinValueValidator(100), MaxValueValidator(250)])
    weight_kg = models.FloatField(null=True, blank=True, validators=[MinValueValidator(25), MaxValueValidator(300)])
    chronic_illnesses = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_complete(self):
        return bool(self.name and self.date_of_birth and self.major and self.year_of_enrollment
                    and self.gender and self.courses_taken)

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def __str__(self):
        return f'{self.name} ({self.user.get_username()})'


def likert():
    """1-5 answer that defaults to 3 (Neutral)."""
    return models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])


class Assessment(models.Model):
    """One row every time the student fills in the questionnaire: the survey answers plus the prediction."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assessments')
    created_at = models.DateTimeField(auto_now_add=True)

    # Section B
    b1_pressure_high_grades = likert()
    b2_workload_overwhelming = likert()
    b3_balance_difficult = likert()
    b4_sufficient_sleep = likert()
    b5_procrastination = likert()
    b6_physical_activity = likert()
    b7_excessive_social_media = likert()
    # Section C
    c1_anxious_academics = likert()
    c2_concentration_hard = likert()
    c3_mood_swings = likert()
    c4_mentally_exhausted = likert()
    c5_worry_future = likert()
    c6_hopelessness_sadness = likert()
    # Section D
    d1_headaches_pain = likert()
    d2_appetite_change = likert()
    d3_sleep_trouble = likert()
    d4_isolation = likert()
    d5_unhealthy_coping = likert()
    # Section E
    e1_stress_frequency = likert()
    e2_overall_stress = likert()
    e3_sought_professional_help = models.BooleanField(default=False)
    e4_affects_academic_performance = models.BooleanField(default=False)

    # Prediction result
    stress_score = models.FloatField(null=True, blank=True)   # 0-100
    stress_level = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.get_username()} - {self.created_at:%Y-%m-%d %H:%M} - {self.stress_level or "n/a"}'
