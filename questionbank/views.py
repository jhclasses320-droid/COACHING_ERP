from django.shortcuts import render, redirect
from django.db.models import Q
from students.forms import QuestionForm
from students.models import Question


def dashboard(request):
    questions = Question.objects.all().order_by("-id")

    return render(
        request,
        "question_bank/dashboard.html",
        {
            "questions": questions,
        },
    )


def create_question(request):

    if request.method == "POST":
        form = QuestionForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect("question_dashboard")

    else:
        form = QuestionForm()

    return render(
        request,
        "question_bank/create_question.html",
        {
            "form": form,
        },
    )


def search_questions(request):

    query = request.GET.get("q", "").strip()

    questions = Question.objects.all().order_by("-id")

    if query:
        questions = questions.filter(
            Q(question_text__icontains=query)
            | Q(topic__name__icontains=query)
            | Q(option_a_text__icontains=query)
            | Q(option_b_text__icontains=query)
            | Q(option_c_text__icontains=query)
            | Q(option_d_text__icontains=query)
            | Q(feedback_text__icontains=query)
        )

    return render(
        request,
        "question_bank/search_questions.html",
        {
            "questions": questions,
            "query": query,
        },
    )


def delete_question(request, question_id):

    if request.method == "POST":
        question = Question.objects.get(id=question_id)
        question.delete()

    return redirect("question_dashboard")
