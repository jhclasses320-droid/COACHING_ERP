from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import datetime
import io
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)

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
                batch=assessment.batch,
                duration=assessment_subject.duration_minutes,
                total_marks=assessment_subject.maximum_marks,
                start_time=start_time,
                end_time=end_time,
                instructions=request.POST.get(
                    "instructions",
                    ""
                ).strip(),
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

# ==========================================================
# ONLINE EXAM - QUESTION SELECTION
# ==========================================================

def question_selection(request, exam_id):

    exam = get_object_or_404(
        Exam.objects.select_related(
            "batch",
            "assessment",
        ),
        id=exam_id,
    )

    # ------------------------------------------------------
    # GET SUBJECT FROM THE ASSESSMENT
    # ------------------------------------------------------

    assessment_subject = get_object_or_404(
        AssessmentSubject.objects.select_related(
            "subject",
        ),
        assessment=exam.assessment,
    )

    subject = assessment_subject.subject

    # ------------------------------------------------------
    # FILTER VALUES
    # ------------------------------------------------------

    topic = request.GET.get(
        "topic",
        ""
    ).strip()

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
    # ------------------------------------------------------
    # BASE QUESTION BANK
    #
    # Restrict the question pool to the topic(s) belonging
    # to the chapter(s) selected for this assessment.
    #
    # The requested number of questions must NEVER expand
    # the question pool beyond the selected chapter(s).
    # ------------------------------------------------------

    selected_chapters = assessment_subject.chapters.all()

    if selected_chapters.exists():

        selected_topic_ids = selected_chapters.values_list(
            "topic_id",
            flat=True,
        )

        questions = Question.objects.filter(
            batch=exam.batch,
            topic__subject=subject,
            topic_id__in=selected_topic_ids,
            is_active=True,
        ).select_related(
            "topic",
        ).order_by("id")

    else:

        questions = Question.objects.filter(
            batch=exam.batch,
            topic__subject=subject,
            is_active=True,
        ).select_related(
            "topic",
        ).order_by("id")

    # ------------------------------------------------------
    # TOPIC FILTER
    # ------------------------------------------------------

    if topic:

        questions = questions.filter(
            topic_id=topic
        )

    # ------------------------------------------------------
    # DIFFICULTY
    # ------------------------------------------------------

    if difficulty:

        questions = questions.filter(
            difficulty=difficulty
        )

    # ------------------------------------------------------
    # QUESTION TYPE
    # ------------------------------------------------------

    if question_type:

        questions = questions.filter(
            question_type=question_type
        )

    # ------------------------------------------------------
    # QUESTION MODE
    # ------------------------------------------------------

    if question_mode:

        questions = questions.filter(
            question_mode=question_mode
        )

    # ------------------------------------------------------
    # MARKS
    # ------------------------------------------------------

    if marks:

        questions = questions.filter(
            marks=marks
        )

    # ------------------------------------------------------
    # SOURCE
    # ------------------------------------------------------

    if source:

        questions = questions.filter(
            source=source
        )

    # ------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------

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

        selected_questions = Question.objects.filter(
            id__in=selected_ids,
            batch=exam.batch,
            topic__subject=subject,
            is_active=True,
        )

        ExamQuestion.objects.filter(
            exam=exam
        ).delete()

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

        # TOPICS AVAILABLE FOR THIS SUBJECT
    # ------------------------------------------------------

    topics = Topic.objects.filter(
        subject=subject
    ).order_by(
        "name"
    )

    # ------------------------------------------------------
    # PAGE CONTEXT
    # ------------------------------------------------------

    context = {

        "exam":
            exam,

        "subject":
            subject,

        "topics":
            topics,

        "questions":
            questions,

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

        "selected_topic":
            topic,

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
# ONLINE EXAM - PREVIEW TEST
# ==========================================================

def preview_test(request, exam_id):

    exam = get_object_or_404(
        Exam.objects.select_related(
            "batch",
            "topic",
            "topic__subject",
        ),
        id=exam_id,
    )

    exam_questions = (
        ExamQuestion.objects
        .filter(exam=exam)
        .select_related("question")
        .order_by("id")
    )

    return render(
        request,
        "performance/exam_preview.html",
        {
            "exam": exam,
            "questions": exam_questions,
        },
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

        return redirect("exam_library")


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
             "exam_library"
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
# ==========================================================
# EXAM PDF - FONT SETUP
# ==========================================================

def _register_exam_pdf_font():

    font_candidates = [
        r"C:\Windows\Fonts\times.ttf",
        r"C:\Windows\Fonts\timesnr.ttf",
        r"C:\Windows\Fonts\Times New Roman.ttf",
    ]

    for font_path in font_candidates:

        if os.path.exists(font_path):

            try:

                pdfmetrics.registerFont(
                    TTFont(
                        "ExamTimesNewRoman",
                        font_path,
                    )
                )

                return "ExamTimesNewRoman"

            except Exception:
                pass

    return "Helvetica"


# ==========================================================
# EXAM PDF - IMAGE HELPER
# ==========================================================

def _exam_pdf_image(image_field, max_width=160 * mm):

    if not image_field:
        return None

    try:

        image_path = image_field.path

        if not os.path.exists(image_path):
            return None

        image = Image(image_path)

        original_width = image.imageWidth
        original_height = image.imageHeight

        if not original_width or not original_height:
            return None

        scale = min(
            max_width / original_width,
            1,
        )

        image.drawWidth = original_width * scale
        image.drawHeight = original_height * scale

        return image

    except Exception:
        return None


# ==========================================================
# EXAM PDF - COMMON DATA
# ==========================================================

def _get_exam_pdf_data(exam_id):

    exam = get_object_or_404(
        Exam.objects.select_related(
            "batch",
            "assessment",
        ),
        id=exam_id,
    )

    assessment_subject = get_object_or_404(
        AssessmentSubject.objects.select_related(
            "subject",
        ),
        assessment=exam.assessment,
    )

    exam_questions = (
        ExamQuestion.objects
        .filter(exam=exam)
        .select_related(
            "question",
        )
        .order_by("id")
    )

    return exam, assessment_subject.subject, exam_questions


# ==========================================================
# EXAM PDF - COMMON STYLES
# ==========================================================

def _exam_pdf_styles():

    font_name = _register_exam_pdf_font()

    styles = getSampleStyleSheet()

    return {
        "font": font_name,

        "school": ParagraphStyle(
            "ExamSchool",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=5 * mm,
        ),

        "title": ParagraphStyle(
            "ExamTitle",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=3 * mm,
        ),

        "details": ParagraphStyle(
            "ExamDetails",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=2 * mm,
        ),

        "heading": ParagraphStyle(
            "ExamHeading",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=15,
            leading=19,
            spaceBefore=4 * mm,
            spaceAfter=3 * mm,
        ),

        "body": ParagraphStyle(
            "ExamBody",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=14,
            leading=19,
            spaceAfter=3 * mm,
        ),

        "option": ParagraphStyle(
            "ExamOption",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=14,
            leading=19,
            leftIndent=7 * mm,
            spaceAfter=2 * mm,
        ),

        "solution": ParagraphStyle(
            "ExamSolution",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=14,
            leading=19,
            leftIndent=5 * mm,
            spaceAfter=3 * mm,
        ),
    }


# ==========================================================
# EXAM PDF - TEST PAPER
# NO ANSWERS / NO SOLUTIONS
# ==========================================================

def exam_test_pdf(request, exam_id):

    exam, subject, exam_questions = _get_exam_pdf_data(
    exam_id
)

    styles = _exam_pdf_styles()

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"{exam.name} - Test Paper",
        author="JH Classes",
    )

    story = []

    # ------------------------------------------------------
    # HEADER
    # ------------------------------------------------------

    story.append(
        Paragraph(
            "JH CLASSES",
            styles["school"],
        )
    )

    story.append(
        Paragraph(
            exam.name,
            styles["title"],
        )
    )

    story.append(
        Paragraph(
            f"Class: {exam.batch.student_class or exam.batch.batch_name}",
            styles["details"],
        )
    )

    story.append(
        Paragraph(
           f"Subject: {subject.name}", 
            styles["details"],
        )
    )

    story.append(
        Paragraph(
            f"Time: {exam.duration} Minutes"
            f" &nbsp;&nbsp;&nbsp; "
            f"Maximum Marks: {exam.total_marks}",
            styles["details"],
        )
    )

    story.append(Spacer(1, 4 * mm))

    # ------------------------------------------------------
    # STUDENT DETAILS
    # ------------------------------------------------------

    student_table = Table(
        [
            [
                Paragraph(
                    "Name: ______________________________",
                    styles["body"],
                ),
                Paragraph(
                    "Roll No.: __________________",
                    styles["body"],
                ),
            ],
            [
                Paragraph(
                    "Date: _______________________________",
                    styles["body"],
                ),
                "",
            ],
        ],
        colWidths=[
            105 * mm,
            65 * mm,
        ],
    )

    student_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ]
        )
    )

    story.append(student_table)

    story.append(Spacer(1, 3 * mm))

    # ------------------------------------------------------
    # INSTRUCTIONS
    # ------------------------------------------------------

    if exam.instructions.strip():

        story.append(
            Paragraph(
                "INSTRUCTIONS",
                styles["heading"],
            )
        )

        instruction_lines = (
            exam.instructions
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .split("\n")
        )

        for line in instruction_lines:

            if line.strip():

                story.append(
                    Paragraph(
                        line.strip(),
                        styles["body"],
                    )
                )

        story.append(
            Spacer(
                1,
                3 * mm,
            )
        )

    # ------------------------------------------------------
    # QUESTIONS
    # ------------------------------------------------------

    for number, exam_question in enumerate(
        exam_questions,
        start=1,
    ):

        question = exam_question.question

        question_text = (
            question.question_text
            or " "
        )

        story.append(
            Paragraph(
                f"<b>Q{number}.</b> {question_text}",
                styles["body"],
            )
        )

        question_image = _exam_pdf_image(
            question.question_image
        )

        if question_image:

            story.append(
                question_image
            )

            story.append(
                Spacer(
                    1,
                    3 * mm,
                )
            )

        options = [
            (
                "A",
                question.option_a_text,
                question.option_a_image,
            ),
            (
                "B",
                question.option_b_text,
                question.option_b_image,
            ),
            (
                "C",
                question.option_c_text,
                question.option_c_image,
            ),
            (
                "D",
                question.option_d_text,
                question.option_d_image,
            ),
        ]

        for label, text, image_field in options:

            if not text and not image_field:
                continue

            option_text = (
                text
                or ""
            )

            story.append(
                Paragraph(
                    f"<b>{label}.</b> {option_text}",
                    styles["option"],
                )
            )

            option_image = _exam_pdf_image(
                image_field,
                max_width=145 * mm,
            )

            if option_image:

                story.append(
                    option_image
                )

                story.append(
                    Spacer(
                        1,
                        2 * mm,
                    )
                )

        story.append(
            Spacer(
                1,
                4 * mm,
            )
        )

    # ------------------------------------------------------
    # BUILD PDF
    # ------------------------------------------------------

    document.build(story)

    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/pdf",
    )

    response[
        "Content-Disposition"
    ] = (
        f'inline; filename="{exam.name} - Test Paper.pdf"'
    )

    return response


# ==========================================================
# EXAM PDF - ANSWER KEY + SOLUTIONS
# ==========================================================

def exam_answer_solution_pdf(request, exam_id):

    exam, subject, exam_questions = _get_exam_pdf_data(
    exam_id
)

    styles = _exam_pdf_styles()

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"{exam.name} - Answer Key and Solutions",
        author="JH Classes",
    )

    story = []

    # ------------------------------------------------------
    # HEADER
    # ------------------------------------------------------

    story.append(
        Paragraph(
            "JH CLASSES",
            styles["school"],
        )
    )

    story.append(
        Paragraph(
            f"{exam.name} - ANSWER KEY & SOLUTIONS",
            styles["title"],
        )
    )

    story.append(
        Paragraph(
            f"Class: {exam.batch.student_class or exam.batch.batch_name}",
            styles["details"],
        )
    )

    story.append(
        Paragraph(
            f"Subject: {subject.name}",
            styles["details"],
        )
    )

    story.append(
        Paragraph(
            f"Time: {exam.duration} Minutes"
            f" &nbsp;&nbsp;&nbsp; "
            f"Maximum Marks: {exam.total_marks}",
            styles["details"],
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    # ------------------------------------------------------
    # INSTRUCTIONS
    # ------------------------------------------------------

    if exam.instructions.strip():

        story.append(
            Paragraph(
                "INSTRUCTIONS",
                styles["heading"],
            )
        )

        instruction_lines = (
            exam.instructions
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .split("\n")
        )

        for line in instruction_lines:

            if line.strip():

                story.append(
                    Paragraph(
                        line.strip(),
                        styles["body"],
                    )
                )

        story.append(
            Spacer(
                1,
                3 * mm,
            )
        )

    # ------------------------------------------------------
    # QUESTIONS + ANSWERS + SOLUTIONS
    # ------------------------------------------------------

    for number, exam_question in enumerate(
        exam_questions,
        start=1,
    ):

        question = exam_question.question

        question_text = (
            question.question_text
            or " "
        )

        story.append(
            Paragraph(
                f"<b>Q{number}.</b> {question_text}",
                styles["body"],
            )
        )

        question_image = _exam_pdf_image(
            question.question_image
        )

        if question_image:

            story.append(
                question_image
            )

            story.append(
                Spacer(
                    1,
                    3 * mm,
                )
            )

        options = [
            (
                "A",
                question.option_a_text,
                question.option_a_image,
            ),
            (
                "B",
                question.option_b_text,
                question.option_b_image,
            ),
            (
                "C",
                question.option_c_text,
                question.option_c_image,
            ),
            (
                "D",
                question.option_d_text,
                question.option_d_image,
            ),
        ]

        for label, text, image_field in options:

            if not text and not image_field:
                continue

            option_text = (
                text
                or ""
            )

            story.append(
                Paragraph(
                    f"<b>{label}.</b> {option_text}",
                    styles["option"],
                )
            )

            option_image = _exam_pdf_image(
                image_field,
                max_width=145 * mm,
            )

            if option_image:

                story.append(
                    option_image
                )

                story.append(
                    Spacer(
                        1,
                        2 * mm,
                    )
                )

        # --------------------------------------------------
        # CORRECT ANSWER
        # --------------------------------------------------

        correct_option = (
            question.correct_option
            or "-"
        )

        story.append(
            Paragraph(
                f"<b>Correct Answer: {correct_option}</b>",
                styles["solution"],
            )
        )

        # --------------------------------------------------
        # SOLUTION
        # --------------------------------------------------

        solution_text = (
            question.feedback_text
            or ""
        ).strip()

        story.append(
            Paragraph(
                "<b>Solution:</b>",
                styles["solution"],
            )
        )

        if solution_text:

            solution_lines = (
                solution_text
                .replace("\r\n", "\n")
                .replace("\r", "\n")
                .split("\n")
            )

            for line in solution_lines:

                if line.strip():

                    story.append(
                        Paragraph(
                            line.strip(),
                            styles["solution"],
                        )
                    )

        else:

            story.append(
                Paragraph(
                    "No solution has been entered for this question.",
                    styles["solution"],
                )
            )

        # --------------------------------------------------
        # SOLUTION IMAGE
        # --------------------------------------------------

        solution_image = _exam_pdf_image(
            question.feedback_image,
            max_width=160 * mm,
        )

        if solution_image:

            story.append(
                solution_image
            )

            story.append(
                Spacer(
                    1,
                    3 * mm,
                )
            )

        story.append(
            Spacer(
                1,
                5 * mm,
            )
        )

    # ------------------------------------------------------
    # BUILD PDF
    # ------------------------------------------------------

    document.build(story)

    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/pdf",
    )

    response[
        "Content-Disposition"
    ] = (
        f'inline; filename="{exam.name} - Answer Key and Solutions.pdf"'
    )

    return response