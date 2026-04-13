
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import models
from django.http import HttpResponse
from datetime import date

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from django.shortcuts import render, get_object_or_404
from .models import Exam, ExamQuestion
from .models import (
    Student,
    Exam,
    Question,
    FeePayment,
    Batch,
    AttendanceSession,
    AttendanceRecord
)

# ================= LOGIN ================= #
def student_login(request):
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        mobile = request.POST.get("mobile")

        try:
            student = Student.objects.get(
                student_id=student_id,
                student_mobile=mobile
            )

            if not student.is_active:
                messages.error(request, "Your account is inactive.")
                return redirect('student_login')

            request.session['student_id'] = student.id
            return redirect('student_dashboard')

        except Student.DoesNotExist:
            messages.error(request, "Invalid ID or Mobile")

    return render(request, 'students/login.html')


# ================= DASHBOARD ================= #
def student_dashboard(request):

    student_id = request.session.get('student_id')

    if not student_id:
        return redirect('student_login')

    student = Student.objects.get(id=student_id)

    exams = Exam.objects.filter(batch=student.batch)

    attendance = AttendanceRecord.objects.filter(student=student)

    return render(request, 'students/dashboard.html', {
        'student': student,
        'exams': exams,
        'attendance': attendance
    })


# ================= REPORT PAGE ================= #
def reports_dashboard(request):
    return render(request, 'admin/reports.html')


# ================= STUDENT PDF ================= #
def download_students_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="students_report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4))
    elements = []

    data = [['Name', 'Class', 'School', 'Mobile', 'Fee']]

    students = Student.objects.filter(is_active=True)

    for s in students:
        data.append([
            s.student_name,
            str(s.batch) if s.batch else '',
            str(s.school) if s.school else '',
            s.student_mobile or '',
            str(s.fee_amount or '')
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    return response


# ================= FEE REPORT ================= #
def download_fee_report(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="fee_report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4))
    elements = []

    data = [['Name', 'Total Fee', 'Paid', 'Pending']]

    students = Student.objects.filter(is_active=True)

    for s in students:
        total_fee = s.fee_amount or 0

        paid = FeePayment.objects.filter(student=s).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        pending = total_fee - paid

        data.append([
            s.student_name,
            str(total_fee),
            str(paid),
            str(pending)
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.green),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
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
        ('BACKGROUND', (0, 0), (-1, 0), colors.red),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
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

    students = Student.objects.filter(batch=batch, is_active=True).order_by("student_name")

    if request.method == "POST":

        for student in students:

            status = request.POST.get(f"student_{student.id}", "A")

            AttendanceRecord.objects.update_or_create(
                session=session,
                student=student,
                defaults={'status': status}
            )

        messages.success(request, "Attendance saved successfully ✅")

        return redirect('student_dashboard')

    return render(request, "attendance/mark.html", {
        'students': students,
        'batch': batch
    })


    if request.method == "POST":
        for student in students:
            status = request.POST.get(f"student_{student.id}", 'A')

            AttendanceRecord.objects.update_or_create(
                session=session,
                student=student,
                defaults={'status': status}
            )

        messages.success(request, "Attendance saved successfully ✅")
        return redirect('student_dashboard')

    return render(request, 'attendance/mark.html', {
        'students': students,
        'batch': batch,
        'session': session
    })


# ================= ATTENDANCE REPORT ================= #
def attendance_report(request):
    students = Student.objects.filter(is_active=True)
    report_data = []

    for s in students:
        total = AttendanceRecord.objects.filter(student=s).count()
        present = AttendanceRecord.objects.filter(student=s, status='P').count()

        percentage = (present / total * 100) if total > 0 else 0

        report_data.append({
            'student': s,
            'total': total,
            'present': present,
            'percentage': round(percentage, 2)
        })

    return render(request, 'attendance/report.html', {
        'report_data': report_data
    })


def attendance_batches(request):
    batches = Batch.objects.all()
    return render(request, 'attendance/batches.html', {'batches': batches})


# ================= STUDENT EXAMS ================= #

def student_exam_list(request):

    student_id = request.session.get('student_id')

    if not student_id:
        return redirect('student_login')

    student = Student.objects.get(id=student_id)

    exams = Exam.objects.filter(batch=student.batch)

    return render(request, 'students/exam_list.html', {
        'exams': exams
    })


# ================= START EXAM ================= #

def start_exam(request, exam_id):

    exam = get_object_or_404(Exam, id=exam_id)

    questions = ExamQuestion.objects.filter(exam=exam)

    return render(request, 'students/start_exam.html', {
        'exam': exam,
        'questions': questions
    })

    from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

# ================= STAFF LOGIN ================= #

def staff_login(request):

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect("question_dashboard")

        messages.error(request, "Invalid username or password")

    return render(request, "staff/login.html")


# ================= QUESTION DASHBOARD ================= #

@login_required
def question_dashboard(request):

    if not request.user.groups.filter(name="Question Entry").exists():
        return redirect("/")

    questions = Question.objects.order_by("-id")[:20]

    return render(request, "staff/dashboard.html", {
        "questions": questions
    })

    from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

# ================= STAFF LOGIN ================= #

def staff_login(request):

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect("staff_dashboard")

        messages.error(request, "Invalid username or password")

    return render(request, "staff/login.html")


# ================= STAFF DASHBOARD ================= #

@login_required
def staff_dashboard(request):

    if not request.user.groups.filter(name="Question Entry").exists():
        return redirect("/")

    questions = Question.objects.order_by("-id")[:20]

    return render(request, "staff/dashboard.html", {
        "questions": questions
    })

    from django.contrib.auth.decorators import login_required

@login_required
def staff_dashboard(request):
    return render(request, "staff/dashboard.html")

    # ================= STAFF LOGIN ================= #

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

def staff_login(request):

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect("staff_dashboard")

        messages.error(request, "Invalid username or password")

    return render(request, "staff/login.html")


@login_required
def staff_dashboard(request):

    if not request.user.groups.filter(name="Question Entry").exists():
        return redirect("/")

    questions = Question.objects.order_by("-id")[:20]

    return render(request, "staff/dashboard.html", {
        "questions": questions
    })