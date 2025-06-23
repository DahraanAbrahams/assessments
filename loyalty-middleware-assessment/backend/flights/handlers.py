from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request

from flights.serializers import FlightSearchRequestSerializer
from flights.services.duffel import search_flights
from utils.docs.swagger_headers import TENANT_HEADERS
from utils.rfc7807 import validation_error, internal_server_error


class FlightSearchHandler(APIView):
    """
    Tenant-aware API endpoint for searching flights via Duffel.

    Validates incoming request data, delegates the search logic to Duffel,
    and returns the available flight offers in a structured response.

    Middleware is expected to attach a `request.tenant` object before this handler is called.
    """

    @swagger_auto_schema(
        operation_description="Search for flights using Duffel.",
        request_body=FlightSearchRequestSerializer,
        responses={200: "OK", 400: "Validation error"},
        manual_parameters=TENANT_HEADERS,
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Handle POST /api/v1/flights/search

        This endpoint accepts validated search parameters, queries Duffel,
        and returns available offers (flights). All errors follow RFC 7807.

        Request Headers:
            - X-Tenant-ID: required (processed by middleware)
            - Authorization / API Key: enforced by middleware per tenant config

        Request Body (JSON):
            {
                "origin": "CPT",
                "destination": "JNB",
                "departure_date": "2025-07-01",
                "return_date": "2025-07-10",
                "passengers": { "adults": 1 },
                "cabin_class": "economy",
                "currency": "USD"
            }

        Returns:
            200 OK: { "offers": [...] }
            400 Bad Request: Validation errors (RFC 7807)
            500 Internal Server Error: Duffel or logic failure (RFC 7807)
        """
        if not hasattr(request, "tenant"):
            return internal_server_error(
                detail="Missing tenant context on request. Ensure TenantMiddleware is active.",
                instance=request.path,
            )

        serializer = FlightSearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return validation_error(
                detail="Invalid flight search payload.",
                instance=request.path,
                extra={"errors": serializer.errors},
            )

        try:
            result = search_flights(serializer.validated_data)
            offers = result.get("data", {}).get("offers", [])
        except Exception as e:
            return internal_server_error(
                detail=f"Failed to fetch flight offers: {str(e)}",
                instance=request.path,
            )

        return Response({"offers": offers}, status=status.HTTP_200_OK)
