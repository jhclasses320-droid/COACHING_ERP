from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone

from students.forms import QuestionForm
from students.models import Question, Batch, Subject, Topic


def question_dashboard(request):

    # ================= SEARCH FILTERS ================= #

    questions = Question.objects.all().order_by("-id")

    batch_id = request.GET.get("batch")
    subject_id = request.GET.get("subject")
    topic_id = request.GET.get("topic")
    difficulty = request.GET.get("difficulty")
    mode = request.GET.get("mode")
    status = request.GET.get("status")
    keyword = request.GET.get("keyword")

    if batch_id:
        questions = questions.filter(batch_id=batch_id)

    if subject_id:
        questions = questions.filter(topic__subject_id=subject_id)

    if topic_id:
        questions = questions.filter(topic_id=topic_id)

    if difficulty:
        questions = questions.filter(difficulty=difficulty)

    if mode:
        questions = questions.filter(question_mode=mode)

    if status == "1":
        questions = questions.filter(is_active=True)
    elif status == "0":
        questions = questions.filter(is_active=False)

    if keyword:
        questions = questions.filter(
            question_text__icontains=keyword
        )

    # ================= STATISTICS ================= #

    total_questions = Question.objects.count()

    today_questions = Question.objects.filter(
        created_at__date=timezone.localdate()
    ).count()

    active_questions = Question.objects.filter(
        is_active=True
    ).count()

    image_questions = Question.objects.filter(
        question_image__isnull=False
    ).exclude(
        question_image=""
    ).count()

    # ================= RECENT QUESTIONS ================= #

    recent_questions = Question.objects.select_related(
        "topic"
    ).order_by("-created_at")[:20]

    # ================= FILTER OPTIONS ================= #

    batches = Batch.objects.all().order_by("batch_name")
    subjects = Subject.objects.all().order_by("name")
    topics = Topic.objects.all().order_by("name")

    return render(
        request,
        "question_bank/dashboard.html",
        {
            "questions": questions,

            "total_questions": total_questions,
            "today_questions": today_questions,
            "active_questions": active_questions,
            "image_questions": image_questions,

            "recent_questions": recent_questions,

            "batches": batches,
            "subjects": subjects,
            "topics": topics,
        }
    )


def create_question(request):

    if request.method == 'POST':

        form = QuestionForm(request.POST, request.FILES)

        if form.is_valid():

            question = form.save(commit=False)

            # Force valid value from model choices
            question.question_mode = 'TYPED'

            question.save()

            messages.success(
                request,
                'Question saved successfully.'
            )

            return redirect('question_dashboard')

        else:

            print(form.errors)

            messages.error(
                request,
                'Please correct the errors below.'
            )

    else:

        form = QuestionForm()

    return render(
        request,
        'question_bank/create_question.html',
        {'form': form}
    )


def question_library(request):
    return render(
        request,
        'question_bank/question_library.html'
    )


def bulk_import(request):
    return render(
        request,
        'question_bank/bulk_import.html'
    )


def paper_builder(request):
    return render(
        request,
        'question_bank/paper_builder.html'
    )


def question_statistics(request):
    return render(
        request,
        'question_bank/statistics.html'
    )
