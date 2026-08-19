from django import forms
from .models import Question, Batch, Topic, Exam


class QuestionForm(forms.ModelForm):

    class Meta:
        model = Question

        fields = [
            'batch',
            'topic',
            'question_mode',
            'difficulty',
            'marks',
            'negative_marks',
            'estimated_time',
            'is_active',

            # Question
            'question_text',
            'question_image',

            # Option A
            'option_a_text',
            'option_a_image',

            # Option B
            'option_b_text',
            'option_b_image',

            # Option C
            'option_c_text',
            'option_c_image',

            # Option D
            'option_d_text',
            'option_d_image',

            # Correct answer
            'correct_option',

            # Solution
            'feedback_text',
            'feedback_image',
        ]

        widgets = {

            'question_text': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': 'Type the question here...'
            }),

            'feedback_text': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Solution / explanation'
            }),

            'batch': forms.Select(attrs={'class': 'form-select'}),
            'topic': forms.Select(attrs={'class': 'form-select'}),
            'question_mode': forms.Select(attrs={'class': 'form-select'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'correct_option': forms.Select(attrs={'class': 'form-select'}),

            'marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'negative_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'estimated_time': forms.NumberInput(attrs={'class': 'form-control'}),

            'option_a_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option A text'
            }),

            'option_b_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option B text'
            }),

            'option_c_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option C text'
            }),

            'option_d_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Option D text'
            }),
        }
     


class ExamForm(forms.ModelForm):

    class Meta:
        model = Exam

        fields = [
            'name',
            'batch',
            'topic',
            'duration',
            'total_marks',
            'number_of_questions',
            'start_time',
            'end_time',
        ]

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'batch': forms.Select(attrs={'class': 'form-select'}),
            'topic': forms.Select(attrs={'class': 'form-select'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'number_of_questions': forms.NumberInput(attrs={'class': 'form-control'}),

            'start_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                }
            ),

            'end_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                }
            ),
        }