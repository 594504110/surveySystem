# -*- coding: utf-8 -*-

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.utils.crypto import get_random_string

from .. import models


@receiver(post_save, sender=models.MiddleSurvey)
def bulk_survey_codes(**kwargs):
    """
    根据调查问卷的人数, 批量创建唯一码
    :param kwargs:
    :return:
    """
    instance = kwargs.get("instance")
    quantity = instance.quantity

    codes = []

    while quantity > 0:
        code = get_random_string(length=8)
        if not models.SurveyCode.objects.filter(unique_code=code).exists():
            codes.append(models.SurveyCode(middle_survey=instance, unique_code=get_random_string(length=8)))
            quantity -= 1

    models.SurveyCode.objects.bulk_create(codes)
