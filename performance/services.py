from decimal import Decimal

from students.models import Student
from .models import Assessment, StudentMark


# ==========================================================
# GET MARKS OF A STUDENT IN ONE ASSESSMENT
# ==========================================================

def get_assessment_total(assessment, student):
    """
    Returns:
        subject_marks : {
            "Maths": Decimal(),
            "Science": Decimal(),
            ...
        }

        total_marks : Decimal
    """

    subject_marks = {}
    total_marks = Decimal("0")

    assessment_subjects = assessment.subjects.select_related(
        "subject"
    ).prefetch_related(
        "student_marks"
    )

    for assessment_subject in assessment_subjects:

        mark = assessment_subject.student_marks.filter(
            student=student
        ).first()

        if mark is None:
            obtained = Decimal("0")

        elif mark.is_absent:
            obtained = Decimal("0")

        elif mark.marks_scored is None:
            obtained = Decimal("0")

        else:
            obtained = Decimal(mark.marks_scored)

        subject_marks[
            assessment_subject.subject.name
        ] = obtained

        total_marks += obtained

    return subject_marks, total_marks


# ==========================================================
# BEST SCORE OF AN ASSESSMENT
# ==========================================================

def get_best_score(assessment):

    students = Student.objects.filter(
        batch=assessment.batch,
        is_active=True
    )

    highest = Decimal("0")

    for student in students:

        _, total = get_assessment_total(
            assessment,
            student
        )

        if total > highest:
            highest = total

    return highest
# ==========================================================
# POSITION OF A STUDENT IN AN ASSESSMENT
# ==========================================================

def calculate_position(assessment, student):
    """
    Returns:
        position_string : Example '2 / 28'
    """

    students = Student.objects.filter(
        batch=assessment.batch,
        is_active=True
    ).order_by("student_name")

    totals = []

    for batch_student in students:

        _, total = get_assessment_total(
            assessment,
            batch_student
        )

        totals.append({
            "student": batch_student,
            "total": total,
        })

    totals.sort(
        key=lambda x: x["total"],
        reverse=True
    )

    total_students = len(totals)

    for index, item in enumerate(totals, start=1):

        if item["student"].id == student.id:

            return f"{index} / {total_students}"

    return "-"


# ==========================================================
# COMPLETE STUDENT REPORT
# ==========================================================

def get_student_report(student, academic_session=None):
    """
    Returns a list like:

    [
        {
            "assessment": Assessment Object,
            "subject_marks": {...},
            "total": Decimal(),
            "position": "2 / 28",
            "best_score": Decimal(),
        }
    ]
    """

    assessments = Assessment.objects.filter(
        batch=student.batch,
        is_active=True
    ).prefetch_related(
        "subjects__subject",
        "subjects__student_marks"
    )

    if academic_session:
        assessments = assessments.filter(
            academic_session=academic_session
        )

    report = []

    for assessment in assessments:

        subject_marks, total = get_assessment_total(
            assessment,
            student
        )

        report.append({

            "assessment": assessment,

            "subject_marks": subject_marks,

            "total": total,

            "position": calculate_position(
                assessment,
                student
            ),

            "best_score": get_best_score(
                assessment
            ),

        })

    return report