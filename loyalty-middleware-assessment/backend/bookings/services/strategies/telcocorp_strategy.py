"""
TelcoCorp Loyalty Strategy Implementation.

Handles TelcoCorp-specific authentication (OAuth 2.0) and booking rules:
- Access token retrieval via client credentials.
- Loyalty balance check and point deduction via API.
- Restriction to economy class only.
"""

import requests
from django.conf import settings
from typing import Dict, Any

from tenants.models import Tenant
from utils.rfc7807 import (
    unauthorized_error,
    forbidden_error,
    service_unavailable_error,
)
from bookings.services.strategies.base_strategy import LoyaltyStrategy


class TelcoCorpStrategy(LoyaltyStrategy):
    """
    Loyalty strategy implementation for the TelcoCorp tenant.

    Manages OAuth 2.0 authentication, loyalty balance retrieval, point deductions,
    and enforces the business rule that only economy class bookings are allowed.

    Attributes:
        BASE_URL (str): Base URL for the TelcoCorp mock API.
        TOKEN_URL (str): Endpoint for acquiring access tokens.
    """

    BASE_URL = settings.TELCOCORP_API_URL
    TOKEN_URL = f"{BASE_URL}/oauth/token"

    def __init__(self, tenant: Tenant, config: Dict[str, Any], auth: Dict[str, str]) -> None:
        """
        Initialize the TelcoCorp strategy with tenant info and auth headers.

        Args:
            tenant (Tenant): The tenant making the request.
            config (Dict[str, Any]): Tenant configuration dictionary.
            auth (Dict[str, str]): Authentication values (e.g. customer ID).
        """
        super().__init__(tenant, config, auth)
        self._access_token = None

    def _headers(self) -> Dict[str, str]:
        """
        Constructs authenticated request headers including OAuth token.

        Optionally includes test headers like `X-Mock-Eligibility` for mock API simulation.

        Returns:
            Dict[str, str]: Request headers for TelcoCorp API.

        Raises:
            ProblemDetailException: If token acquisition fails.
        """
        headers = {
            "Authorization": f"Bearer {self._access_token or self._get_oauth_token()}",
            self.tenant.config["id_header"]: self.auth.get("member_id"),
        }

        # Optional: forward test header if passed (e.g. from test clients)
        if mock := self.auth.get("mock_eligibility"):
            headers["X-Mock-Eligibility"] = mock

        return headers

    def _get_oauth_token(self) -> str:
        """
        Retrieves a new OAuth 2.0 access token using client credentials.

        Returns:
            str: Bearer token for API requests.

        Raises:
            ProblemDetailException: If credentials are invalid or request fails.
        """
        try:
            response = requests.post(
                self.TOKEN_URL,
                json={
                    "grant_type": "client_credentials",
                    "client_id": self.tenant.config["client_id"],
                    "client_secret": self.tenant.config["client_secret"],
                },
                timeout=5,
            )
            if response.status_code == 401:
                raise unauthorized_error("Invalid client credentials", instance=self.TOKEN_URL)
            if not response.ok:
                try:
                    message = response.json().get("detail", "OAuth token fetch failed")
                except Exception:
                    message = response.text or "OAuth token fetch failed"
                raise service_unavailable_error(message, instance=self.TOKEN_URL)
            return response.json().get("access_token")
        except requests.RequestException:
            raise service_unavailable_error("Connection error while getting OAuth token", instance=self.TOKEN_URL)

    def get_balance(self) -> int:
        """
        Fetch the loyalty point balance for the customer.

        Returns:
            int: Available points in TelcoCorp account.

        Raises:
            ProblemDetailException: On auth or service failure.
        """
        customer_id = self.auth.get("member_id")
        url = f"{self.BASE_URL}/api/v2/customers/{customer_id}/points"
        try:
            response = requests.get(url, headers=self._headers(), timeout=5)
            if response.status_code == 401:
                raise unauthorized_error("Invalid or expired token", instance=url)
            if not response.ok:
                try:
                    message = response.json().get("detail", "Unable to retrieve TelcoCorp balance")
                except Exception:
                    message = response.text or "Unable to retrieve TelcoCorp balance"
                raise service_unavailable_error(message, instance=url)
            return response.json().get("balance", 0)
        except requests.RequestException:
            raise service_unavailable_error("Network error fetching TelcoCorp balance", instance=url)

    def deduct_points(self, amount: int) -> None:
        """
        Deducts loyalty points from the user's TelcoCorp account.

        Args:
            amount (int): Number of points to deduct.

        Raises:
            ProblemDetailException: On authentication or deduction failure.
        """
        customer_id = self.auth.get("member_id")
        reference_id = self.auth.get("reference")  # Must be set in self.auth
        url = f"{self.BASE_URL}/api/v2/customers/{customer_id}/points/use"

        if not reference_id:
            raise service_unavailable_error("Missing booking reference for deduction", instance=url)

        try:
            payload = {
                "points": amount,
                "reference_id": reference_id,
                "description": "Flight booking via loyalty middleware"
            }

            response = requests.post(url, json=payload, headers=self._headers(), timeout=5)

            if response.status_code == 403:
                raise forbidden_error("Insufficient balance", instance=url)
            if response.status_code == 401:
                raise unauthorized_error("Invalid or expired token", instance=url)
            if not response.ok:
                print(f"[DEBUG] Deduction failed: {response.status_code}, body={response.text}")
                try:
                    # Try to extract meaningful detail message
                    detail_json = response.json()
                    if isinstance(detail_json.get("detail"), dict):
                        message = detail_json["detail"].get("message", str(detail_json["detail"]))
                    else:
                        message = detail_json.get("detail", str(detail_json))
                except Exception:
                    message = response.text or "Point deduction failed"
                raise service_unavailable_error(detail=message, instance=url)

        except requests.RequestException:
            raise service_unavailable_error("Connection error during point deduction", instance=url)

    def requires_approval(self, amount: int, reference: str = None) -> bool:
        """
        Validates if the booking class is eligible (economy only for TelcoCorp).

        Args:
            amount (int): Loyalty amount for the booking (not used directly here).
            reference (str, optional): The booking reference, if available.

        Returns:
            bool: False (bookings are either accepted or forbidden, not pending).

        Raises:
            ProblemDetailException: If eligibility check fails or connection issues occur.
        """
        customer_id = self.auth.get("member_id")
        url = f"{self.BASE_URL}/api/v2/customers/{customer_id}/travel/eligibility"

        try:
            print(f"[DEBUG] Checking eligibility for cabin_class='economy', user_id={customer_id}")
            response = requests.get(url, headers=self._headers(), timeout=5)
            if response.status_code == 401:
                raise unauthorized_error("Invalid or expired token", instance=url)
            if not response.ok:
                try:
                    message = response.json().get("detail", "Eligibility check failed")
                except Exception:
                    message = response.text or "Eligibility check failed"
                raise service_unavailable_error(message, instance=url)

            eligible_classes = response.json().get("allowed_classes", [])
            print(f"[DEBUG] Eligible classes returned: {eligible_classes}")
            if "economy" not in eligible_classes:
                raise forbidden_error("TelcoCorp allows only economy class bookings", instance=url)
            return False
        except requests.RequestException:
            raise service_unavailable_error("Connection error during eligibility check", instance=url)

    def refund_points(self, amount: int) -> None:
        """
        Refund loyalty points to the user's account. (Currently unimplemented.)

        Args:
            amount (int): Points to refund.

        Raises:
            NotImplementedError: As refunds are not supported for TelcoCorp.
        """
        raise NotImplementedError("Refunds are not supported for TelcoCorp.")

    def authenticate(self, headers: Dict[str, str]) -> None:
        """
        No-op authentication for CoffeeChain (API key passed implicitly in headers).

        Args:
            headers (Dict[str, str]): Request headers from client.

        Raises:
            None
        """
        pass