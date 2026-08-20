from django.db import models


# ================= BASIC MODELS ================= #

class School(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Batch(models.Model):
    batch_name = models.CharField(max_length=50)
    student_class = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.batch_name} ({self.student_class})"


# ================= STUDENT MODEL ================= #

class Student(models.Model):

    FEE_PLAN_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('THREE_QUARTERLY', '3 Quarterly'),
    ]

    student_name = models.CharField(max_length=100)
    student_mobile = models.CharField(max_length=15, blank=True, null=True)
    student_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    must_change_password = models.BooleanField(default=True)

    date_of_birth = models.DateField(blank=True, null=True)

    father_name = models.CharField(max_length=100, blank=True, null=True)
    father_mobile = models.CharField(max_length=15, blank=True, null=True)

    mother_name = models.CharField(max_length=100, blank=True, null=True)
    mother_mobile = models.CharField(max_length=15, blank=True, null=True)

    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Existing primary batch (UNCHANGED)

    batch = models.ForeignKey(
        Batch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="primary_students"
    )

    # Student can belong to multiple batches

    additional_batches = models.ManyToManyField(
    Batch,
    blank=True,
    related_name="additional_students",
    verbose_name="Additional Batches",
    help_text="Select additional batches. Main Batch is selected above."
    )
    

    fee_plan = models.CharField(
        max_length=20,
        choices=FEE_PLAN_CHOICES,
        blank=True,
        null=True
    )

    fee_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )

    address = models.TextField(blank=True, null=True)

    student_photo = models.ImageField(
        upload_to='students/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)
    

    def __str__(self):
        return self.student_name


# ================= FEE PAYMENT ================= #

class FeePayment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)

    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.student.student_name} - {self.amount}"


# ================= ENQUIRY ================= #

class Query(models.Model):
    student_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    school = models.CharField(max_length=100, blank=True, null=True)
    student_class = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.student_name or "Query"


# ================= SUBJECT ================= #

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


# ================= TOPIC ================= #

class Topic(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='topics'
    )

    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.subject.name})"

    # ================= CHAPTER ================= #

class Chapter(models.Model):

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='chapters'
    )

    name = models.CharField(max_length=150)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        unique_together = ('topic', 'name')
        verbose_name = "Chapter"
        verbose_name_plural = "Chapters"

    def __str__(self):
        return f"{self.name} ({self.topic.name})"   

    # ================= QUESTION ================= #

class Question(models.Model):

    batch = models.ForeignKey(
    Batch,
    on_delete=models.CASCADE,
    related_name="questions",
    verbose_name="Batch",
)

    # ==========================================================
    # CHOICES
    # ==========================================================

    QUESTION_MODE_CHOICES = [
        ('IMAGE', 'Import Question'),
        ('TYPED', 'Typed Question'),
        ('HYBRID', 'Hybrid Question'),
    ]

    QUESTION_TYPE_CHOICES = [
        ('MCQ', 'MCQ'),
        ('MATCH', 'Match the Matrix'),
        ('CASE', 'Case Study'),
        ('NUMERICAL', 'Numerical'),
        ('SHORT', 'Short Answer'),
        ('LONG', 'Long Answer'),
        ('ASSERTION', 'Assertion–Reason'),
        ('OTHER', 'Other'),
    ]

    DIFFICULTY_CHOICES = [
        ('E', 'Easy'),
        ('M', 'Medium'),
        ('H', 'Hard'),
    ]

    SOURCE_CHOICES = [
        ('SELF', 'Self Created'),
        ('NCERT', 'NCERT'),
        ('EXEMPLAR', 'NCERT Exemplar'),
        ('PYQ', 'Previous Year Question'),
        ('BOOK', 'Reference Book'),
        ('AI', 'AI Generated'),
    ]

    # ==========================================================
    # BASIC DETAILS
    # ==========================================================


    batch = models.ForeignKey(
    Batch,
    on_delete=models.CASCADE,
    related_name="questions",
    null=True,
    blank=True,
    )

    topic = models.ForeignKey(
    Topic,
    on_delete=models.CASCADE,
)



    question_mode = models.CharField(
        max_length=10,
        choices=QUESTION_MODE_CHOICES,
        default='IMAGE'
    )

    question_type = models.CharField(
        max_length=15,
        choices=QUESTION_TYPE_CHOICES,
        default='MCQ'
    )

    difficulty = models.CharField(
        max_length=1,
        choices=DIFFICULTY_CHOICES,
        default='M'
    )

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='SELF'
    )

    estimated_time = models.PositiveIntegerField(
        default=60,
        help_text="Estimated time in seconds"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # ==========================================================
    # QUESTION
    # ==========================================================

    question_text = models.TextField(
        blank=True,
        null=True
    )


    question_image = models.ImageField(
        upload_to='questions/',
        blank=True,
        null=True
    )

    # ==========================================================
    # OPTION A
    # ==========================================================

    option_a_text = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    option_a_image = models.ImageField(
        upload_to='options/',
        blank=True,
        null=True
    )

    # ==========================================================
    # OPTION B
    # ==========================================================

    option_b_text = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    option_b_image = models.ImageField(
        upload_to='options/',
        blank=True,
        null=True
    )

    # ==========================================================
    # OPTION C
    # ==========================================================

    option_c_text = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    option_c_image = models.ImageField(
        upload_to='options/',
        blank=True,
        null=True
    )

    # ==========================================================
    # OPTION D
    # ==========================================================

    option_d_text = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    option_d_image = models.ImageField(
        upload_to='options/',
        blank=True,
        null=True
    )

    # ==========================================================
    # CORRECT ANSWER
    # ==========================================================

    correct_option = models.CharField(
        max_length=1,
        choices=[
            ('A', 'Option A'),
            ('B', 'Option B'),
            ('C', 'Option C'),
            ('D', 'Option D'),
        ]
    )

    # ==========================================================
    # FEEDBACK / SOLUTION
    # ==========================================================

    feedback_text = models.TextField(
        blank=True,
        null=True
    )

    feedback_image = models.ImageField(
        upload_to='feedback/',
        blank=True,
        null=True
    )

    # ==========================================================
    # MARKING
    # ==========================================================

    marks = models.PositiveIntegerField(default=1)

    negative_marks = models.FloatField(default=0)

    # ==========================================================
    # DISPLAY
    # ==========================================================

    def __str__(self):
        if self.question_text:
            return self.question_text[:80]
        return f"Image Question #{self.pk}"


# ================= EXAM ================= #

class Exam(models.Model):

    name = models.CharField(max_length=100)


    assessment = models.OneToOneField(
        'performance.Assessment',
        on_delete=models.CASCADE,
        related_name='online_exam',
        null=True,
        blank=True
    )



    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE
    )   




    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE
    )

    duration = models.IntegerField(
        help_text="Duration in minutes"
    )

    total_marks = models.IntegerField()

    number_of_questions = models.IntegerField(default=10)

    start_time = models.DateTimeField()

    end_time = models.DateTimeField()

    def __str__(self):
        return self.name

        
    # ================= EXAM ASSIGNMENT ================= #

class ExamAssignment(models.Model):

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="assignments"
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="exam_assignments"
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        unique_together = ("exam", "student")
        ordering = ["student__student_name"]

    def __str__(self):
        return f"{self.exam.name} - {self.student.student_name}"    




# ================= EXAM QUESTION ================= #


class ExamQuestion(models.Model):

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.exam.name} - Q{self.question.id}"

    # ================= ATTENDANCE SYSTEM ================= #

class AttendanceSession(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('batch', 'date')

    def __str__(self):
        return f"{self.batch} - {self.date}"


class AttendanceRecord(models.Model):

    STATUS_CHOICES = [
        ('P', 'Present'),
        ('A', 'Absent'),
        ('L', 'Late'),
    ]

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='records'
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES
    )

    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        return f"{self.student.student_name} - {self.status}"


# ================= STUDENT EXAM ATTEMPT ================= #

class StudentExamAttempt(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE
    )

    start_time = models.DateTimeField(auto_now_add=True)

    end_time = models.DateTimeField(
        blank=True,
        null=True
    )

    score = models.FloatField(default=0)

    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'exam')
        ordering = ['-score']

    def __str__(self):
        return f"{self.student.student_name} - {self.exam.name}"


# ================= STUDENT ANSWERS ================= #

class StudentAnswer(models.Model):

    attempt = models.ForeignKey(
        StudentExamAttempt,
        on_delete=models.CASCADE
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )

    selected_option = models.CharField(
        max_length=1,
        choices=[
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D'),
        ]
    )

    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.attempt.student.student_name} - Q{self.question.id}"

    # ================= STUDY MATERIAL ================= #

class StudyMaterial(models.Model):

    title = models.CharField(max_length=200)

    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name="study_materials"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="study_materials"
    )

    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="study_materials"
    )

    dropbox_link = models.URLField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["subject", "chapter", "title"]

    def __str__(self):
        return self.title