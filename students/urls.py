from django.urls import path
from . import views
from . import question_views


urlpatterns = [

    # ==========================================================
    # STUDENT LOGIN
    # ==========================================================

   path('student/', views.student_login, name='student_login'),

path(
    'student/change-password/',
    views.student_change_password,
    name='student_change_password'
),

path(
    'student/reset-password/',
    views.student_reset_password,
    name='student_reset_password'
),

path(
    'student/forgot-password/',
    views.student_forgot_password,
    name='student_forgot_password'
),

path('student/dashboard/', views.student_dashboard, name='student_dashboard'),

path('student/logout/', views.student_logout, name='student_logout'),
    # ==========================================================
    # STUDENT EXAMS
    # ==========================================================

    path('student/exams/', views.student_exam_list, name='student_exams'),
    path('student/exam/<int:exam_id>/', views.start_exam, name='start_exam'),

    # ==========================================================
    # ADMIN REPORTS
    # ==========================================================

    path('reports/', views.reports_dashboard, name='reports'),

    # ==========================================================
    # PDF DOWNLOADS
    # ==========================================================

    path('download-students-pdf/', views.download_students_pdf, name='students_pdf'),
    path('download-fee-report/', views.download_fee_report, name='fee_report'),
    path('download-defaulter-report/', views.download_defaulter_report, name='defaulter_report'),

    # ==========================================================
    # ATTENDANCE
    # ==========================================================

    path('attendance/', views.attendance_batches, name='attendance_batches'),
    path('attendance/<int:batch_id>/', views.mark_attendance, name='mark_attendance'),
    path('attendance-report/', views.attendance_report, name='attendance_report'),

    # ==========================================================
    # STAFF PANEL
    # ==========================================================

    path('staff-login/', views.staff_login, name='staff_login'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path("staff-logout/", views.staff_logout, name="staff_logout"),

    # ==========================================================
    # EXAMS
    # ==========================================================

    path('operations/exams/create/', views.create_exam, name='create_exam'),
    path('operations/exams/library/', views.exam_library, name='exam_library'),
    path('operations/exams/<int:exam_id>/edit/', views.edit_test, name='edit_test'),
    path('operations/exams/<int:exam_id>/assign/', views.assign_test, name='assign_test'),

    # ==========================================================
    # QUESTION BANK
    # ==========================================================

    path('questions/', question_views.question_dashboard, name='question_dashboard'),
    path('questions/add/', question_views.create_question, name='create_question'),
]