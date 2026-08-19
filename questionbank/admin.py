from django.contrib import admin
from .models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'class_name',
        'subject',
        'chapter',
        'topic',
        'question_type',
        'difficulty',
        'marks',
        'is_active',
        'created_at',
    )

    list_filter = (
        'class_name',
        'subject',
        'question_type',
        'difficulty',
        'is_active',
    )

    search_fields = (
        'topic',
        'chapter',
        'keywords',
        'question_text',
    )

    ordering = ('-created_at',)
