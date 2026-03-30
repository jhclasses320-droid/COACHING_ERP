from django.contrib import admin
from django.db.models import Sum
import random
from django.utils.html import format_html
from datetime import date
from urllib.parse import quote  # ✅ ADDED

from .models import (
    School, Batch, Student, FeePayment, Query,
    Subject, Topic, Question,
    Exam, ExamQuestion
)

# ================= CUSTOM ADMIN SITE ================= #
class MyAdminSite(admin.AdminSite):
    site_header = "JH CLASSES"
    site_title = "JH CLASSES"
    index_title = "Dashboard"

    def index(self, request, extra_context=None):

        total_students = Student.objects.count()
        total_fees = Student.objects.aggregate(total=Sum('fee_amount'))['total'] or 0
        total_paid = FeePayment.objects.aggregate(total=Sum('amount'))['total'] or 0
        pending_fees = total_fees - total_paid

        # ✅ BIRTHDAY LOGIC
        today = date.today()
        birthday_students = Student.objects.filter(
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

        return super().index(request, extra_context=extra_context)


# ✅ CREATE INSTANCE
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
        'whatsapp_fee',      # ✅ NEW
        'whatsapp_birthday'  # ✅ NEW
    )

    def student_photo_preview(self, obj):
        if obj.student_photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius:5px;" />',
                obj.student_photo.url
            )
        return "No Image"

    student_photo_preview.short_description = 'Photo'

    # ✅ WHATSAPP FEE REMINDER
    def whatsapp_fee(self, obj):
        if not obj.student_mobile:
            return "No Number"

        message = f"""
Hello {obj.father_name or 'Parent'},

This is JH Classes.

Fee for {obj.student_name} ({obj.batch}) of ₹{obj.fee_amount} is pending.
Kindly pay at the earliest.

Thank you.
"""

        url = f"https://wa.me/91{obj.student_mobile}?text={quote(message)}"

        return format_html(
            '<a href="{}" target="_blank" style="background:#25D366;color:white;padding:5px 10px;border-radius:5px;text-decoration:none;">📲 Fee</a>',
            url
        )

    whatsapp_fee.short_description = "Fee Reminder"

    # ✅ WHATSAPP BIRTHDAY WISH
    def whatsapp_birthday(self, obj):
        if not obj.student_mobile or not obj.date_of_birth:
            return "-"

        today = date.today()

        if obj.date_of_birth.day == today.day and obj.date_of_birth.month == today.month:
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


admin_site.register(Student, StudentAdmin)


admin_site.register(FeePayment)
admin_site.register(Query)


# ================= SUBJECT ================= #
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name',)

admin_site.register(Subject, SubjectAdmin)


# ================= TOPIC ================= #
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject')
    list_filter = ('subject',)
    search_fields = ('name',)

admin_site.register(Topic, TopicAdmin)


# ================= QUESTION ================= #
class QuestionAdmin(admin.ModelAdmin):

    fieldsets = (

        ("📘 Question", {
            'fields': (
                'topic',
                'question_text',
                'question_image',
            )
        }),

        ("🅰️ Option A", {
            'fields': (
                'option_a_text',
                'option_a_image',
            )
        }),

        ("🅱️ Option B", {
            'fields': (
                'option_b_text',
                'option_b_image',
            )
        }),

        ("🅲 Option C", {
            'fields': (
                'option_c_text',
                'option_c_image',
            )
        }),

        ("🅳 Option D", {
            'fields': (
                'option_d_text',
                'option_d_image',
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
            )
        }),

        ("📊 Marks Settings", {
            'fields': (
                'marks',
                'negative_marks',
            )
        }),

    )

    list_display = (
        'id',
        'short_question',
        'topic',
        'get_subject',
        'correct_option',
        'marks'
    )

    list_filter = ('topic__subject', 'topic')
    search_fields = ('question_text',)

    def short_question(self, obj):
        return obj.question_text[:50] if obj.question_text else "Image Question"

    def get_subject(self, obj):
        return obj.topic.subject.name


admin_site.register(Question, QuestionAdmin)


# ================= EXAM ================= #
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'topic', 'number_of_questions', 'duration')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        ExamQuestion.objects.filter(exam=obj).delete()

        questions = list(Question.objects.filter(topic=obj.topic))

        selected_questions = random.sample(
            questions,
            min(len(questions), obj.number_of_questions)
        )

        for q in selected_questions:
            ExamQuestion.objects.create(exam=obj, question=q)

admin_site.register(Exam, ExamAdmin)


# ================= EXAM QUESTION ================= #
class ExamQuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'question')

admin_site.register(ExamQuestion, ExamQuestionAdmin)

from .models import StudentExamAttempt, StudentAnswer

admin.site.register(StudentExamAttempt)
admin.site.register(StudentAnswer)