from rest_framework import pagination
from rest_framework.response import Response


# class CustomPagination(pagination.PageNumberPagination):

page_size = 2


def get_paginated_response(self, data):
    return Response({
        'links': {
            'next_page': self.get_next_link(),
            'previous_page': self.get_previous_link(),
        },
        'count': self.page.paginator.count,
        'result': data
    })


class AlertCursorPagination(pagination.CursorPagination):
    page_size = 2
    ordering = '-created_at'
    cursor_query_param = 'cursor'
