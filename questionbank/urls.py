from django.urls import path
from . import views

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

]