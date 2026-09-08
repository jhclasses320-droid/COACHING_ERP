from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from students.forms import QuestionForm
from students.models import Question


def create_question(request):

    if request.method == 'POST':

        form = QuestionForm(request.POST, request.FILES)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Question saved successfully.'
            )

            return redirect('create_question')

        else:

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


def view_question(request, question_id):

    question = get_object_or_404(
        Question,
        id=question_id
    )

    return render(
        request,
        'question_bank/view_question.html',
        {'question': question}
    )


def edit_question(request, question_id):

    question = get_object_or_404(
        Question,
        id=question_id
    )

    if request.method == 'POST':

        form = QuestionForm(
            request.POST,
            request.FILES,
            instance=question
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Question updated successfully.'
            )

            return redirect(
                'questionbank:view_question',
                question_id=question.id
            )

        else:

            messages.error(
                request,
                'Please correct the errors below.'
            )

    else:

        form = QuestionForm(
            instance=question
        )

    return render(
        request,
        'question_bank/edit_question.html',
        {
            'form': form,
            'question': question
        }
    )