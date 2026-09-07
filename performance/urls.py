print(">>> PERFORMANCE URLS LOADED <<<")

from django.urls import path
from . import views


urlpatterns = [

    # ==========================================================
    # CREATE TEST
    # ==========================================================

    path(
        "create-test/",
        views.create_test,
        name="performance_create_test",
    ),

    # ==========================================================
    # ONLINE EXAM - QUESTION SELECTION
    # ==========================================================

    path(
        "question-selection/<int:exam_id>/",
        views.question_selection,
        name="performance_question_selection",
    ),

    # ==========================================================
    # ONLINE EXAM - PUBLISH
    # ==========================================================

    path(
        "exams/<int:exam_id>/publish/",
        views.publish_test,
        name="publish_test",
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

    path(
        "exams/<int:exam_id>/students/",
        views.exam_student_status,
        name="exam_student_status",
    ),

    # ==========================================================
    # EXAM PDFS
    # ==========================================================

    path(
        "exams/<int:exam_id>/test-pdf/",
        views.exam_test_pdf,
        name="exam_test_pdf",
    ),

    path(
        "exams/<int:exam_id>/answer-solution-pdf/",
        views.exam_answer_solution_pdf,
        name="exam_answer_solution_pdf",
    ),

    # ==========================================================
    # WORKSHEET GENERATOR
    # ==========================================================

    path(
        "worksheets/",
        views.worksheet_library,
        name="worksheet_library",
    ),

    path(
        "worksheets/create/",
        views.worksheet_create,
        name="worksheet_create",
    ),

]