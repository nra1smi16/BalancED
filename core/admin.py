from django.contrib import admin

from .models import Assessment, StudentProfile
from .survey import SURVEY_FIELDS


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    # 'age' and 'years_enrolled' are calculated (from date of birth / year of enrollment), not stored columns
    list_display = ('name', 'user', 'major', 'gender', 'age', 'years_enrolled',
                    'courses_taken', 'avg_daily_study_hours', 'created_at')
    search_fields = ('name', 'user__username', 'major')
    list_filter = ('major', 'gender', 'avg_daily_study_hours')


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'stress_level', 'stress_score') + tuple(SURVEY_FIELDS)
    list_filter = ('stress_level', 'created_at')
    search_fields = ('user__username', 'stress_level')
