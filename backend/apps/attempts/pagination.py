from rest_framework.pagination import PageNumberPagination


class AttemptPagination(PageNumberPagination):
    """
    Standard pagination for Attempt listing endpoints.
    Default page size is 20, max page size is 100.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
