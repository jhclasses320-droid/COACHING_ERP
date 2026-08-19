from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import datetime

from students.models import Student, Batch, Subject, Topic, Chapter, Exam, ExamQuestion, Question

from .models import (
    Assessment,
    AssessmentSubject,
    AssessmentType,
    StudentMark,
)


# ==========================================================
# ERP CREATE TEST
# ==========================================================

def create_test(request):

    assessment_types = AssessmentType.objects.filter(
        is_active=True
    ).order_by("display_order", "name")

    batches = Batch.objects.all().order_by("id")

    subjects = Subject.objects.all().order_by("name")

    topics = Topic.objects.all().order_by("name")

    chapters = Chapter.objects.filter(
        is_active=True
    ).order_by("name")

    if request.method == "POST":

        test_mode = request.POST.get("test_mode")

        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        if test_mode == "online":

            if not start_time or not end_time:
                messages.error(
                    request,
                    "Start Date & Time and End Date & Time are required for an Online Test."
                )
                return redirect("performance_create_test")

            if not request.POST.get("topic"):
                messages.error(
                    request,
                    "Topic is required for an Online Test."
                )
                return redirect("performance_create_test")

            start_time = timezone.make_aware(
                datetime.fromisoformat(start_time)
            )

            end_time = timezone.make_aware(
                datetime.fromisoformat(end_time)
            )

            if end_time <= start_time:
                messages.error(
                    request,
                    "End Date & Time must be after Start Date & Time."
                )
                return redirect("performance_create_test")

        assessment = Assessment.objects.create(
            assessment_name=request.POST.get("assessment_name"),
            assessment_type_id=request.POST.get("assessment_type"),
            academic_session=request.POST.get("academic_session"),
            batch_id=request.POST.get("batch"),
            assessment_date=request.POST.get("assessment_date"),
            created_by=request.user,
        )

        assessment_subject = AssessmentSubject.objects.create(
            assessment=assessment,
            subject_id=request.POST.get("subject"),
            topic_id=request.POST.get("topic") or None,
            chapter_covered=request.POST.get("chapter_covered", ""),
            maximum_marks=request.POST.get("maximum_marks"),
            duration_minutes=request.POST.get("duration_minutes"),
        )

        chapter_ids = request.POST.getlist("chapters")

        if chapter_ids:
            assessment_subject.chapters.set(chapter_ids)

        if test_mode == "online":

            exam = Exam.objects.create(
                name=assessment.assessment_name,
                assessment=assessment,
                topic_id=request.POST.get("topic"),
                batch=assessment.batch,
                duration=assessment_subject.duration_minutes,
                total_marks=assessment_subject.maximum_marks,
                start_time=start_time,
                end_time=end_time,
            )

        messages.success(
            request,
            "Test created successfully."
        )

        if test_mode == "online":
            return redirect(
                "performance_question_selection",
                exam_id=exam.id,
            )

        return redirect("performance_create_test")

    context = {
        "assessment_types": assessment_types,
        "batches": batches,
        "subjects": subjects,
        "topics": topics,
        "chapters": chapters,
        "academic_sessions": Assessment.ACADEMIC_SESSION_CHOICES,
    }

    return render(
        request,
        "performance/create_test.html",
        context,
    )
# ==========================================================
# MARKS ENTRY
# ==========================================================

def marks_entry(request):

    assessment_subjects = AssessmentSubject.objects.select_related(
        "assessment",
        "subject",
        "assessment__batch",
    ).all()

    selected_subject = None
    students = []
    existing_marks = {}

    assessment_subject_id = (
        request.GET.get("assessment_subject")
        or request.POST.get("assessment_subject")
    )

    if assessment_subject_id:

        selected_subject = get_object_or_404(
            AssessmentSubject,
            id=assessment_subject_id,
        )

        students = list(
    Student.objects.filter(
        Q(batch=selected_subject.assessment.batch) |
        Q(additional_batches=selected_subject.assessment.batch),
        is_active=True,
    )
    .distinct()
    .order_by("student_name")
    )

        saved_marks = StudentMark.objects.filter(
            assessment_subject=selected_subject
        )

        existing_marks = {
            mark.student_id: mark
            for mark in saved_marks
        }

        if request.method == "POST":

            for student in students:

                marks_value = request.POST.get(
                    f"marks_{student.id}"
                )

                is_absent = (
                    request.POST.get(
                        f"absent_{student.id}"
                    ) == "on"
                )

                if is_absent:
                    marks_value = None

                if marks_value not in ("", None) or is_absent:

                    StudentMark.objects.update_or_create(
                        assessment_subject=selected_subject,
                        student=student,
                        defaults={
                            "marks_scored": marks_value,
                            "is_absent": is_absent,
                        },
                    )

            messages.success(
                request,
                "Marks saved successfully.",
            )

            return redirect(
                f"{request.path}?assessment_subject={selected_subject.id}"
            )

        for student in students:
            student.saved_mark = existing_marks.get(student.id)

    context = {
        "assessment_subjects": assessment_subjects,
        "selected_subject": selected_subject,
        "students": students,
    }

    return render(
        request,
        "performance/marks_entry.html",
        context,
    )


# ==========================================================
# REPORTS HOME
# ==========================================================

def performance_reports(request):

    return render(
        request,
        "performance/reports.html",
    )


# ==========================================================
# STUDENT PERFORMANCE REPORT
# ==========================================================

def student_performance_report(request):

    batches = Batch.objects.all().order_by("batch_name")

    students = Student.objects.filter(
        is_active=True
    ).order_by("student_name")

    selected_batch = request.GET.get("batch")
    selected_student = request.GET.get("student")
    selected_session = request.GET.get("session")

    report_rows = []

    total_maximum = 0
    total_obtained = 0
    total_present = 0
    total_absent = 0

    if selected_batch:
        students = students.filter(
            batches__id=selected_batch
        ).distinct()

    if selected_student:

        marks = StudentMark.objects.select_related(
            "assessment_subject",
            "assessment_subject__assessment",
            "assessment_subject__subject",
            "student",
        ).filter(
            student_id=selected_student
        )

        if selected_session:
            marks = marks.filter(
                assessment_subject__assessment__academic_session=selected_session
            )

        marks = marks.order_by(
            "-assessment_subject__assessment__assessment_date",
            "assessment_subject__subject__name",
        )

        for mark in marks:

            maximum = mark.assessment_subject.maximum_marks
            obtained = mark.marks_scored or 0

            percentage = 0

            if not mark.is_absent and maximum > 0:
                percentage = round(
                    (obtained / maximum) * 100,
                    2,
                )

            report_rows.append(
                {
                    "assessment": mark.assessment_subject.assessment.assessment_name,
                    "subject": mark.assessment_subject.subject.name,
                    "date": mark.assessment_subject.assessment.assessment_date,
                    "maximum": maximum,
                    "obtained": obtained,
                    "percentage": percentage,
                    "status": "Absent" if mark.is_absent else "Present",
                }
            )

            total_maximum += maximum

            if not mark.is_absent:
                total_obtained += obtained
                total_present += 1
            else:
                total_absent += 1

    overall_percentage = 0

    if total_maximum:
        overall_percentage = round(
            (total_obtained / total_maximum) * 100,
            2,
        )

    context = {
        "batches": batches,
        "students": students,
        "selected_batch": selected_batch,
        "selected_student": selected_student,
        "selected_session": selected_session,
        "report_rows": report_rows,
        "total_maximum": total_maximum,
        "total_obtained": total_obtained,
        "overall_percentage": overall_percentage,
        "total_present": total_present,
        "total_absent": total_absent,
    }

    return render(
        request,
        "performance/student_performance_report.html",
        context,
    )
# ==========================================================
# ASSESSMENT REPORT
# ==========================================================

def assessment_report(request, assessment_subject_id):

    assessment_subject = get_object_or_404(
        AssessmentSubject.objects.select_related(
            "assessment",
            "assessment__assessment_type",
            "assessment__batch",
            "subject",
        ),
        id=assessment_subject_id,
    )

    marks = list(
        StudentMark.objects.select_related(
            "student"
        ).filter(
            assessment_subject=assessment_subject
        )
    )

    # Present students only
    present_marks = [
        m for m in marks
        if not m.is_absent
    ]

    present_marks.sort(
        key=lambda x: x.marks_scored,
        reverse=True,
    )

    # Competition Ranking
    rank_map = {}

    previous_score = None
    current_rank = 0

    for index, mark in enumerate(
        present_marks,
        start=1,
    ):

        if previous_score != mark.marks_scored:
            current_rank = index

        rank_map[mark.student_id] = current_rank
        previous_score = mark.marks_scored

    rows = []

    for mark in marks:

        rows.append(
            {
                "rank": "-" if mark.is_absent else rank_map[mark.student_id],
                "student_id": mark.student.student_id,
                "student_name": mark.student.student_name,
                "marks_obtained": "AB" if mark.is_absent else mark.marks_scored,
                "maximum_marks": assessment_subject.maximum_marks,
                "sort_marks": -1 if mark.is_absent else float(mark.marks_scored),
                "is_absent": mark.is_absent,
            }
        )

    rows.sort(
        key=lambda x: x["sort_marks"],
        reverse=True,
    )

    present = len(present_marks)
    absent = len(marks) - present

    highest = (
        max(float(x.marks_scored) for x in present_marks)
        if present_marks else 0
    )

    lowest = (
        min(float(x.marks_scored) for x in present_marks)
        if present_marks else 0
    )

    average = (
        round(
            sum(float(x.marks_scored) for x in present_marks) / present,
            2,
        )
        if present else 0
    )

    context = {
        "assessment_subject": assessment_subject,
        "rows": rows,
        "total_students": len(marks),
        "present": present,
        "absent": absent,
        "highest": highest,
        "lowest": lowest,
        "average": average,
        "generated_on": timezone.now(),
    }

    return render(
        request,
        "performance/assessment_report.html",
        context,
    )


# ==========================================================
# BATCH PERFORMANCE REPORT
# ==========================================================

def batch_performance_report(request):

    return render(
        request,
        "performance/batch_performance_report.html",
    )


# ==========================================================
# SUBJECT ANALYSIS REPORT
# ==========================================================

def subject_analysis_report(request):

    return render(
        request,
        "performance/subject_analysis_report.html",
    )


# ==========================================================
# PARENT REPORT
# ==========================================================

def parent_report(request):

    return render(
        request,
        "performance/parent_report.html",
    )



# ==========================================================
# ONLINE EXAM - QUESTION SELECTION
# ==========================================================




    

    # ==========================================================
# ONLINE EXAM - QUESTION SELECTION
# ==========================================================

def question_selection(request, exam_id):

    exam = get_object_or_404(
        Exam.objects.select_related(
            "batch",
            "topic",
            "topic__subject",
        ),
        id=exam_id,
    )

    # ------------------------------------------------------
    # FILTER VALUES
    # ------------------------------------------------------

    difficulty = request.GET.get(
        "difficulty",
        ""
    ).strip()

    question_type = request.GET.get(
        "question_type",
        ""
    ).strip()

    question_mode = request.GET.get(
        "question_mode",
        ""
    ).strip()

    marks = request.GET.get(
        "marks",
        ""
    ).strip()

    source = request.GET.get(
        "source",
        ""
    ).strip()

    search = request.GET.get(
        "search",
        ""
    ).strip()

    # ------------------------------------------------------
    # BASE QUESTIONS
    # Exam Batch + Topic remain the fixed boundary
    # ------------------------------------------------------

    questions = Question.objects.filter(
        batch=exam.batch,
        topic=exam.topic,
        is_active=True,
    ).order_by("id")

    # ------------------------------------------------------
    # APPLY FILTERS
    # ------------------------------------------------------

    if difficulty:

        questions = questions.filter(
            difficulty=difficulty
        )

    if question_type:

        questions = questions.filter(
            question_type=question_type
        )

    if question_mode:

        questions = questions.filter(
            question_mode=question_mode
        )

    if marks:

        questions = questions.filter(
            marks=marks
        )

    if source:

        questions = questions.filter(
            source=source
        )

    if search:

        questions = questions.filter(
            Q(question_text__icontains=search)
            |
            Q(feedback_text__icontains=search)
        )

    # ------------------------------------------------------
    # ALREADY SELECTED QUESTIONS
    # ------------------------------------------------------

    selected_question_ids = set(
        ExamQuestion.objects.filter(
            exam=exam
        ).values_list(
            "question_id",
            flat=True,
        )
    )

    # ------------------------------------------------------
    # SAVE SELECTED QUESTIONS
    # ------------------------------------------------------

    if request.method == "POST":

        selected_ids = request.POST.getlist(
            "questions"
        )

        ExamQuestion.objects.filter(
            exam=exam
        ).delete()

        selected_questions = Question.objects.filter(
            id__in=selected_ids,
            batch=exam.batch,
            topic=exam.topic,
            is_active=True,
        )

        for question in selected_questions:

            ExamQuestion.objects.create(
                exam=exam,
                question=question,
            )

        exam.number_of_questions = (
            selected_questions.count()
        )

        exam.save(
            update_fields=[
                "number_of_questions"
            ]
        )

        messages.success(
            request,
            "Questions selected successfully.",
        )

        return redirect(
            "performance_question_selection",
            exam_id=exam.id,
        )

    # ------------------------------------------------------
    # PAGE CONTEXT
    # ------------------------------------------------------

    context = {

        "exam": exam,

        "questions": questions,

        "selected_question_ids":
            selected_question_ids,

        "difficulty_choices":
            Question.DIFFICULTY_CHOICES,

        "question_type_choices":
            Question.QUESTION_TYPE_CHOICES,

        "question_mode_choices":
            Question.QUESTION_MODE_CHOICES,

        "source_choices":
            Question.SOURCE_CHOICES,

        "selected_difficulty":
            difficulty,

        "selected_question_type":
            question_type,

        "selected_question_mode":
            question_mode,

        "selected_marks":
            marks,

        "selected_source":
            source,

        "search":
            search,
    }

    return render(
        request,
        "performance/question_selection.html",
        context,
    )

    