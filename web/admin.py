from django.contrib import admin

from . import models

# Register your models here.

admin.site.register(models.MiddleSurvey)
admin.site.register(models.SurveyCode)
admin.site.register(models.SurveyRecord)
