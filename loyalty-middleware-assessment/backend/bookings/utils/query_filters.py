from django.core.paginator import Paginator, EmptyPage
from django.utils.dateparse import parse_date
from rest_framework.request import Request


def filter_and_paginate_bookings(queryset, request: Request, max_limit=100, default_limit=20):
    """
    Apply filtering and pagination to a Booking queryset based on query parameters.

    Args:
        queryset (QuerySet): Initial Booking queryset.
        request (Request): DRF request object with query parameters.
        max_limit (int, optional): Maximum allowed page size. Defaults to 100.
        default_limit (int, optional): Default number of results per page. Defaults to 20.

    Returns:
        tuple:
            - page (list): Paginated list of bookings.
            - metadata (dict): Metadata for pagination (total, limit, offset, has_more).
    """
    tenant_slug = request.query_params.get("tenant")
    status_filter = request.query_params.get("status")
    from_date = parse_date(request.query_params.get("from_date", ""))
    to_date = parse_date(request.query_params.get("to_date", ""))

    if tenant_slug:
        queryset = queryset.filter(tenant__slug=tenant_slug)
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if from_date:
        queryset = queryset.filter(created_at__date__gte=from_date)
    if to_date:
        queryset = queryset.filter(created_at__date__lte=to_date)

    try:
        limit = min(int(request.query_params.get("limit", default_limit)), max_limit)
        offset = int(request.query_params.get("offset", 0))
    except ValueError:
        return None, {"error": "Invalid pagination parameters."}

    paginator = Paginator(queryset, limit)
    try:
        page = paginator.page((offset // limit) + 1)
    except EmptyPage:
        page = []

    metadata = {
        "total": paginator.count,
        "limit": limit,
        "offset": offset,
        "has_more": page.has_next() if page else False,
    }

    return page, metadata
