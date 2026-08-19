from django.shortcuts import render, redirect
from django.contrib import messages

from students.forms import QuestionForm


def create_question(request):

    if request.method == 'POST':

        form = QuestionForm(request.POST, request.FILES)

        if form.is_valid():

            form.save()

            messages.success(request, 'Question saved successfully.')

            return redirect('create_question')

        else:

            messages.error(request, 'Please correct the errors below.')

    else:

        form = QuestionForm()

    return render(
        request,
        'question_bank/create_question.html',
        {'form': form}
    )