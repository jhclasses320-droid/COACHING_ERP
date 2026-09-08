from django.urls import path
from . import views
from students import question_views

app_name = "questionbank"

urlpatterns = [

    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "add/",
        views.create_question,
        name="create_question",
    ),

    path(
        "search/",
        views.search_questions,
        name="search_questions",
    ),

    path(
        "<int:question_id>/view/",
        question_views.view_question,
        name="view_question",
    ),

    path(
        "<int:question_id>/edit/",
        question_views.edit_question,
        name="edit_question",
    ),

]