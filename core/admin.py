from django.contrib import admin
from .models import StudentProfile, Assessment

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'major', 'gender', 'created_at')
    search_fields = ('name', 'user__username', 'major')
    list_filter = ('major', 'gender')

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'stress_level', 'stress_score', 'created_at')
    list_filter = ('stress_level', 'created_at')
    search_fields = ('user__username', 'stress_level')
