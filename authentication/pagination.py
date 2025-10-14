from rest_framework import pagination
from rest_framework.response import Response


class CustomPagination(pagination.PageNumberPagination):
    page_size_query_param = 'limit'
    page_query_param = 'page'
    page_size = 10

    def get_paginated_response(self, data):
        return Response({
            'page': self.page.number,
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })