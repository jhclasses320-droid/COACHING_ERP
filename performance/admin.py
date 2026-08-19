from django.contrib import admin
from students.admin import admin_site

from .models import (
    AssessmentType,
    Assessment,
    AssessmentSubject,
)


# ==========================================================
# INLINE
# ==========================================================

class AssessmentSubjectInline(admin.TabularInline):
    model = AssessmentSubject
    extra = 1

    fields = (
        "subject",
        "topic",
        "chapters",
        "chapter_covered",
        "maximum_marks",
        "duration_minutes",
    )


# ==========================================================
# ASSESSMENT TYPE
# ==========================================================

class AssessmentTypeAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "display_order",
        "is_active",
        "created_on",
    )

    list_editable = (
        "display_order",
        "is_active",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "display_order",
    )


# ==========================================================
# ASSESSMENT
# ==========================================================

class AssessmentAdmin(admin.ModelAdmin):

    list_display = (
        "assessment_name",
        "assessment_type",
        "academic_session",
        "batch",
        "assessment_date",
        "status",
    )

    list_filter = (
        "assessment_type",
        "academic_session",
        "batch",
        "status",
    )

    search_fields = (
        "assessment_name",
    )

    inlines = [
        AssessmentSubjectInline,
    ]


# ==========================================================
# ASSESSMENT SUBJECT
# ==========================================================

class AssessmentSubjectAdmin(admin.ModelAdmin):

    list_display = (
        "assessment",
        "subject",
        "chapter_covered",
        "maximum_marks",
        "duration_minutes",
    )


# ==========================================================
# REGISTER WITH CUSTOM ADMIN
# ==========================================================

admin_site.register(AssessmentType, AssessmentTypeAdmin)
admin_site.register(Assessment, AssessmentAdmin)
admin_site.register(AssessmentSubject, AssessmentSubjectAdmin)