# -*- coding: utf-8 -*-


from collections import OrderedDict

from rest_framework import pagination


class CustomLimitOffsetPagination(pagination.LimitOffsetPagination):
    default_limit = 2

    def get_paginated_response(self, data):
        return OrderedDict([
            ('count', self.count),
            ('page_size', self.default_limit),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ])
