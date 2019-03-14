# -*- coding: utf-8 -*-
# __author__ = "maple"

from django.urls import path
from django.urls import re_path

from .views import backend

urlpatterns = [
    path("", backend.IndexView.as_view()),
    re_path("^(?P<pk>\d+)/$", backend.SurveyDetailView.as_view()),
    re_path("^(?P<pk>\d+)/report/$", backend.SurveyReportView.as_view()),

    re_path("^(?P<pk>\d+)/downloads/$", backend.SurveyCodeDownloadView.as_view()),

]
