from django.db import models
from django.contrib.auth.models import User
from students.models import Batch, Subject, Student


# ==========================================================
# ASSESSMENT TYPE
# ==========================================================

class AssessmentType(models.Model):

    name = models.CharField(max_length=100, unique=True)

    is_active = models.BooleanField(default=True)

    display_order = models.PositiveIntegerField(default=1)

    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "Assessment Type"
        verbose_name_plural = "Assessment Types"

    def __str__(self):
        return self.name


# ==========================================================
# ASSESSMENT
# ==========================================================

class Assessment(models.Model):

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('READY_FOR_MARKS', 'Ready for Marks Entry'),
        ('COMPLETED', 'Completed'),
    ]

    ACADEMIC_SESSION_CHOICES = [
        ('2025-26', '2025-26'),
        ('2026-27', '2026-27'),
        ('2027-28', '2027-28'),
        ('2028-29', '2028-29'),
        ('2029-30', '2029-30'),
    ]

    assessment_name = models.CharField(max_length=200)

    assessment_type = models.ForeignKey(
        AssessmentType,
        on_delete=models.PROTECT,
        related_name='assessments'
    )

    academic_session = models.CharField(
        max_length=20,
        choices=ACADEMIC_SESSION_CHOICES
    )

    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name='assessments'
    )

    assessment_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_assessments'
    )

    created_on = models.DateTimeField(auto_now_add=True)

    updated_on = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-assessment_date', 'assessment_name']
        verbose_name = "Assessment"
        verbose_name_plural = "Assessments"

    def __str__(self):
        return f"{self.assessment_name} ({self.batch})"



# ==========================================================
# ASSESSMENT SUBJECT
# ==========================================================

class AssessmentSubject(models.Model):

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='subjects'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT
    )

     
    topic = models.ForeignKey(
        'students.Topic',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='assessment_subjects'
    )

    chapters = models.ManyToManyField(
        'students.Chapter',
        blank=True,
        related_name='assessment_chapters'
    )

    chapter_covered = models.CharField(
        max_length=250,
        verbose_name="Chapter Covered"
    )

    maximum_marks = models.PositiveIntegerField()

    duration_minutes = models.PositiveIntegerField(
        default=60,
        verbose_name="Duration (Minutes)"
    )

    class Meta:
        ordering = ['subject__name']
        verbose_name = "Assessment Subject"
        verbose_name_plural = "Assessment Subjects"

        unique_together = (
            'assessment',
            'subject',
        )

    def __str__(self):
        return f"{self.assessment.assessment_name} - {self.subject.name}"


# ==========================================================
# STUDENT MARKS
# ==========================================================

class StudentMark(models.Model):

    assessment_subject = models.ForeignKey(
        AssessmentSubject,
        on_delete=models.CASCADE,
        related_name='student_marks'
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='performance_marks'
    )

    marks_scored = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True
    )

    is_absent = models.BooleanField(
        default=False,
        verbose_name="Absent"
    )

    created_on = models.DateTimeField(
        auto_now_add=True
    )

    updated_on = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['student__student_name']
        verbose_name = "Student Mark"
        verbose_name_plural = "Student Marks"

        unique_together = (
            'assessment_subject',
            'student',
        )

    def __str__(self):
        return (
            f"{self.student.student_name} - "
            f"{self.assessment_subject}"
        )
