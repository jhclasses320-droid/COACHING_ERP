from django.shortcuts import render, redirect
from django.db.models import Q
from .models import Question


def dashboard(request):
    return render(request, 'question_bank/dashboard.html')


def create_question(request):

    if request.method == 'POST':

        Question.objects.create(
            class_name=request.POST.get('class_name'),
            subject=request.POST.get('subject'),
            chapter=request.POST.get('chapter'),
            topic=request.POST.get('topic'),
            question_type=request.POST.get('question_type'),
            difficulty=request.POST.get('difficulty'),
            marks=request.POST.get('marks') or 1,
            negative_marks=request.POST.get('negative_marks') or 0,
            estimated_time=request.POST.get('estimated_time') or 60,
            keywords=request.POST.get('keywords', ''),
            olympiad_question=request.POST.get('olympiad_question') == 'on',
            is_active=request.POST.get('is_active') == 'on',
            question_text=request.POST.get('question_text', ''),
            option_a=request.POST.get('option_a', ''),
            option_b=request.POST.get('option_b', ''),
            option_c=request.POST.get('option_c', ''),
            option_d=request.POST.get('option_d', ''),
            correct_option=request.POST.get('correct_option', ''),
            solution=request.POST.get('solution', ''),
        )

        return redirect('question_dashboard')

    return render(request, 'question_bank/create_question.html')


def search_questions(request):

    query = request.GET.get('q', '').strip()

    questions = Question.objects.all().order_by('-id')

    if query:
        questions = questions.filter(
            Q(question_text__icontains=query) |
            Q(topic__icontains=query) |
            Q(chapter__icontains=query) |
            Q(subject__icontains=query) |
            Q(class_name__icontains=query) |
            Q(keywords__icontains=query)
        )

    return render(
        request,
        'question_bank/search_questions.html',
        {
            'questions': questions,
            'query': query,
        }
    )