# -*- coding: utf-8 -*-

from django.db.models import Count
from django.utils.timezone import now
from django.db import transaction

from rest_framework import serializers

from web import models

from ..service import fields


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class SurveySerializer(DynamicFieldsModelSerializer):
    # 展示地区名称
    by_class = serializers.CharField(source="by_zone.name")
    # 统计填写人数
    count = serializers.SerializerMethodField()
    # 填写链接
    link = serializers.SerializerMethodField()
    # 指定时间格式 通过 format 参数控制
    # date = serializers.DateTimeField(format="%Y-%m-%d %X")
    date = fields.CustomDateField()
    # 操作
    handle = fields.HandleField(source="pk")

    class Meta:
        model = models.MiddleSurvey
        fields = (
            "name",
            "by_zone",
            "count",
            "link",
            "date",
            "handle",
        )

    def get_count(self, instance):
        # 统计一共分了多少个组
        return instance.surveyrecord_set.values("survey_code").annotate(Count("survey_code")).count()

    def get_link(self, instance):
        # 获取 `request` 对象
        request = self.context["request"]
        return "<a href='{link}'>{link}</a>".format(
            link="{}://{}/{}/".format(
                request.scheme, request.get_host(), instance.pk
            )
        )


class ChoiceSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = models.SurveyChoices
        fields = "__all__"


class QuestionSerializer(DynamicFieldsModelSerializer):
    survey = serializers.SerializerMethodField()
    survey_item = serializers.IntegerField(source="pk")
    # instance.answers
    choices = ChoiceSerializer(source="answers", many=True, fields=("content", "points"))
    # 用作于用户的输入
    value = serializers.CharField(default="")
    # 用作于展示错误信息
    error = serializers.CharField(default="")

    class Meta:
        model = models.SurveyItem
        fields = (
            "survey",
            "survey_item",
            "name",
            "answer_type",
            "choices",
            "value",
            "error",
        )

    def get_survey(self, instance):
        return self.context.get("survey_id")


class SurveyDetailSerializer(DynamicFieldsModelSerializer):
    questions = serializers.ListSerializer(child=QuestionSerializer())

    class Meta:
        model = models.Survey
        fields = (
            "id",
            "name",
            "questions"
        )

    def to_representation(self, instance):
        self.context["survey_id"] = instance.pk

        data = super(SurveyDetailSerializer, self).to_representation(instance)

        return data


class MiddleSurveyDetailSerializer(DynamicFieldsModelSerializer):
    # 第一种
    # surveys = serializers.ListSerializer(child=SurveyDetailSerializer())
    # 第二种
    # survey_details = SurveyDetailSerializer(many=True, source="surveys")
    surveys = SurveyDetailSerializer(many=True)

    class Meta:
        model = models.MiddleSurvey
        fields = (
            "name",
            "surveys",
        )


class QuestionCreateSerializer(serializers.ModelSerializer):
    value = serializers.CharField(required=True)

    class Meta:
        model = models.SurveyRecord
        fields = (
            "survey",
            "survey_item",
            "value"
        )

    def validate(self, data):
        data["middle_survey_id"] = self.context["view"].kwargs.get("pk")

        value = data.pop("value", "")
        survey_item = data.get("survey_item")

        if survey_item.answer_type == "single":
            data["score"] = value
            data["single"] = models.SurveyChoices.objects.filter(
                question=survey_item, points=value
            ).first()
        else:
            data["suggestion"] = value

        data["survey_code"] = self.context.get("unique_code")

        return data


class SurveyRoleSerializer(serializers.Serializer):
    questions = serializers.ListSerializer(
        child=QuestionCreateSerializer(),
        required=False, allow_empty=False,
        error_messages={
            "required": "这个字段必传",
            "empty": "这个字段不能为空列表",
        }
    )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class SurveyCreateSerializer(serializers.Serializer):
    unique_code = serializers.CharField(
        required=True, allow_null=False, allow_blank=False,
        error_messages={
            "required": "这个字段必传",
            "null": "这个字段不能为null",
            "blank": "这个字段不能为空",
        }
    )
    form_data = serializers.ListSerializer(
        child=SurveyRoleSerializer(),
        required=False, allow_empty=False,
        error_messages={
            "required": "这个字段必传",
            "empty": "这个字段不能为空列表",
        }
    )

    def validate_unique_code(self, value):
        view = self.context.get("view")
        code = models.SurveyCode.objects.filter(
            unique_code=value, middle_survey_id=view.kwargs.get("pk")
        ).first()

        if code is None:
            raise serializers.ValidationError("无效的唯一码")

        if code.used:
            raise serializers.ValidationError("唯一码已被使用")

        self.context["unique_code"] = code
        return code

    def update(self, instance, validated_data):
        pass

    @transaction.atomic
    def create(self, validated_data):
        unique_code = validated_data.get("unique_code")

        unique_code.used = True
        unique_code.used_time = now()
        unique_code.save(update_fields=("used", "used_time",))

        records = []
        for item in validated_data.get("form_data", []):
            for record in item.get("questions", []):
                records.append(models.SurveyRecord(**record))

        models.SurveyRecord.objects.bulk_create(records)

        return {}
