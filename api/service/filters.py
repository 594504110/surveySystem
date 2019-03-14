# -*- coding: utf-8 -*-


from rest_framework import filters


class CustomSearchFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        search = request.query_params.get("search")
        if search:
            return queryset.filter(name=search)
        else:
            return queryset
