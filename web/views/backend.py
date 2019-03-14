# -*- coding: utf-8 -*-
import os

import xlwt

from django.conf import settings
from django.views import View
from django.views.generic import TemplateView
from django.http.response import FileResponse
from django.db.models import Count

from web import models


class IndexView(TemplateView):
    template_name = "web/index.html"

    extra_context = {
        "title": "欢迎使用问卷调查系统"
    }


class SurveyReportView(TemplateView):
    template_name = "web/report.html"

    extra_context = {
        "title": "问卷报告"
    }

    def get_context_data(self, **kwargs):
        context = super(SurveyReportView, self).get_context_data(**kwargs)

        result = []
        middle_survey = models.MiddleSurvey.objects.get(pk=context.get("pk"))

        for survey in middle_survey.surveys.iterator():

            records = models.SurveyRecord.objects.filter(middle_survey=middle_survey, survey=survey)

            score_records = records.exclude(survey_item__answer_type="suggestion")
            # 构造每个唯一码的数据
            answers = {}
            for item in score_records.iterator():
                unique_code = item.survey_code.unique_code

                if unique_code not in answers:
                    answers[unique_code] = {
                        'questions': [{
                            'id': item.survey_item.pk,
                            'name': item.survey_item.name,
                            'score': item.score
                        }],
                        'is_hide': item.is_hide,
                        'score_sum': item.score
                    }
                else:
                    answers[unique_code]["score_sum"] += item.score
                    answers[unique_code]["questions"].append({
                        'id': item.survey_item.pk,
                        'name': item.survey_item.name,
                        'score': item.score
                    })

            # 构造每个问题的数据
            choices = {}
            for item in score_records.iterator():
                question_id = item.survey_item.pk
                max_score = item.survey_item.answers.order_by("-points").only("points").first().points

                if question_id in choices:
                    choices[question_id]["real_score"] += item.score
                    choices[question_id]["score"] += max_score
                else:
                    choices[question_id] = {
                        'name': item.survey_item.name,
                        'real_score': item.score,
                        'score': max_score
                    }

            score = 0
            real_score = 0
            for value in choices.values():
                score += value["score"]
                real_score += value["real_score"]

            result.append({
                "id": "survey-{}".format(survey.pk),
                "name": survey.name,
                "answers": answers,
                "choices": choices,
                # 建议
                "suggestions": [
                    item.suggestion for item in records.filter(survey_item__answer_type="suggestion").iterator()
                ],
                "percent": "{:.2f}".format(real_score / (score or 1) * 100)
            })

        context["result"] = result
        context["count"] = middle_survey.surveyrecord_set.values("survey_code").annotate(
            Count("survey_code")
        ).count()

        return context


class SurveyDetailView(TemplateView):
    template_name = "web/detail.html"

    extra_context = {
        "title": "请填写问卷调查"
    }


class SurveyCodeDownloadView(View):

    def get(self, request, *args, **kwargs):
        # 找到问卷调查的对应的唯一码
        codes = models.SurveyCode.objects.filter(middle_survey_id=kwargs.get("pk"))
        # 写入到 excel 文件, 下载
        xls = xlwt.Workbook(encoding="utf-8", style_compression=2)
        sheet = xls.add_sheet("sheet1", cell_overwrite_ok=True)
        sheet.write(0, 0, '号码')

        for index, code in enumerate(codes.iterator(), 1):
            sheet.write(index, 0, code.unique_code)

        xls.save("唯一码.xls")

        return FileResponse(open(os.path.join(settings.BASE_DIR, "唯一码.xls"), "rb"), as_attachment=True)
