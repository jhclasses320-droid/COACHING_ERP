print(">>> PERFORMANCE URLS LOADED <<<")

from django.urls import path
from . import views


urlpatterns = [


        path(
        "create-test/",
        views.create_test,
        name="performance_create_test",
    ),
path(
    "question-selection/<int:exam_id>/",
    views.question_selection,
    name="performance_question_selection",
),

    # ==========================================================
    # TRANSACTIONS
    # ==========================================================

    path(
        "marks-entry/",
        views.marks_entry,
        name="performance_marks_entry",
    ),

    # ==========================================================
    # REPORTS HOME
    # ==========================================================

    path(
        "reports/",
        views.performance_reports,
        name="performance_reports",
    ),

    # ==========================================================
    # REPORTS
    # ==========================================================

    path(
        "reports/student/",
        views.student_performance_report,
        name="student_performance_report",
    ),

    # ==========================================================
    # ASSESSMENT REPORT
    # ==========================================================

    path(
        "reports/assessment/<int:assessment_subject_id>/",
        views.assessment_report,
        name="assessment_report",
    ),

    path(
        "reports/batch/",
        views.batch_performance_report,
        name="batch_performance_report",
    ),

    path(
        "reports/subject/",
        views.subject_analysis_report,
        name="subject_analysis_report",
    ),

    path(
        "reports/parent/",
        views.parent_report,
        name="parent_report",
    ),

]