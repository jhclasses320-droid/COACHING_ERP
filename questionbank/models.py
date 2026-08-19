from django.db import models


class Question(models.Model):

    QUESTION_TYPES = [
        ('MCQ', 'MCQ'),
        ('SHORT', 'Short Answer'),
        ('LONG', 'Long Answer'),
        ('CASE', 'Case Study'),
        ('NUM', 'Numerical'),
    ]

    DIFFICULTY_LEVELS = [
        ('E', 'Easy'),
        ('M', 'Medium'),
        ('H', 'Hard'),
    ]

    class_name = models.CharField(max_length=20)
    subject = models.CharField(max_length=50)
    chapter = models.CharField(max_length=100)
    topic = models.CharField(max_length=100)

    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPES
    )

    difficulty = models.CharField(
        max_length=1,
        choices=DIFFICULTY_LEVELS
    )

    marks = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    negative_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    estimated_time = models.PositiveIntegerField(default=60)

    keywords = models.CharField(max_length=255, blank=True)

    olympiad_question = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    question_text = models.TextField()

    question_image = models.ImageField(
        upload_to='question_images/',
        blank=True,
        null=True
    )

    option_a = models.TextField(blank=True)
    option_b = models.TextField(blank=True)
    option_c = models.TextField(blank=True)
    option_d = models.TextField(blank=True)

    correct_option = models.CharField(
        max_length=1,
        choices=[
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D'),
        ],
        blank=True
    )

    solution = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.class_name} - {self.subject} - {self.topic}'