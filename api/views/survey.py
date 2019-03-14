# -*- coding: utf-8 -*-

from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
# from rest_framework.pagination import LimitOffsetPagination

from web import models

from ..serializers import survey
from ..service.pagination import CustomLimitOffsetPagination


# from ..service import filters


# 获取问卷调查列表
class SurveyApi(generics.ListAPIView):
    # 针对问卷调查模型
    queryset = models.MiddleSurvey.objects.all()
    # 序列化器
    serializer_class = survey.SurveySerializer
    # 过滤器
    filter_backends = (SearchFilter, OrderingFilter,)
    # 搜索的字段
    search_fields = ('name', 'by_zone__name')
    # 排序的字段
    ordering_fields = ('name', 'by_zone',)
    # 分页器
    pagination_class = CustomLimitOffsetPagination

    fields = (
        {
            "prop": "name",
            "label": "名称"
        },
        {
            "prop": "by_zone",
            "label": "地区名称"
        },
        {
            "prop": "count",
            "label": "填写人数"
        },
        {
            "prop": "link",
            "label": "填写连接"
        },
        {
            "prop": "date",
            "label": "日期"
        },
        {
            "prop": "handle",
            "label": "操作"
        },
    )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = self.get_paginated_response(serializer.data)
            ordering = self.request.query_params.get("ordering")
            results = data["results"]

            if ordering.startswith("-"):
                reverse = True
                ordering = ordering[1:]
            else:
                reverse = False

            if ordering in [item["prop"] for item in self.fields]:
                results = sorted(results, key=lambda item: item[ordering], reverse=reverse)

            data["results"] = results

            return Response({
                "fields": self.fields,
                "data": data
            })

        serializer = self.get_serializer(queryset, many=True, fields=(item["prop"] for item in self.fields))
        return Response({
            "fields": self.fields,
            "data": serializer.data
        })


# 获取问卷调查详情
class SurveyDetailApi(generics.RetrieveAPIView, generics.CreateAPIView):
    queryset = models.MiddleSurvey.objects.all()

    def get_serializer_class(self):
        """
        获取序列化器
        :return: class
        """
        if self.request.method == "GET":
            return survey.MiddleSurveyDetailSerializer
        else:
            return survey.SurveyCreateSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({"status": True})
        else:
            error = serializer.errors
            return Response({"status": False, "errors": error})
