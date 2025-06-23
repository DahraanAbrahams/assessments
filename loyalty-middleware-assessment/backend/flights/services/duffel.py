import logging
from typing import Dict, Any, List

import httpx
import requests
from decouple import config
from django.conf import settings

from utils.exceptions import ProblemDetailException
from utils.error_types import DUFFEL_TIMEOUT, DUFFEL_ERROR

logger = logging.getLogger(__name__)


def search_flights(search_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform a flight search using the Duffel API.

    This function sends a real-time request to Duffel's `offer_requests` endpoint
    using the provided search parameters. It supports round-trip logic and
    dynamically builds the passenger list.

    Args:
        search_params (Dict[str, Any]): A dictionary containing validated fields:
            - origin (str): Origin airport IATA code.
            - destination (str): Destination airport IATA code.
            - departure_date (date): Date of outbound flight.
            - return_date (date, optional): Date of return flight, if round trip.
            - passengers (Dict[str, int]): Dict of passenger counts (adults, children, infants).
            - cabin_class (str): Cabin class (e.g., economy).
            - currency (str): Desired currency code (e.g., "USD", "stars").

    Returns:
        Dict[str, Any]: The raw Duffel API JSON response.

    Raises:
        ProblemDetailException: RFC 7807-compliant error if the request fails or times out.
    """
    logger.info("Sending flight search request to Duffel with params: %s", search_params)

    slices = [
        {
            "origin": search_params["origin"],
            "destination": search_params["destination"],
            "departure_date": search_params["departure_date"].isoformat(),
        }
    ]

    if search_params.get("return_date"):
        slices.append({
            "origin": search_params["destination"],
            "destination": search_params["origin"],
            "departure_date": search_params["return_date"].isoformat(),
        })

    payload = {
        "slices": slices,
        "cabin_class": search_params["cabin_class"],
        "passengers": _build_passengers_for_duffel(search_params["passengers"]),
        "currency": search_params["currency"],
        "max_connections": 1,
    }

    try:
        client = httpx.Client(
            base_url=config("DUFFEL_API_URL"),
            headers={
                "Authorization": f"Bearer {config('DUFFEL_API_KEY')}",
                "Duffel-Version": config("DUFFEL_API_VERSION", default="v2"),
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=15.0,
        )

        response = client.post("/offer_requests?return_offers=true", json={"data": payload})
        response.raise_for_status()

        logger.info("Duffel flight search successful with status code: %d", response.status_code)
        return response.json()

    except httpx.TimeoutException:
        logger.exception("Duffel API request timed out")
        raise ProblemDetailException(
            type_=DUFFEL_TIMEOUT,
            title="Duffel Timeout",
            status=504,
            detail="Flight search timed out while contacting Duffel.",
            instance="/flights/search",
        )

    except httpx.HTTPStatusError as e:
        logger.error("Duffel responded with HTTP error %d: %s", e.response.status_code, e.response.text)
        raise ProblemDetailException(
            type_=DUFFEL_ERROR,
            title="Duffel API Error",
            status=502,
            detail="Duffel API responded with an error.",
            instance="/flights/search",
            extra={"duffel_status": e.response.status_code, "message": e.response.text},
        )


def get_offer_by_id(offer_id: str) -> dict:
    """
    Fetch a specific flight offer from Duffel using the offer ID.

    Args:
        offer_id (str): The Duffel offer ID to retrieve.

    Returns:
        dict: Offer details from Duffel.

    Raises:
        ProblemDetailException: On request failure or 404 Not Found.
    """
    base_url = getattr(settings, "DUFFEL_API_URL", "https://api.duffel.com/air")
    token = getattr(settings, "DUFFEL_API_KEY", None)
    print(f"[Duffel] Fetching offer: {offer_id}")
    print(f"[Duffel] API Token (truncated): {token[:6]}...")

    if not token:
        raise ProblemDetailException(
            status=500,
            title="Duffel Token Missing",
            detail="DUFFEL_API_KEY is not configured in settings.",
            type_="https://api.loyalty-middleware.com/errors/misconfigured-duffel-token",
            instance=f"{base_url}/offers/{offer_id}"
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Duffel-Version": getattr(settings, "DUFFEL_API_VERSION", "v2"),
    }

    url = f"{base_url}/offers/{offer_id}"
    print(f"[Duffel] URL: {url}")


    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"[Duffel] Response status: {response.status_code}")
        print(f"[Duffel] Response body: {response.text}")
        if response.status_code == 404:
            raise ProblemDetailException(
                status=410,
                title="Offer Expired or Invalid",
                detail=f"No offer found for ID '{offer_id}'. It may have expired or been removed.",
                type_="https://api.loyalty-middleware.com/errors/offer-not-found",
                instance=url
            )

        response.raise_for_status()
        return response.json().get("data", {})

    except requests.exceptions.RequestException as e:
        raise ProblemDetailException(
            status=503,
            title="Duffel API Error",
            detail=f"Error contacting Duffel: {str(e)}",
            type_="https://api.loyalty-middleware.com/errors/duffel-api",
            instance=url,
        )


def _build_passengers_for_duffel(counts: Dict[str, int]) -> List[Dict[str, str]]:
    """
    Convert internal passenger count structure into Duffel-compatible format.

    Args:
        counts (Dict[str, int]): Dictionary like {"adults": 2, "children": 1}.

    Returns:
        List[Dict[str, str]]: List of passenger type dicts, e.g., [{"type": "adult"}, ...].
    """
    types = {"adults": "adult", "children": "child", "infants": "infant"}
    passengers = []

    for label, type_ in types.items():
        for _ in range(counts.get(label, 0)):
            passengers.append({"type": type_})

    logger.debug("Constructed %d passenger(s) for Duffel request", len(passengers))
    return passengers
