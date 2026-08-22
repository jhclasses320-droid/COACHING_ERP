
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models
from django.http import HttpResponse
from datetime import date, datetime
from django.utils import timezone   

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import ExamForm

from .models import (
    Student,
    Exam,
    ExamQuestion,
    Question,
    FeePayment,
    Batch,
    AttendanceSession,
    AttendanceRecord,
    ExamAssignment,
    StudyMaterial,
)



from performance.models import (
    Assessment,
    AssessmentSubject,
    StudentMark
)


# ================= STUDENT LOGIN ================= #

from django.contrib.auth.hashers import make_password, check_password


def student_login(request):

    if request.method == "POST":

        student_id = request.POST.get("student_id")
        password = request.POST.get("password")

        try:

            student = Student.objects.get(
                student_id=student_id
            )

            if not student.is_active:

                messages.error(
                    request,
                    "Your account is inactive."
                )

                return redirect("student_login")


            # --------------------------------------------------
            # CHECK PASSWORD
            # --------------------------------------------------

            if not student.password or not check_password(
                password,
                student.password
            ):

                messages.error(
                    request,
                    "Invalid Student ID or Password."
                )

                return redirect("student_login")


            # --------------------------------------------------
            # CREATE STUDENT SESSION
            # --------------------------------------------------

            request.session["student_id"] = student.id


            # --------------------------------------------------
            # FORCE PASSWORD CHANGE
            # --------------------------------------------------

            if student.must_change_password:

                return redirect(
                    "student_change_password"
                )


            return redirect(
                "student_dashboard"
            )


        except Student.DoesNotExist:

            messages.error(
                request,
                "Invalid Student ID or Password."
            )


    return render(
        request,
        "students/login.html"
    )
# ================= CHANGE STUDENT PASSWORD ================= #

def student_change_password(request):

    student_id = request.session.get("student_id")

    if not student_id:
        return redirect("student_login")

    student = get_object_or_404(
        Student,
        id=student_id,
        is_active=True,
    )

    if request.method == "POST":

        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if not new_password or not confirm_password:
            messages.error(
                request,
                "Please enter and confirm your new password."
            )
            return redirect("student_change_password")

        if new_password != confirm_password:
            messages.error(
                request,
                "Passwords do not match."
            )
            return redirect("student_change_password")

        if len(new_password) < 4:
            messages.error(
                request,
                "Password must be at least 4 characters."
            )
            return redirect("student_change_password")

        student.password = make_password(new_password)
        student.must_change_password = False

        student.save(
            update_fields=[
                "password",
                "must_change_password",
            ]
        )

        messages.success(
            request,
            "Password changed successfully."
        )

        return redirect("student_dashboard")

    return render(
        request,
        "students/change_password.html"
    )

# ================= FORGOT STUDENT PASSWORD ================= #

def student_forgot_password(request):

    if request.method == "POST":

        student_id = request.POST.get("student_id")
        mobile = request.POST.get("mobile")

        try:

            student = Student.objects.get(
                student_id=student_id,
                student_mobile=mobile,
                is_active=True,
            )

        except Student.DoesNotExist:

            messages.error(
                request,
                "Student ID and Mobile Number do not match."
            )

            return redirect(
                "student_forgot_password"
            )

        request.session["password_reset_student_id"] = student.id

        return redirect(
            "student_reset_password"
        )

    return render(
        request,
        "students/forgot_password.html"
    )

# ================= RESET STUDENT PASSWORD ================= #

def student_reset_password(request):

    student_id = request.session.get(
        "password_reset_student_id"
    )

    if not student_id:
        return redirect("student_forgot_password")

    student = get_object_or_404(
        Student,
        id=student_id,
        is_active=True,
    )

    if request.method == "POST":

        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if not new_password or not confirm_password:

            messages.error(
                request,
                "Please enter and confirm your new password."
            )

            return redirect(
                "student_reset_password"
            )

        if new_password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect(
                "student_reset_password"
            )

        if len(new_password) < 4:

            messages.error(
                request,
                "Password must be at least 4 characters."
            )

            return redirect(
                "student_reset_password"
            )

        student.password = make_password(
            new_password
        )

        student.must_change_password = False

        student.save(
            update_fields=[
                "password",
                "must_change_password",
            ]
        )

        request.session.pop(
            "password_reset_student_id",
            None
        )

        messages.success(
            request,
            "Password reset successfully. You can now login."
        )

        return redirect(
            "student_login"
        )

    return render(
        request,
        "students/reset_password.html"
    )

# ================= STUDENT LOGOUT ================= #

def student_logout(request):

    request.session.flush()

    return redirect("student_login")


# ================= STUDENT DASHBOARD ================= #

def student_dashboard(request):

    student_id = request.session.get("student_id")

    if not student_id:
        return redirect("student_login")

    student = Student.objects.get(
        id=student_id
    )

      # ================= STUDY MATERIAL ================= #

    study_batches = [student.batch]

    if student.batch:
        batch_name = student.batch.batch_name

        if batch_name.endswith("_Maths_Science"):

            maths_batch = Batch.objects.filter(
                batch_name=batch_name.replace(
                    "_Maths_Science",
                    "_Maths"
                )
            ).first()

            science_batch = Batch.objects.filter(
                batch_name=batch_name.replace(
                    "_Maths_Science",
                    "_Science"
                )
            ).first()

            if maths_batch:
                study_batches.append(maths_batch)

            if science_batch:
                study_batches.append(science_batch)

    study_materials = StudyMaterial.objects.filter(
        batch__in=study_batches,
        is_active=True
    ).order_by(
        "subject",
        "title"
    )

    exams = Exam.objects.filter(
        batch=student.batch
    )

    attendance = AttendanceRecord.objects.filter(
        student=student
    )

    return render(
        request,
        "students/dashboard.html",
        {
            "student": student,
            "exams": exams,
            "attendance": attendance,
            "study_materials": study_materials
        }
    )  

# ================= REPORT PAGE ================= #

def reports_dashboard(request):
    return render(request, "admin/reports.html")


# ================= STUDENT PDF ================= #

def download_students_pdf(request):

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=students_report.pdf"

    doc = SimpleDocTemplate(response, pagesize=landscape(A4))
    elements = []

    data = [["Name", "Class", "School", "Mobile", "Fee"]]

    students = Student.objects.filter(is_active=True)

    for s in students:
        data.append([
            s.student_name,
            str(s.batch) if s.batch else "",
            str(s.school) if s.school else "",
            s.student_mobile or "",
            str(s.fee_amount or "")
        ])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.blue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    return response


# ================= FEE REPORT ================= #

def download_fee_report(request):

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=fee_report.pdf"

    doc = SimpleDocTemplate(response, pagesize=landscape(A4))
    elements = []

    data = [["Name", "Total Fee", "Paid", "Pending"]]

    students = Student.objects.filter(is_active=True)

    for s in students:

        total_fee = s.fee_amount or 0

        paid = FeePayment.objects.filter(student=s).aggregate(
            total=models.Sum("amount")
        )["total"] or 0

        pending = total_fee - paid

        data.append([
            s.student_name,
            str(total_fee),
            str(paid),
            str(pending)
        ])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.green),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    return response

# ================= DEFAULTER REPORT ================= #

def download_defaulter_report(request):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="defaulter_report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4))
    elements = []

    data = [['Name', 'Class', 'Mobile', 'Total Fee', 'Paid', 'Pending']]

    students = Student.objects.filter(is_active=True)

    for s in students:

        total_fee = s.fee_amount or 0

        paid = FeePayment.objects.filter(student=s).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        pending = total_fee - paid

        if pending > 0:
            data.append([
                s.student_name,
                str(s.batch) if s.batch else '',
                s.student_mobile or '',
                str(total_fee),
                str(paid),
                str(pending)
            ])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.red),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),1,colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    return response


# ================= ATTENDANCE ================= #

def mark_attendance(request, batch_id):

    today = date.today()
    batch = Batch.objects.get(id=batch_id)

    session, created = AttendanceSession.objects.get_or_create(
        batch=batch,
        date=today
    )

    students = Student.objects.filter(
        batch=batch,
        is_active=True
    ).order_by("student_name")

    if request.method == "POST":

        for student in students:

            status = request.POST.get(f"student_{student.id}", "A")

            AttendanceRecord.objects.update_or_create(
                session=session,
                student=student,
                defaults={"status": status}
            )

        messages.success(request, "Attendance saved successfully")

        return redirect("student_dashboard")

    return render(request, "attendance/mark.html", {
        "students": students,
        "batch": batch
    })


# ================= ATTENDANCE REPORT ================= #

def attendance_report(request):

    students = Student.objects.filter(is_active=True)
    report_data = []

    for s in students:

        total = AttendanceRecord.objects.filter(student=s).count()
        present = AttendanceRecord.objects.filter(student=s, status="P").count()

        percentage = (present / total * 100) if total > 0 else 0

        report_data.append({
            "student": s,
            "total": total,
            "present": present,
            "percentage": round(percentage,2)
        })

    return render(request, "attendance/report.html", {
        "report_data": report_data
    })


def attendance_batches(request):
    batches = Batch.objects.all()
    return render(request, "attendance/batches.html", {"batches": batches})


# ================= STUDENT EXAMS ================= #

def student_exam_list(request):

    student_id = request.session.get("student_id")

    if not student_id:
        return redirect("student_login")

    student = get_object_or_404(
        Student,
        id=student_id,
        is_active=True,
    )

    exams = Exam.objects.filter(
        assignments__student=student,
        assignments__is_active=True,
    ).distinct().order_by(
        "-id"
    )

    return render(
        request,
        "students/exam_list.html",
        {
            "exams": exams,
        }
    )

# ================= START EXAM ================= #

def start_exam(request, exam_id):

    student_id = request.session.get("student_id")

    if not student_id:
        return redirect("student_login")

    student = get_object_or_404(
        Student,
        id=student_id,
        is_active=True,
    )

    exam = get_object_or_404(
        Exam,
        id=exam_id,
    )

    # ------------------------------------------------------
    # VERIFY STUDENT IS ASSIGNED TO THIS EXAM
    # ------------------------------------------------------

    assignment_exists = ExamAssignment.objects.filter(
        exam=exam,
        student=student,
        is_active=True,
    ).exists()

    if not assignment_exists:

        messages.error(
            request,
            "This test has not been assigned to you."
        )

        return redirect(
            "student_exams"
        )


    questions = ExamQuestion.objects.filter(
        exam=exam
    ).select_related(
        "question"
    )


    # ------------------------------------------------------
    # SUBMIT EXAM
    # ------------------------------------------------------

    if request.method == "POST":

        attempt, created = (
            StudentExamAttempt.objects.get_or_create(
                student=student,
                exam=exam,
            )
        )

        # Prevent submitting the same completed exam again

        if attempt.completed:

            messages.info(
                request,
                "You have already completed this test."
            )

            return redirect(
                "student_exams"
            )


        score = 0


        # --------------------------------------------------
        # PROCESS EACH QUESTION
        # --------------------------------------------------

        for exam_question in questions:

            question = exam_question.question

            selected_option = request.POST.get(
                f"q{question.id}"
            )


            # Blank answer

            if not selected_option:

                continue


            # Check whether already answered

            StudentAnswer.objects.filter(
                attempt=attempt,
                question=question,
            ).delete()


            # --------------------------------------------------
            # CORRECT ANSWER
            # --------------------------------------------------

            if selected_option == question.correct_option:

                score += question.marks

                is_correct = True


            # --------------------------------------------------
            # WRONG ANSWER
            # --------------------------------------------------

            else:

                score -= question.negative_marks

                is_correct = False


            StudentAnswer.objects.create(

                attempt=attempt,

                question=question,

                selected_option=selected_option,

                is_correct=is_correct,

            )


        # --------------------------------------------------
        # SAVE ATTEMPT SCORE
        # --------------------------------------------------

        attempt.score = score

        attempt.completed = True

        attempt.end_time = timezone.now()

        attempt.save()


        # --------------------------------------------------
        # UPDATE PERFORMANCE MARK
        # --------------------------------------------------

        if exam.assessment:

            assessment_subject = (
                AssessmentSubject.objects.filter(
                    assessment=exam.assessment
                )
                .first()
            )


            if assessment_subject:

                StudentMark.objects.update_or_create(

                    assessment_subject=assessment_subject,

                    student=student,

                    defaults={
                        "marks_scored": score,
                        "is_absent": False,
                    },

                )


        messages.success(
            request,
            f"Test submitted successfully. Your score is {score}."
        )

        return redirect(
            "student_exams"
        )


    return render(
        request,
        "students/start_exam.html",
        {
            "exam": exam,
            "questions": questions,
        }
    )


# ================= STAFF LOGIN ================= #

def staff_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        print("Authenticated user:", user)

        if user is not None:
            print("Username:", user.username)
            print("Is Staff:", user.is_staff)
            print("Is Superuser:", user.is_superuser)

        if user is not None and user.is_staff:

            login(request, user)
            print("LOGIN SUCCESSFUL")

            return redirect("staff_dashboard")

        print("LOGIN FAILED")

        messages.error(request, "Invalid username or password")

    return render(request, "staff/login.html")


# ================= STAFF LOGOUT ================= #

def staff_logout(request):

    logout(request)

    return redirect("staff_login")


# ================= STAFF DASHBOARD ================= #

@login_required
def staff_dashboard(request):

    if not request.user.is_staff:
        return redirect("/")

    questions = Question.objects.order_by("-id")[:20]

    context = {

        "question_count": Question.objects.count(),

        "test_count": Exam.objects.count(),

        "student_count": Student.objects.filter(
            is_active=True
        ).count(),

        "batch_count": Batch.objects.count(),

        "questions": questions,

    }

    return render(
        request,
        "operations/dashboard.html",
        context,
    )

    if not request.user.is_staff:
        return redirect("/")

    questions = Question.objects.order_by("-id")[:20]

    return render(request, "operations/dashboard.html", {
        "questions": questions
    })
# ================= CREATE EXAM ================= #

@login_required
def create_exam(request):

    if not request.user.is_staff:
        return redirect('/')

    if request.method == 'POST':

        form = ExamForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Exam created successfully.')
            return redirect('staff_dashboard')

    else:
        form = ExamForm()

        return render(request, 'operations/create_exam.html', {
        'form': form
    })


def exam_library(request):
    from .models import Exam

    exams = Exam.objects.all().order_by('-id')

    return render(
        request,
        'operations/exam_library.html',
        {
            'exams': exams,
        }
    )

# ================= EDIT PERFORMANCE TEST ================= #

@login_required
def edit_test(request, exam_id):

    if not request.user.is_staff:
        return redirect('/')

    exam = get_object_or_404(
        Exam.objects.select_related(
            "assessment",
            "batch",
            "topic",
        ),
        id=exam_id,
    )

    assessment = exam.assessment

    assessment_subject = get_object_or_404(
        AssessmentSubject.objects.select_related(
            "subject",
        ),
        assessment=assessment,
    )

    batches = Batch.objects.all().order_by("id")

    assessment_types = (
        Assessment.objects.model
        .assessment_type
        .field
        .related_model
        .objects
        .filter(is_active=True)
        .order_by("display_order", "name")
    )

    if request.method == "POST":

        # --------------------------------------------------
        # ASSESSMENT DETAILS
        # --------------------------------------------------

        assessment.assessment_name = request.POST.get(
            "assessment_name"
        )

        assessment.assessment_type_id = request.POST.get(
            "assessment_type"
        )

        assessment.academic_session = request.POST.get(
            "academic_session"
        )

        assessment.batch_id = request.POST.get(
            "batch"
        )

        assessment.assessment_date = request.POST.get(
            "assessment_date"
        )

        assessment.save()


        # --------------------------------------------------
        # SUBJECT DETAILS
        # --------------------------------------------------

        assessment_subject.chapter_covered = request.POST.get(
            "chapter_covered",
            ""
        )

        assessment_subject.maximum_marks = request.POST.get(
            "maximum_marks"
        )

        assessment_subject.duration_minutes = request.POST.get(
            "duration_minutes"
        )

        assessment_subject.save()


        # --------------------------------------------------
        # ONLINE EXAM DETAILS
        # --------------------------------------------------

        exam.name = assessment.assessment_name

        exam.batch_id = assessment.batch_id

        exam.duration = assessment_subject.duration_minutes

        exam.total_marks = assessment_subject.maximum_marks

        start_time = request.POST.get(
            "start_time"
        )

        end_time = request.POST.get(
            "end_time"
        )

        if start_time:

            exam.start_time = timezone.make_aware(
                datetime.fromisoformat(
                    start_time
                )
            )

        else:

            exam.start_time = None


        if end_time:

            exam.end_time = timezone.make_aware(
                datetime.fromisoformat(
                    end_time
                )
            )

        else:

            exam.end_time = None


        exam.save()


        messages.success(
            request,
            "Test updated successfully."
        )

        return redirect(
            "exam_library"
        )


    # ------------------------------------------------------
    # PAGE CONTEXT
    # ------------------------------------------------------

    context = {

        "exam": exam,

        "assessment": assessment,

        "assessment_subject": assessment_subject,

        "batches": batches,

        "assessment_types": assessment_types,

        "academic_sessions":
            Assessment.ACADEMIC_SESSION_CHOICES,

    }

    return render(
        request,
        "operations/edit_test.html",
        context,
    )

# ================= ASSIGN TEST TO STUDENTS ================= #

@login_required
def assign_test(request, exam_id):

    if not request.user.is_staff:
        return redirect('/')

    exam = get_object_or_404(
        Exam.objects.select_related(
            "batch",
            "topic",
        ),
        id=exam_id,
    )

    # ------------------------------------------------------
    # ELIGIBLE STUDENTS
    # Primary batch OR additional batch
    # ------------------------------------------------------

    students = Student.objects.filter(
        models.Q(batch=exam.batch)
        |
        models.Q(additional_batches=exam.batch),
        is_active=True,
    ).distinct().order_by(
        "student_name"
    )

    # ------------------------------------------------------
    # SAVE ASSIGNMENTS
    # ------------------------------------------------------

    if request.method == "POST":

        assignment_mode = request.POST.get(
            "assignment_mode"
        )

        selected_student_ids = request.POST.getlist(
            "students"
        )

        if assignment_mode == "batch":

            students_to_assign = students

        elif assignment_mode in [
            "selected",
            "individual",
        ]:

            students_to_assign = students.filter(
                id__in=selected_student_ids
            )

        else:

            messages.error(
                request,
                "Please select an assignment mode."
            )

            return redirect(
                "assign_test",
                exam_id=exam.id,
            )

        created_count = 0

        for student in students_to_assign:

            assignment, created = (
                ExamAssignment.objects.get_or_create(
                    exam=exam,
                    student=student,
                    defaults={
                        "is_active": True
                    },
                )
            )

            if created:

                created_count += 1

            elif not assignment.is_active:

                assignment.is_active = True

                assignment.save(
                    update_fields=["is_active"]
                )

        messages.success(
            request,
            f"{created_count} student(s) assigned successfully."
        )

        return redirect(
            "exam_library"
        )

    context = {

        "exam": exam,

        "students": students,

    }

    return render(
        request,
        "operations/assign_test.html",
        context,
    )