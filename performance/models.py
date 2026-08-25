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

    is_retest = models.BooleanField(
        default=False,
        verbose_name="Retest"
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


    # ==========================================================
# WORKSHEET GENERATOR
# ==========================================================


class WorksheetProject(models.Model):

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ANALYSING', 'Analysing Sources'),
        ('READY', 'Ready to Generate'),
        ('GENERATING', 'Generating Worksheets'),
        ('COMPLETED', 'Completed'),
    ]

    class_level = models.CharField(
        max_length=50,
        verbose_name="Class"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='worksheet_projects'
    )

    chapter = models.ForeignKey(
        'students.Chapter',
        on_delete=models.PROTECT,
        related_name='worksheet_projects',
        null=True,
        blank=True
    )

    chapter_name = models.CharField(
        max_length=200,
        verbose_name="Chapter Name"
    )

    title = models.CharField(
        max_length=250,
        verbose_name="Worksheet Project Title"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    number_of_sets = models.PositiveIntegerField(
        default=1,
        verbose_name="Number of Worksheet Sets"
    )

    worksheets_per_set = models.PositiveIntegerField(
        default=4,
        verbose_name="Worksheets Per Set"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='worksheet_projects'
    )

    created_on = models.DateTimeField(
        auto_now_add=True
    )

    updated_on = models.DateTimeField(
        auto_now=True
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ['-created_on']
        verbose_name = "Worksheet Project"
        verbose_name_plural = "Worksheet Projects"

    def __str__(self):
        return self.title


# ==========================================================
# WORKSHEET SOURCE DOCUMENT
# ==========================================================


class WorksheetSourceDocument(models.Model):

    SOURCE_TYPE_CHOICES = [
        ('TEXTBOOK', 'Textbook'),
        ('NOTES', 'School Notes'),
        ('REFERENCE', 'Reference Material'),
        ('PYQ', 'Previous Year Questions'),
        ('OTHER', 'Other'),
    ]

    project = models.ForeignKey(
        WorksheetProject,
        on_delete=models.CASCADE,
        related_name='source_documents'
    )

    title = models.CharField(
        max_length=250
    )

    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE_CHOICES,
        default='OTHER'
    )

    pdf_file = models.FileField(
        upload_to='worksheet_sources/'
    )

    uploaded_on = models.DateTimeField(
        auto_now_add=True
    )

    is_active = models.BooleanField(
        default=True
    )

    # Filled later by the AI analysis process
    page_count = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    extracted_text = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['uploaded_on']
        verbose_name = "Worksheet Source Document"
        verbose_name_plural = "Worksheet Source Documents"

    def __str__(self):
        return self.title


# ==========================================================
# WORKSHEET SET
# ==========================================================


class WorksheetSet(models.Model):

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('GENERATING', 'Generating'),
        ('COMPLETED', 'Completed'),
    ]

    project = models.ForeignKey(
        WorksheetProject,
        on_delete=models.CASCADE,
        related_name='worksheet_sets'
    )

    set_number = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    created_on = models.DateTimeField(
        auto_now_add=True
    )

    completed_on = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['set_number']
        unique_together = (
            'project',
            'set_number',
        )
        verbose_name = "Worksheet Set"
        verbose_name_plural = "Worksheet Sets"

    def __str__(self):
        return f"{self.project.title} - Set {self.set_number}"


# ==========================================================
# INDIVIDUAL WORKSHEET
# ==========================================================


class Worksheet(models.Model):

    WORKSHEET_TYPE_CHOICES = [
        ('FOUNDATION', 'Foundation'),
        ('CONCEPTUAL', 'Conceptual'),
        ('APPLICATION', 'Application'),
        ('HOTS', 'HOTS / Comprehensive'),
        ('MIXED', 'Mixed'),
    ]

    set = models.ForeignKey(
        WorksheetSet,
        on_delete=models.CASCADE,
        related_name='worksheets'
    )

    worksheet_number = models.PositiveIntegerField()

    title = models.CharField(
        max_length=250
    )

    worksheet_type = models.CharField(
        max_length=20,
        choices=WORKSHEET_TYPE_CHOICES,
        default='MIXED'
    )

    total_marks = models.PositiveIntegerField(
        default=0
    )

    duration_minutes = models.PositiveIntegerField(
        default=60
    )

    answer_space_mode = models.CharField(
        max_length=20,
        choices=[
            ('AUTO', 'Automatic'),
            ('COMPACT', 'Compact'),
            ('STANDARD', 'Standard'),
            ('SPACIOUS', 'Spacious'),
        ],
        default='AUTO'
    )

    include_answer_key = models.BooleanField(
        default=True
    )

    created_on = models.DateTimeField(
        auto_now_add=True
    )

    updated_on = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['worksheet_number']
        unique_together = (
            'set',
            'worksheet_number',
        )
        verbose_name = "Worksheet"
        verbose_name_plural = "Worksheets"

    def __str__(self):
        return self.title


# ==========================================================
# WORKSHEET QUESTION
# ==========================================================


class WorksheetQuestion(models.Model):

    QUESTION_TYPE_CHOICES = [
        ('MCQ', 'MCQ'),
        ('2M', '2 Marker'),
        ('3M', '3 Marker'),
        ('5M', '5 Marker'),
        ('CASE', 'Case Study'),
    ]

    worksheet = models.ForeignKey(
        Worksheet,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    question = models.ForeignKey(
        'students.Question',
        on_delete=models.PROTECT,
        related_name='worksheet_usages'
    )

    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPE_CHOICES
    )

    question_number = models.PositiveIntegerField()

    marks = models.PositiveIntegerField(
        default=1
    )

    answer_space_lines = models.PositiveIntegerField(
        default=3
    )

    created_on = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['question_number']
        unique_together = (
            'worksheet',
            'question_number',
        )
        verbose_name = "Worksheet Question"
        verbose_name_plural = "Worksheet Questions"

    def __str__(self):
        return (
            f"{self.worksheet.title} - "
            f"Q{self.question_number}"
        )