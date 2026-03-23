from django.urls import path
from . import views

urlpatterns = [

    # ================= STUDENT LOGIN ================= #
    path('student/', views.student_login, name='student_login'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),

    # ================= REPORTS (ADMIN SIDE) ================= #
    path('admin/reports/', views.reports_dashboard, name='reports'),

    # ================= PDF DOWNLOADS ================= #
    path('download-students-pdf/', views.download_students_pdf, name='students_pdf'),
    path('download-fee-report/', views.download_fee_report, name='fee_report'),
    path('download-defaulter-report/', views.download_defaulter_report, name='defaulter_report'),

    # ================= ATTENDANCE ================= #
    path('attendance/', views.attendance_batches, name='attendance_batches'),  # ✅ NEW
    path('attendance/<int:batch_id>/', views.mark_attendance, name='mark_attendance'),
    path('attendance-report/', views.attendance_report, name='attendance_report'),
]


