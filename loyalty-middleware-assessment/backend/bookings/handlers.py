from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage
from django.utils.dateparse import parse_date
from drf_yasg.utils import swagger_auto_schema

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request

from bookings.models import Booking
from bookings.serializers import BookingDetailSerializer, BookingCreateSerializer
from bookings.services.strategies.resolver import get_loyalty_strategy
from bookings.utils.booking_logic import build_booking_payload, validate_flight_offer, extract_flight_metadata, \
    parse_auth_headers
from bookings.utils.generate_ref import generate_booking_reference
from utils.docs.swagger_headers import TENANT_HEADERS
from utils.exceptions import ProblemDetailException
from utils.rfc7807 import validation_error, not_found_error, service_unavailable_error


class BookingHandler(APIView):
    """
    Handles loyalty flight bookings for the current tenant.

    Supports:
        - GET: List bookings with optional filters and pagination.
        - POST: Create a booking using live Duffel offer verification and tenant-specific rules.
    """

    def get_queryset(self, request: Request):
        """
        Retrieve bookings scoped to the current tenant, applying optional filters.

        Args:
            request (Request): The HTTP request with tenant context.

        Returns:
            QuerySet[Booking]: Filtered queryset of bookings.
        """
        tenant = request.tenant
        qs = Booking.objects.filter(tenant=tenant).order_by("-created_at")

        status_filter = request.query_params.get("status")
        from_date = parse_date(request.query_params.get("from_date") or "")
        to_date = parse_date(request.query_params.get("to_date") or "")

        if status_filter:
            qs = qs.filter(status=status_filter)
        if from_date:
            qs = qs.filter(created_at__date__gte=from_date)
        if to_date:
            qs = qs.filter(created_at__date__lte=to_date)

        return qs

    @swagger_auto_schema(
        operation_description="Create a booking using a Duffel offer.",
        request_body=BookingCreateSerializer,
        responses={201: "Created", 400: "Validation error"},
        manual_parameters=TENANT_HEADERS,
    )
    def get(self, request: Request) -> Response:
        """
        List bookings for the tenant with optional filters and pagination.

        Query Parameters:
            - status (str, optional): Filter by booking status.
            - from_date (str, optional): Filter bookings created after this date.
            - to_date (str, optional): Filter bookings created before this date.
            - limit (int, optional): Number of records per page (default: 20, max: 100).
            - offset (int, optional): Pagination offset (default: 0).

        Args:
            request (Request): DRF request object.

        Returns:
            Response: Paginated list of bookings or validation error.
        """
        qs = self.get_queryset(request)

        try:
            limit = min(int(request.query_params.get("limit", 20)), 100)
            offset = int(request.query_params.get("offset", 0))
        except ValueError:
            return validation_error(
                detail="Invalid pagination parameters.",
                instance=request.path,
            )

        paginator = Paginator(qs, limit)
        try:
            page = paginator.page((offset // limit) + 1)
        except EmptyPage:
            page = []

        serializer = BookingDetailSerializer(page, many=True)
        return Response({
            "data": {
                "bookings": serializer.data,
                "pagination": {
                    "total": paginator.count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": page.has_next() if page else False,
                }
            }
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create a booking using a Duffel offer.",
        request_body=BookingCreateSerializer,
        responses={201: "Created", 400: "Validation error"},
        manual_parameters=TENANT_HEADERS,
    )
    def post(self, request: Request) -> Response:
        """
        Create a loyalty booking based on a Duffel offer.

        The request must include a valid Duffel `flight_id` (offer ID).
        This handler will:
            - Validate payload.
            - Fetch offer live from Duffel using ID.
            - Validate tenant cabin class permissions.
            - Apply loyalty business logic (deduct, approve, refund).
            - Create and return booking record.

        Args:
            request (Request): DRF request with tenant context.

        Returns:
            Response: Booking confirmation payload or RFC 7807 error.
        """
        tenant = request.tenant
        data = request.data.copy()
        data["tenant_id"] = tenant.id

        auth = parse_auth_headers(request, tenant)
        print(f"DEBUG: Auth Dict: {auth}")
        print("HEADERS IN:", dict(request.headers))

        strategy = get_loyalty_strategy(tenant, auth)

        serializer = BookingCreateSerializer(data=data, context={"request": request})
        if not serializer.is_valid():
            return validation_error(
                detail="Invalid booking payload.",
                instance=request.path,
                extra={"errors": serializer.errors},
            )

        flight_id = serializer.validated_data["flight_id"]
        print(f"[BookingHandler] Looking up flight ID: {flight_id}")
        offer = validate_flight_offer(flight_id, request.path)

        origin, destination, departure_date, return_date, cabin_class = extract_flight_metadata(offer)

        if not tenant.is_valid_cabin_class(cabin_class):
            return validation_error(
                detail=f"Cabin class '{cabin_class}' is not allowed for tenant '{tenant.slug}'.",
                instance=request.path,
            )

        raw_amount = serializer.validated_data["payment"]["amount"]
        amount = strategy.apply_cashback(raw_amount)
        loyalty_amount = int(round(amount, 2))

        member_id = auth.get("member_id") or auth.get("user_id") or auth.get("customer_id")
        reference = generate_booking_reference(member_id)
        auth["reference"] = reference

        try:
            with transaction.atomic():
                booking_status = (
                    "pending" if strategy.requires_approval(loyalty_amount, reference=reference)
                    else "confirmed"
                )

                booking = Booking.objects.create(
                    tenant=tenant,
                    member_id=member_id,
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date,
                    cabin_class=cabin_class,
                    num_passengers=len(serializer.validated_data["passengers"]),
                    amount=amount,
                    loyalty_currency=serializer.validated_data["payment"]["currency"],
                    reference=reference,
                    status=booking_status,
                )

                if booking_status == "confirmed":
                    strategy.deduct_points(loyalty_amount)

                usd_equivalent = strategy.to_usd(amount)

        except ProblemDetailException as e:
            raise e
        except Exception as e:
            return service_unavailable_error(str(e), instance=request.path)

        response_payload = build_booking_payload(
            booking=booking,
            reference=reference,
            serializer_data=serializer.validated_data,
            usd_equivalent=usd_equivalent,
            tenant=tenant
        )

        return Response({"data": response_payload}, status=status.HTTP_201_CREATED)


class BookingDetailHandler(APIView):
    """
    Retrieve details of a specific booking by ID, scoped to the tenant.
    """

    @swagger_auto_schema(
        operation_description="Create a booking using a Duffel offer.",
        request_body=BookingCreateSerializer,
        responses={201: "Created", 400: "Validation error"},
        manual_parameters=TENANT_HEADERS,
    )
    def get(self, request: Request, booking_id: int) -> Response:
        """
        Get booking detail for a specific ID under the current tenant.

        Args:
            request (Request): DRF request object.
            booking_id (int): ID of the booking to retrieve.

        Returns:
            Response: Serialized booking detail or not found error.
        """
        tenant = request.tenant
        try:
            booking = Booking.objects.get(id=booking_id, tenant=tenant)
        except Booking.DoesNotExist:
            return not_found_error(
                detail=f"Booking with ID '{booking_id}' not found",
                instance=request.path,
            )

        serializer = BookingDetailSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BookingCancelHandler(APIView):
    """
    Cancel a booking and optionally process a tenant-specific refund.
    """

    @swagger_auto_schema(
        operation_description="Create a booking using a Duffel offer.",
        request_body=BookingCreateSerializer,
        responses={201: "Created", 400: "Validation error"},
        manual_parameters=TENANT_HEADERS,
    )
    def post(self, request: Request, booking_id: int) -> Response:
        """
        Cancel the specified booking and issue a refund if requested.

        Request Body:
            - reason (str, optional): Reason for cancellation.
            - refund_requested (bool): Whether a refund should be processed.

        Args:
            request (Request): DRF request object.
            booking_id (int): ID of the booking to cancel.

        Returns:
            Response: Cancellation confirmation and refund info if applicable.
        """
        tenant = request.tenant
        try:
            booking = Booking.objects.get(id=booking_id, tenant=tenant)
        except Booking.DoesNotExist:
            return not_found_error(
                detail=f"Booking with ID '{booking_id}' not found",
                instance=request.path,
            )

        if booking.status == "cancelled":
            return validation_error(
                detail="Booking is already cancelled.",
                instance=request.path,
            )

        payload = request.data
        refund_requested = payload.get("refund_requested", False)

        if not isinstance(refund_requested, bool):
            return validation_error(
                detail="Field `refund_requested` must be a boolean.",
                instance=request.path,
            )

        # Optional reason handling
        cancel_reason = payload.get("reason")
        if cancel_reason and hasattr(booking, "cancel_reason"):
            booking.cancel_reason = cancel_reason

        # Mark as cancelled
        booking.status = "cancelled"
        booking.cancelled_at = timezone.now()

        # Attempt refund
        if refund_requested:
            try:
                auth = parse_auth_headers(request, tenant)
                strategy = get_loyalty_strategy(tenant, auth)
                strategy.refund_points(booking.amount)

                booking.refund_status = "processed"
                booking.refund_amount = booking.amount
                booking.refund_processed_at = timezone.now()

            except NotImplementedError:
                # Refund not implemented — skip silently
                pass
            except ProblemDetailException as e:
                raise e
            except Exception as e:
                return service_unavailable_error(
                    detail="Unexpected error during refund",
                    instance=request.path,
                )

        booking.save()

        response = {
            "data": {
                "booking_id": booking.id,
                "status": "cancelled",
                "cancelled_at": booking.cancelled_at.isoformat(),
            }
        }

        if refund_requested and booking.refund_status == "processed":
            refund_amount = float(booking.refund_amount)
            response["data"]["refund"] = {
                "status": "processed",
                "loyalty_amount": refund_amount,
                "loyalty_currency": booking.loyalty_currency,
                "fee": 0,
                "net_refund": refund_amount,
                "processed_at": booking.refund_processed_at.isoformat(),
            }

        return Response(response, status=status.HTTP_200_OK)


class BookingSearchHandler(APIView):
    """
    Search bookings for a tenant by partial match on member ID.
    """

    @swagger_auto_schema(
        operation_description="Create a booking using a Duffel offer.",
        request_body=BookingCreateSerializer,
        responses={201: "Created", 400: "Validation error"},
        manual_parameters=TENANT_HEADERS,
    )
    def get(self, request: Request) -> Response:
        """
        Perform a substring search for bookings by `member_id`.

        Query Parameters:
            - q (str): Substring to search for in member IDs.

        Args:
            request (Request): DRF request object.

        Returns:
            Response: Matching bookings or validation error.
        """
        tenant = request.tenant
        query = request.query_params.get("q", "").strip()

        if not query:
            return validation_error(
                detail="Query parameter 'q' is required for search.",
                instance=request.path,
            )

        bookings = Booking.objects.filter(
            tenant=tenant,
            member_id__icontains=query
        ).order_by("-created_at")

        serializer = BookingDetailSerializer(bookings, many=True)
        return Response({"data": {"results": serializer.data}}, status=status.HTTP_200_OK)
