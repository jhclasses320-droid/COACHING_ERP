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
    WorksheetProject,
    WorksheetSet,
    Worksheet,
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

                is_retest = (
                    request.POST.get(
                        f"retest_{student.id}"
                    ) == "on"
                )

                if is_absent or is_retest:
                    marks_value = None

                if (
                    marks_value not in ("", None)
                    or is_absent
                    or is_retest
                ):

                    StudentMark.objects.update_or_create(
                        assessment_subject=selected_subject,
                        student=student,
                        defaults={
                            "marks_scored": marks_value,
                            "is_absent": is_absent,
                            "is_retest": is_retest,
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

    selected_batch_id = request.GET.get("batch")
    selected_student_id = request.GET.get("student")
    selected_session = request.GET.get("session")

    selected_batch = None
    selected_student = None

    report_rows = []

    total_maximum = 0
    total_obtained = 0
    total_present = 0
    total_absent = 0

    # ------------------------------------------------------
    # SELECTED BATCH
    # ------------------------------------------------------

    if selected_batch_id:

        selected_batch = get_object_or_404(
            Batch,
            id=selected_batch_id
        )

        students = students.filter(
            Q(batch=selected_batch) |
            Q(additional_batches=selected_batch)
        ).distinct()

    # ------------------------------------------------------
    # SELECTED STUDENT
    # ------------------------------------------------------

    if selected_student_id:

        selected_student = get_object_or_404(
            Student,
            id=selected_student_id,
            is_active=True,
        )

        marks = StudentMark.objects.select_related(
            "assessment_subject",
            "assessment_subject__assessment",
            "assessment_subject__subject",
            "student",
        ).filter(
            student=selected_student
        )

        # --------------------------------------------------
        # ACADEMIC SESSION FILTER
        # --------------------------------------------------

        if selected_session:

            marks = marks.filter(
                assessment_subject__assessment__academic_session=
                selected_session
            )

        # --------------------------------------------------
        # ORDER
        # --------------------------------------------------

        marks = marks.order_by(
            "-assessment_subject__assessment__assessment_date",
            "assessment_subject__subject__name",
        )

        # --------------------------------------------------
        # BUILD REPORT
        # --------------------------------------------------

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
                    "assessment":
                        mark.assessment_subject.assessment.assessment_name,

                    "subject":
                        mark.assessment_subject.subject.name,

                    "date":
                        mark.assessment_subject.assessment.assessment_date,

                    "maximum":
                        maximum,

                    "obtained":
                        obtained,

                    "percentage":
                        percentage,

                    "status":
                        "Absent" if mark.is_absent else "Present",
                }
            )

            # --------------------------------------------------
            # TOTALS
            # --------------------------------------------------

            total_maximum += maximum

            if not mark.is_absent:

                total_obtained += obtained
                total_present += 1

            else:

                total_absent += 1

    # ------------------------------------------------------
    # OVERALL PERCENTAGE
    # ------------------------------------------------------

    overall_percentage = 0

    if total_maximum:

        overall_percentage = round(
            (total_obtained / total_maximum) * 100,
            2,
        )

    # ------------------------------------------------------
    # CONTEXT
    # ------------------------------------------------------

    context = {

        "batches":
            batches,

        "students":
            students,

        "selected_batch":
            selected_batch,

        "selected_student":
            selected_student,

        "selected_session":
            selected_session,

        "report_rows":
            report_rows,

        "total_maximum":
            total_maximum,

        "total_obtained":
            total_obtained,

        "overall_percentage":
            overall_percentage,

        "total_present":
            total_present,

        "total_absent":
            total_absent,
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

    # ------------------------------------------------------
    # STUDENTS WITH VALID MARKS
    # ------------------------------------------------------

    present_marks = [
        m for m in marks
        if not m.is_absent
        and not m.is_retest
        and m.marks_scored is not None
    ]

    present_marks.sort(
        key=lambda x: x.marks_scored,
        reverse=True,
    )

    # ------------------------------------------------------
    # COMPETITION RANKING
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # BUILD REPORT ROWS
    # ------------------------------------------------------

    rows = []

    for mark in marks:

        if mark.is_absent:

            rank = "-"
            marks_obtained = "AB"
            sort_marks = -1

        elif mark.is_retest:

            rank = "-"
            marks_obtained = "RT"
            sort_marks = -1

        elif mark.marks_scored is None:

            rank = "-"
            marks_obtained = "-"
            sort_marks = -1

        else:

            rank = rank_map.get(
                mark.student_id,
                "-"
            )

            marks_obtained = mark.marks_scored
            sort_marks = float(
                mark.marks_scored
            )

        rows.append(
            {
                "rank": rank,
                "student_id": mark.student.student_id,
                "student_name": mark.student.student_name,
                "marks_obtained": marks_obtained,
                "maximum_marks": assessment_subject.maximum_marks,
                "sort_marks": sort_marks,
                "is_absent": mark.is_absent,
            }
        )

    # ------------------------------------------------------
    # SORT
    # ------------------------------------------------------

    rows.sort(
        key=lambda x: x["sort_marks"],
        reverse=True,
    )

    # ------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------

    present = len(present_marks)

    absent = sum(
        1
        for mark in marks
        if mark.is_absent
    )

    highest = (
        max(
            float(mark.marks_scored)
            for mark in present_marks
        )
        if present_marks
        else 0
    )

    lowest = (
        min(
            float(mark.marks_scored)
            for mark in present_marks
        )
        if present_marks
        else 0
    )

    average = (
        round(
            sum(
                float(mark.marks_scored)
                for mark in present_marks
            ) / present,
            2,
        )
        if present
        else 0
    )

    # ------------------------------------------------------
    # CONTEXT
    # ------------------------------------------------------

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

    # ==========================================================
# ONLINE EXAM - PUBLISH TEST
# ==========================================================

def publish_test(request, exam_id):

    exam = get_object_or_404(
        Exam,
        id=exam_id,
    )

    # ------------------------------------------------------
    # ALREADY PUBLISHED
    # ------------------------------------------------------

    if exam.status == "PUBLISHED":

        messages.warning(
            request,
            "This exam has already been published."
        )

        return redirect("performance_exam_library")


    # ------------------------------------------------------
    # VALIDATE EXAM BEFORE PUBLISHING
    # ------------------------------------------------------

    question_count = ExamQuestion.objects.filter(
        exam=exam
    ).count()

    if question_count == 0:

        messages.error(
            request,
            "This exam cannot be published because no questions have been added."
        )

        return redirect(
            "performance_question_selection",
            exam_id=exam.id,
        )


    if not exam.duration or exam.duration <= 0:

        messages.error(
            request,
            "A valid exam duration is required before publishing."
        )

        return redirect(
            "edit_test",
            exam.id,
        )


    if not exam.total_marks or exam.total_marks <= 0:

        messages.error(
            request,
            "Maximum marks must be greater than zero before publishing."
        )

        return redirect(
            "edit_test",
            exam.id,
        )


    # ------------------------------------------------------
    # PUBLISH
    # ------------------------------------------------------

    exam.status = "PUBLISHED"
    exam.published_at = timezone.now()

    exam.save(
        update_fields=[
            "status",
            "published_at",
        ]
    )

    messages.success(
        request,
        f"'{exam.name}' has been published successfully."
    )

    return redirect(
        "performance_exam_library"
    )

# ==========================================================
# ONLINE EXAM - ASSIGNED STUDENTS STATUS
# ==========================================================

def exam_student_status(request, exam_id):

    from students.models import Exam, ExamAssignment, StudentExamAttempt

    exam = Exam.objects.get(id=exam_id)

    assignments = ExamAssignment.objects.filter(
        exam=exam,
        is_active=True
    ).select_related("student")

    attempts = {
        attempt.student_id: attempt
        for attempt in StudentExamAttempt.objects.filter(
            exam=exam
        )
    }

    student_status = []

    for assignment in assignments:

        attempt = attempts.get(assignment.student_id)

        student_status.append({
            "student": assignment.student,
            "attempted": attempt is not None,
            "attempt": attempt,
        })

    total_assigned = len(assignments)
    total_attempted = sum(
        1 for item in student_status
        if item["attempted"]
    )
    total_pending = total_assigned - total_attempted

    return render(
        request,
        "performance/exam_student_status.html",
        {
            "exam": exam,
            "student_status": student_status,
            "total_assigned": total_assigned,
            "total_attempted": total_attempted,
            "total_pending": total_pending,
        }
    )

# ==========================================================
# WORKSHEET LIBRARY
# ==========================================================

def worksheet_library(request):

    worksheet_projects = (
        WorksheetProject.objects
        .select_related(
            "subject",
            "chapter",
            "created_by",
        )
        .prefetch_related(
            "worksheet_sets",
        )
        .filter(is_active=True)
        .order_by("-created_on")
    )

    return render(
        request,
        "performance/worksheet_library.html",
        {
            "worksheet_projects": worksheet_projects,
        },
    )


# ==========================================================
# CREATE WORKSHEET PROJECT
# ==========================================================

def worksheet_create(request):

    batches = Batch.objects.all().order_by(
        "student_class",
        "batch_name",
    )

    subjects = Subject.objects.all().order_by(
        "name"
    )

    chapters = Chapter.objects.filter(
        is_active=True
    ).select_related(
        "topic",
        "topic__subject",
    ).order_by(
        "topic__subject__name",
        "topic__name",
        "name",
    )

    if request.method == "POST":

        batch_id = request.POST.get("batch")
        subject_id = request.POST.get("subject")
        chapter_id = request.POST.get("chapter")

        title = request.POST.get(
            "title"
        ).strip()

        number_of_sets = int(
            request.POST.get(
                "number_of_sets",
                1,
            )
        )

        if not title:

            messages.error(
                request,
                "Worksheet project title is required.",
            )

            return redirect(
                "worksheet_create"
            )

        if number_of_sets < 1:

            messages.error(
                request,
                "At least one worksheet set is required.",
            )

            return redirect(
                "worksheet_create"
            )

        batch = get_object_or_404(
            Batch,
            id=batch_id,
        )

        subject = get_object_or_404(
            Subject,
            id=subject_id,
        )

        chapter = None

        if chapter_id:

            chapter = get_object_or_404(
                Chapter,
                id=chapter_id,
                is_active=True,
            )

        project = WorksheetProject.objects.create(

            class_level=(
                batch.student_class
                or ""
            ),

            subject=subject,

            chapter=chapter,

            chapter_name=(
                chapter.name
                if chapter
                else ""
            ),

            title=title,

            number_of_sets=number_of_sets,

            worksheets_per_set=4,

            created_by=(
                request.user
                if request.user.is_authenticated
                else None
            ),
        )

        # --------------------------------------------------
        # CREATE THE REQUESTED NUMBER OF SETS
        # --------------------------------------------------

        for set_number in range(
            1,
            number_of_sets + 1,
        ):

            worksheet_set = WorksheetSet.objects.create(
                project=project,
                set_number=set_number,
            )

            # --------------------------------------------------
            # EVERY SET STARTS WITH 4 WORKSHEETS
            # --------------------------------------------------

            worksheet_types = [
                ("FOUNDATION", "Foundation"),
                ("CONCEPTUAL", "Conceptual"),
                ("APPLICATION", "Application"),
                ("HOTS", "HOTS / Comprehensive"),
            ]

            for worksheet_number, (
                worksheet_type,
                worksheet_title,
            ) in enumerate(
                worksheet_types,
                start=1,
            ):

                Worksheet.objects.create(
                    set=worksheet_set,
                    worksheet_number=worksheet_number,
                    title=(
                        f"{title} - "
                        f"Set {set_number} - "
                        f"Worksheet {worksheet_number}"
                    ),
                    worksheet_type=worksheet_type,
                )

        messages.success(
            request,
            (
                f"Worksheet project created successfully "
                f"with {number_of_sets * 4} worksheets."
            ),
        )

        return redirect(
            "worksheet_library"
        )

    return render(
        request,
        "performance/worksheet_create.html",
        {
            "batches": batches,
            "subjects": subjects,
            "chapters": chapters,
        },
    )