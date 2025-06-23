"""
Module: swagger_query_params.py

This module defines reusable OpenAPI query parameters for Swagger documentation,
specifically for the booking list API endpoints.

These parameters are intended to be included using `manual_parameters` in
drf_yasg's `@swagger_auto_schema` decorators, allowing for cleaner and more
maintainable Swagger docs across tenant and admin booking views.
"""

from drf_yasg import openapi

# A list of OpenAPI query parameters used for filtering booking lists.
#
# Includes:
# - status: Filter by booking status.
# - from_date: Start date for booking creation.
# - to_date: End date for booking creation.
#
# These parameters can be used with:
# - GET /api/bookings/
# - GET /api/admin/bookings/
BOOKING_QUERY_PARAMS = [
    openapi.Parameter(
        name="status",
        in_=openapi.IN_QUERY,
        description="Filter bookings by status (e.g. confirmed, cancelled)",
        type=openapi.TYPE_STRING,
        required=False
    ),
    openapi.Parameter(
        name="from_date",
        in_=openapi.IN_QUERY,
        description="Start date for booking creation (YYYY-MM-DD)",
        type=openapi.TYPE_STRING,
        format="date",
        required=False
    ),
    openapi.Parameter(
        name="to_date",
        in_=openapi.IN_QUERY,
        description="End date for booking creation (YYYY-MM-DD)",
        type=openapi.TYPE_STRING,
        format="date",
        required=False
    ),
]

SEARCH_QUERY_PARAM = [
    openapi.Parameter(
        name="q",
        in_=openapi.IN_QUERY,
        description="Substring to match against member IDs",
        type=openapi.TYPE_STRING,
        required=True,
    )
]