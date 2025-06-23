from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bookings.admin.serializers import AdminBookingSerializer
from bookings.models import Booking
from bookings.serializers import BookingDetailSerializer
from bookings.utils.query_filters import filter_and_paginate_bookings
from utils.docs.swagger_headers import TENANT_HEADERS
from utils.docs.swagger_query_params import BOOKING_QUERY_PARAMS
from utils.rfc7807 import not_found_error


from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from bookings.models import Booking
from bookings.admin.serializers import AdminBookingSerializer
from bookings.utils.query_filters import filter_and_paginate_bookings
from utils.docs.swagger_query_params import BOOKING_QUERY_PARAMS
from utils.rfc7807 import validation_error


class AdminBookingListHandler(APIView):
    """
    Admin handler for listing bookings across all tenants.

    This endpoint supports filtering and pagination:

    Filters:
        - tenant (slug): Filter by tenant slug.
        - status (str): Filter by booking status.
        - from_date (YYYY-MM-DD): Filter bookings created on or after this date.
        - to_date (YYYY-MM-DD): Filter bookings created on or before this date.

    Pagination:
        - limit (int): Number of records per page (default: 20, max: 100).
        - offset (int): Offset for paginated results (default: 0).

    Example:
        GET /api/v1/admin/bookings/?tenant=coffeechain&status=confirmed&limit=10&offset=0
    """

    @swagger_auto_schema(
        operation_description="List all bookings across all tenants with optional filters and pagination.",
        manual_parameters=BOOKING_QUERY_PARAMS,
        responses={200: "OK", 400: "Validation error"}
    )
    def get(self, request):
        """
        Retrieve a paginated list of bookings across all tenants, with optional filtering.

        Args:
            request (Request): DRF request object with query parameters.

        Returns:
            Response: JSON response containing bookings and pagination metadata.
        """
        base_queryset = Booking.objects.select_related("tenant").all()
        page, metadata = filter_and_paginate_bookings(base_queryset, request)

        if page is None:
            validation_error(
                detail=metadata["error"],
                instance=request.path,
            )

        serializer = AdminBookingSerializer(page, many=True)
        return Response(
            {
                "data": {
                    "bookings": serializer.data,
                    "pagination": metadata,
                }
            },
            status=status.HTTP_200_OK,
        )


class AdminBookingDetailHandler(APIView):
    """
    Retrieve detailed information about a specific booking (admin/global scope).

    This handler is intended for admin-level access across all tenants and supports:
        - Global lookup by booking ID
        - Full metadata including tenant info
    """

    @swagger_auto_schema(
        operation_description="Retrieve a single booking by ID (admin scope).",
        manual_parameters=TENANT_HEADERS,
        responses={
            200: BookingDetailSerializer,
            404: "Booking not found"
        }
    )
    def get(self, request, booking_id: int) -> Response:
        """
        Get details for a specific booking across all tenants.

        Args:
            request (Request): DRF request object.
            booking_id (int): Internal booking ID.

        Returns:
            Response: JSON representation of the booking or 404 if not found.
        """
        try:
            booking = Booking.objects.select_related("tenant").get(id=booking_id)
        except Booking.DoesNotExist:
            not_found_error(
                detail=f"Booking with ID {booking_id} not found.",
                instance=request.path,
            )

        serializer = BookingDetailSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)