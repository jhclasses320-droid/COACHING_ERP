from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
import random
from django.utils.html import format_html
from datetime import date
from urllib.parse import quote
from django.http import JsonResponse
from django.urls import path

from .models import (
    School,
    Batch,
    Student,
    FeePayment,
    Query,
    Subject,
    Topic,
    Chapter,
    Question,
    Exam,
    ExamQuestion,
    StudentExamAttempt,
       StudentAnswer,
    StudyMaterial,
)


# ================= CUSTOM ADMIN SITE ================= #

class MyAdminSite(admin.AdminSite):
    site_header = "JH CLASSES"
    site_title = "JH CLASSES"
    index_title = ""

    def index(self, request, extra_context=None):

        total_students = Student.objects.filter(
            is_active=True
        ).count()

        total_fees = Student.objects.filter(
            is_active=True
        ).aggregate(total=Sum('fee_amount'))['total'] or 0

        total_paid = FeePayment.objects.filter(
            student__is_active=True
        ).aggregate(total=Sum('amount'))['total'] or 0

        pending_fees = total_fees - total_paid

        today = date.today()

        birthday_students = Student.objects.filter(
            is_active=True,
            date_of_birth__day=today.day,
            date_of_birth__month=today.month
        )

        extra_context = extra_context or {}

        extra_context.update({
            'total_students': total_students,
            'total_fees': total_fees,
            'pending_fees': pending_fees,
            'birthday_students': birthday_students,
        })

        return super().index(
            request,
            extra_context=extra_context
        )

        
admin_site = MyAdminSite(name='myadmin')


# ================= AUTH MODELS ================= #

from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)


# ================= BASIC MODELS ================= #

admin_site.register(School)
admin_site.register(Batch)


# ================= STUDENT ADMIN ================= #

class StudentAdmin(admin.ModelAdmin):

    list_display = (
        'student_name',
        'student_mobile',
        'student_photo_preview',
        'whatsapp_fee',
        'whatsapp_birthday',
    )

    search_fields = (
    'student_name',
    'student_id',
    'father_name',
    'mother_name',
    'student_mobile',
    'father_mobile',
    'mother_mobile',
    )

    list_filter = (
        'batch',
        'is_active',
    )

    ordering = (
        'student_name',
    )

    list_per_page = 25

    filter_horizontal = (
        'additional_batches',
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_active=True)

    def student_photo_preview(self, obj):
        if obj.student_photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius:5px;" />',
                obj.student_photo.url
            )
        return "No Image"

    student_photo_preview.short_description = "Photo"

    def whatsapp_fee(self, obj):

        if not obj.student_mobile:
            return "No Number"

        message = f"""
Hello {obj.father_name or 'Parent'},

This is JH Classes.

Fee for {obj.student_name} ({obj.batch}) of ₹{obj.fee_amount} is pending.
Kindly pay at the earliest.

This is a computer generated message.
Please ignore if already paid.

Thank you.
"""

        url = f"https://wa.me/91{obj.student_mobile}?text={quote(message)}"

        return format_html(
            '<a href="{}" target="_blank" style="background:#25D366;color:white;padding:5px 10px;border-radius:5px;text-decoration:none;">📲 Fee</a>',
            url
        )

    whatsapp_fee.short_description = "Fee Reminder"

    def whatsapp_birthday(self, obj):


        if not obj.student_mobile or not obj.date_of_birth:
            return "-"

        today = date.today()

        if (
            obj.date_of_birth.day == today.day
            and obj.date_of_birth.month == today.month
        ):

            message = f"""
Happy Birthday {obj.student_name}! 🎉

Wishing you success and happiness.

- JH Classes
"""

            url = f"https://wa.me/91{obj.student_mobile}?text={quote(message)}"

            return format_html(
                '<a href="{}" target="_blank" style="background:#ff9800;color:white;padding:5px 10px;border-radius:5px;text-decoration:none;">🎂 Wish</a>',
                url
            )

        return "-"

    whatsapp_birthday.short_description = "Birthday"

    
def save_model(self, request, obj, form, change):

        if not change and not obj.password:
            obj.password = make_password("1234")
            obj.must_change_password = False

        super().save_model(request, obj, form, change)      



admin_site.register(Student, StudentAdmin)


# ================= OTHER MODELS ================= #

admin_site.register(FeePayment)
admin_site.register(Query)


# ================= SUBJECT ================= #

class SubjectAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'code',
    )

    search_fields = (
        'name',
    )


admin_site.register(Subject, SubjectAdmin)


# ================= TOPIC ================= #

class TopicAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'subject',
    )

    list_filter = (
        'subject',
    )

    search_fields = (
        'name',
    )


admin_site.register(Topic, TopicAdmin)

# ================= CHAPTER ================= #

class ChapterAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'topic',
        'get_subject',
        'is_active',
    )

    list_filter = (
        'topic__subject',
        'topic',
        'is_active',
    )

    search_fields = (
        'name',
        'topic__name',
    )

    ordering = (
        'topic__subject__name',
        'topic__name',
        'name',
    )

    def get_subject(self, obj):
        return obj.topic.subject.name

    get_subject.short_description = "Subject"


admin_site.register(Chapter, ChapterAdmin)

# ================= QUESTION ================= #

class QuestionAdmin(admin.ModelAdmin):

    readonly_fields = (
        'question_image_preview',
        'option_a_image_preview',
        'option_b_image_preview',
        'option_c_image_preview',
        'option_d_image_preview',
        'feedback_image_preview',
    )

    fieldsets = (

        ("📘 Question Details", {
    'fields': (
        'batch',
        'topic',
        'question_mode',
        'difficulty',
        'source',
        'estimated_time',
        'is_active',
    )
}),

        ("❓ Question", {
            'fields': (
                'question_text',
                'question_image',
                'question_image_preview',
            )
        }),

        ("🅰️ Option A", {
            'fields': (
                'option_a_text',
                'option_a_image',
                'option_a_image_preview',
            )
        }),

        ("🅱️ Option B", {
            'fields': (
                'option_b_text',
                'option_b_image',
                'option_b_image_preview',
            )
        }),

        ("🅲 Option C", {
            'fields': (
                'option_c_text',
                'option_c_image',
                'option_c_image_preview',
            )
        }),

        ("🅳 Option D", {
            'fields': (
                'option_d_text',
                'option_d_image',
                'option_d_image_preview',
            )
        }),

        ("✅ Correct Answer", {
            'fields': (
                'correct_option',
            )
        }),

        ("🧠 Feedback / Solution", {
            'fields': (
                'feedback_text',
                'feedback_image',
                'feedback_image_preview',
            )
        }),

        ("📊 Marks", {
            'fields': (
                'marks',
                'negative_marks',
            )
        }),

    )

    list_display = (
        'id',
        'batch',
        'short_question',
        'question_mode',
        'difficulty',
        'source',
        'topic',
        'get_subject',
        'correct_option',
        'marks',
        'is_active',
    )

    list_filter = (
        'batch',
        'question_mode',
        'difficulty',
        'source',
        'is_active',
        'topic__subject',
        'topic',
    )

    search_fields = (
        'question_text',
    )

    ordering = (
        '-id',
    )

    list_per_page = 25

    def short_question(self, obj):
        if obj.question_text:
            return obj.question_text[:60]
        return "Image Question"

    short_question.short_description = "Question"

    def get_subject(self, obj):
        return obj.topic.subject.name

    get_subject.short_description = "Subject"

    # ==========================================================
    # IMAGE PREVIEWS
    # ==========================================================

    def question_image_preview(self, obj):
        if obj.question_image:
            return format_html(
                '<img src="{}" style="max-width:1000px; max-height:700px; border:1px solid #ccc; padding:5px;" />',
                obj.question_image.url
            )
        return "No image uploaded"

    question_image_preview.short_description = "Question Preview"

    def option_a_image_preview(self, obj):
        if obj.option_a_image:
            return format_html(
                '<img src="{}" style="max-width:300px; max-height:200px;" />',
                obj.option_a_image.url
            )
        return ""

    option_a_image_preview.short_description = "Preview"

    def option_b_image_preview(self, obj):
        if obj.option_b_image:
            return format_html(
                '<img src="{}" style="max-width:300px; max-height:200px;" />',
                obj.option_b_image.url
            )
        return ""

    option_b_image_preview.short_description = "Preview"

    def option_c_image_preview(self, obj):
        if obj.option_c_image:
            return format_html(
                '<img src="{}" style="max-width:300px; max-height:200px;" />',
                obj.option_c_image.url
            )
        return ""

    option_c_image_preview.short_description = "Preview"

    def option_d_image_preview(self, obj):
        if obj.option_d_image:
            return format_html(
                '<img src="{}" style="max-width:300px; max-height:200px;" />',
                obj.option_d_image.url
            )
        return ""

    option_d_image_preview.short_description = "Preview"

    def feedback_image_preview(self, obj):
        if obj.feedback_image:
            return format_html(
                '<img src="{}" style="max-width:1000px; max-height:500px; border:1px solid #ccc; padding:5px;" />',
                obj.feedback_image.url
            )
        return ""

    feedback_image_preview.short_description = "Feedback Preview"


admin_site.register(Question, QuestionAdmin)

# ================= EXAM ================= #

class ExamAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'topic',
        'number_of_questions',
        'duration',
    )

    def save_model(self, request, obj, form, change):

        super().save_model(request, obj, form, change)

        # Remove existing questions
        ExamQuestion.objects.filter(exam=obj).delete()

        # Pick active questions only
        questions = list(
            Question.objects.filter(
            batch=obj.batch,
            topic=obj.topic,
            is_active=True,

            )
        )

        selected_questions = random.sample(
            questions,
            min(len(questions), obj.number_of_questions)
        )

        for q in selected_questions:
            ExamQuestion.objects.create(
                exam=obj,
                question=q
            )


admin_site.register(Exam, ExamAdmin)


# ================= EXAM QUESTION ================= #

class ExamQuestionAdmin(admin.ModelAdmin):

    list_display = (
        'exam',
        'question',
    )


admin_site.register(ExamQuestion, ExamQuestionAdmin)


# ================= STUDENT EXAM ================= #

admin_site.register(StudentExamAttempt)
admin_site.register(StudentAnswer)

# ================= STUDY MATERIAL ================= #

class StudyMaterialAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'batch',
        'subject',
        'chapter',
        'is_active',
    )

    list_filter = (
        'batch',
        'subject',
        'chapter',
        'is_active',
    )

    search_fields = (
        'title',
        'dropbox_link',
    )

    ordering = (
        'batch',
        'subject',
        'chapter',
        'title',
    )


admin_site.register(StudyMaterial, StudyMaterialAdmin)