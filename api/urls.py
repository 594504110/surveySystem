# -*- coding: utf-8 -*-

from django.urls import path
from django.urls import re_path

from .views import survey

urlpatterns = [
    path("surveys/", survey.SurveyApi.as_view()),
    re_path("survey/(?P<pk>\d+)/", survey.SurveyDetailApi.as_view()),
]
