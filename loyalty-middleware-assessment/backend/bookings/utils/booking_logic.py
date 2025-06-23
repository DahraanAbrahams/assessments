"""
Booking utility functions for loyalty booking flow.

Handles:
- Authentication header extraction
- Offer validation via Duffel
- Flight metadata extraction
- Booking response payload construction
"""

from datetime import datetime
from typing import Dict, Optional, Any, Tuple

from django.utils import timezone
from rest_framework.request import Request

from tenants.models import Tenant
from utils.exceptions import ProblemDetailException
from bookings.models import Booking
from flights.services.duffel import get_offer_by_id


def parse_auth_headers(request: Request, tenant: Tenant) -> Dict[str, str]:
    """
    Parse tenant-aware authentication headers from the request.

    Args:
        request (Request): The DRF request object.
        tenant (Tenant): The current tenant.

    Returns:
        Dict[str, str]: Parsed auth dictionary.
    """
    auth = {}
    headers = request.headers

    if "auth_header" in tenant.config:
        auth["api_key"] = headers.get(tenant.config["auth_header"])

    if "id_header" in tenant.config:
        value = headers.get(tenant.config["id_header"])
        auth["member_id"] = value
        auth["user_id"] = auth.get("user_id") or value

    if "user_id_header" in tenant.config and not auth.get("user_id"):
        auth["user_id"] = headers.get(tenant.config["user_id_header"])

    if "jwt_header" in tenant.config:
        jwt_value = headers.get(tenant.config["jwt_header"])
        if jwt_value and jwt_value.startswith("Bearer "):
            auth["jwt_token"] = jwt_value.split(" ", 1)[1]
        else:
            auth["jwt_token"] = jwt_value

    if "X-Mock-Eligibility" in headers:
        auth["mock_eligibility"] = headers["X-Mock-Eligibility"]

    auth["device_id"] = headers.get("X-FA-Device-ID")
    auth["session_id"] = headers.get("X-FA-Session-ID")

    if not auth.get("member_id"):
        auth["member_id"] = auth.get("user_id") or auth.get("customer_id")

    return auth


def validate_flight_offer(flight_id: str, path: str) -> Dict[str, Any]:
    """
    Fetch and validate a Duffel offer by flight ID.

    Args:
        flight_id (str): Duffel offer ID.
        path (str): API path for error context.

    Returns:
        Dict[str, Any]: The offer object.

    Raises:
        ProblemDetailException: If lookup fails or offer is missing.
    """
    try:
        offer = get_offer_by_id(flight_id)
        if not offer:
            raise ProblemDetailException(
                status=410,
                title="Offer Expired",
                detail="The selected flight offer is no longer available.",
                type_="https://api.loyalty-middleware.com/errors/offer-expired",
                instance=path,
            )
        return offer
    except ProblemDetailException:
        raise
    except Exception as e:
        raise ProblemDetailException(
            status=503,
            title="Offer Lookup Failed",
            detail=f"Could not fetch offer by ID: {str(e)}",
            type_="https://api.loyalty-middleware.com/errors/duffel-lookup-failure",
            instance=path,
        )


def extract_flight_metadata(offer: Dict[str, Any]) -> Tuple[str, str, Optional[datetime.date], Optional[datetime.date], str]:
    """
    Extract origin, destination, dates, and cabin class from Duffel offer.

    Args:
        offer (Dict[str, Any]): Duffel offer.

    Returns:
        Tuple[str, str, Optional[date], Optional[date], str]:
            - origin
            - destination
            - departure_date
            - return_date
            - cabin_class
    """
    slices = offer.get("slices", [])
    segments = slices[0].get("segments", []) if slices else []

    origin = segments[0]["origin"]["iata_code"] if segments else "UNKNOWN"
    destination = segments[-1]["destination"]["iata_code"] if segments else "UNKNOWN"
    departure_date = (
        datetime.fromisoformat(segments[0]["departing_at"].replace("Z", "+00:00")).date()
        if segments else None
    )

    return_date = None
    if len(slices) > 1 and slices[1].get("segments"):
        return_date = datetime.fromisoformat(
            slices[1]["segments"][0]["departing_at"].replace("Z", "+00:00")
        ).date()

    cabin_class = (
        slices[0].get("segments", [{}])[0]
        .get("passengers", [{}])[0]
        .get("cabin_class")
    )

    return origin, destination, departure_date, return_date, cabin_class


def build_booking_payload(
    booking: Booking,
    reference: str,
    serializer_data: Dict[str, Any],
    usd_equivalent: float,
    tenant: Tenant
) -> Dict[str, Any]:
    """
    Construct the final booking response payload.

    Args:
        booking (Booking): Saved booking instance.
        reference (str): Booking reference.
        serializer_data (dict): Validated booking input.
        usd_equivalent (float): USD equivalent of loyalty value.
        tenant (Tenant): Current tenant.

    Returns:
        Dict[str, Any]: Response data payload.
    """
    payload = {
        "booking_id": str(booking.id),
        "status": "pending_approval" if booking.status == "pending" else "confirmed",
        "tenant_id": tenant.slug,
        "member_id": booking.member_id,
        "flight": {
            "id": reference,
            "flight_number": booking.flight_number or "UA123",
            "departure": booking.departure_date.isoformat() + "T08:00:00Z",
            "arrival": (
                booking.return_date.isoformat() + "T11:30:00Z"
                if booking.return_date else "TBD"
            )
        },
        "passengers": [
            {
                "name": f"{p.get('first_name')} {p.get('last_name')}",
                "ticket_number": "0162345678901"
            } for p in serializer_data["passengers"]
        ],
        "payment": {
            "loyalty_amount": float(booking.amount),
            "loyalty_currency": booking.loyalty_currency,
            "usd_equivalent": float(usd_equivalent),
            "cashback": round(float(booking.amount) * tenant.get_cashback_rate(), 2)
            if tenant.get_cashback_rate() else None
        },
        "created_at": booking.created_at.isoformat(),
        "expires_at": (booking.created_at + timezone.timedelta(minutes=30)).isoformat()
    }

    if booking.status == "pending":
        payload.update({
            "approval_required": True,
            "approval_reason": "Booking exceeds approval threshold",
            "estimated_approval_time": "PT24H"
        })

    return payload
