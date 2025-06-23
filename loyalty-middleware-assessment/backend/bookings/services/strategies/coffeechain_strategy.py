"""
CoffeeChain Loyalty Strategy Implementation.

Defines the loyalty integration logic for CoffeeChain, including:
- API authentication using API key and member ID.
- Balance retrieval and deduction via CoffeeChain's mock API.
- Approval checks based on loyalty point thresholds.
"""

import requests
from django.conf import settings
from typing import Dict, Any

from requests import RequestException

from tenants.models import Tenant
from utils.rfc7807 import unauthorized_error, forbidden_error, service_unavailable_error
from bookings.services.strategies.base_strategy import LoyaltyStrategy


class CoffeeChainStrategy(LoyaltyStrategy):
    """
    Loyalty strategy implementation for the CoffeeChain tenant.

    This strategy handles authentication via API key and member ID, performs
    point deductions, and checks whether approval is required for high-value bookings.

    Attributes:
        BASE_URL (str): Base URL for CoffeeChain's loyalty API (configured via Django settings).
    """

    BASE_URL = settings.COFFEECHAIN_API_URL

    def __init__(self, tenant: Tenant, config: Dict[str, Any], auth: Dict[str, str]) -> None:
        """
        Initialize the CoffeeChain strategy with tenant data and authentication headers.

        Args:
            tenant (Tenant): The current tenant instance.
            config (Dict[str, Any]): Configuration dictionary from the tenant model.
            auth (Dict[str, str]): Parsed authentication values (e.g. API key, member ID).
        """
        super().__init__(tenant, config, auth)

    def _headers(self) -> Dict[str, str]:
        """
        Constructs the required authentication headers for API calls.

        Returns:
            Dict[str, str]: Dictionary containing API key and member ID headers.
        """
        return {
            self.tenant.config["auth_header"]: self.auth.get("api_key"),
            self.tenant.config["id_header"]: self.auth.get("member_id"),
        }

    def get_balance(self) -> int:
        """
        Retrieve the current loyalty balance for the member from CoffeeChain.

        Returns:
            int: The member's current balance in loyalty stars.

        Raises:
            ProblemDetailException: If authentication fails or the API is unreachable.
        """
        url = f"{self.BASE_URL}/api/v1/members/{self.auth['member_id']}/balance"
        try:
            response = requests.get(url, headers=self._headers(), timeout=5)
            if response.status_code == 401:
                raise unauthorized_error("Invalid API key or member ID", instance=url)
            if not response.ok:
                try:
                    message = response.json().get("detail", response.text or "Unable to fetch balance")
                except Exception:
                    message = response.text or "Unable to fetch balance"
                raise service_unavailable_error(message, instance=url)
            return response.json().get("balance", 0)
        except requests.RequestException:
            raise service_unavailable_error("Connection error while fetching CoffeeChain balance", instance=url)

    def deduct_points(self, amount: int, reference: str = None, description: str = None) -> None:
        """
        Deduct loyalty stars from the member's account for a booking.

        Args:
            amount (int): Number of loyalty stars to deduct.
            reference (str): Booking reference ID.
            description (str): Description for the deduction.

        Raises:
            ProblemDetailException: On deduction failure or API/network issues.
        """
        url = f"{self.BASE_URL}/api/v1/members/{self.auth['member_id']}/deduct"

        payload = {
            "reference_id": reference or "undefined-ref",
            "description": description or f"Flight booking for member {self.auth.get('member_id', 'unknown')}",
            "amount": amount
        }

        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=5)
            if response.status_code == 403:
                raise forbidden_error("Insufficient balance", instance=url)
            if response.status_code == 401:
                raise unauthorized_error("Invalid API key or member ID", instance=url)
            if not response.ok:
                try:
                    message = response.json().get("detail", response.text or "Failed to deduct points")
                except Exception:
                    message = response.text or "Failed to deduct points"
                raise service_unavailable_error(message, instance=url)
        except requests.RequestException:
            raise service_unavailable_error("Connection error during point deduction", instance=url)

    def requires_approval(self, amount: int, reference: str = None) -> bool:
        """
        Determine whether this booking amount exceeds the approval threshold.

        Args:
            amount (int): Loyalty amount in stars.
            reference (str, optional): The booking reference, if available.

        Returns:
            bool: True if approval is required, False otherwise.

        Raises:
            RuntimeError: If the approval check fails or cannot be reached.
        """
        threshold = self.tenant.config.get("approval_threshold", 50000)
        if amount <= threshold:
            return False

        url = f"{self.BASE_URL}/api/v1/approvals/check"
        payload = {
            "member_id": self.auth.get("member_id"),
            "amount": amount,
            "booking_reference": reference or "undefined-ref"
        }

        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=5)
            if not response.ok:
                raise RuntimeError(f"Approval check failed with status {response.status_code}: {response.text}")
            return response.json().get("approval_required", False)
        except RequestException as e:
            raise RuntimeError(f"Connection error during approval check: {e}")

    def refund_points(self, amount: int) -> None:
        """
        Refunds loyalty points to a CoffeeChain member's account.

        Args:
            amount (int): Number of points to refund.

        Raises:
            ProblemDetailException: If the refund fails due to auth issues or service error.
        """
        member_id = self.auth.get("member_id")
        url = f"{self.BASE_URL}/api/v1/members/{member_id}/refund"

        try:
            response = requests.post(
                url,
                json={"amount": int(amount)},
                headers=self._headers(),
                timeout=5
            )
            if response.status_code == 401:
                raise unauthorized_error("Invalid API key or member ID", instance=url)
            if not response.ok:
                raise service_unavailable_error("Refund failed for CoffeeChain", instance=url)
        except requests.RequestException:
            raise service_unavailable_error("Network error during CoffeeChain refund", instance=url)

    def authenticate(self, headers: Dict[str, str]) -> None:
        """
        No-op authentication for CoffeeChain (API key passed implicitly in headers).

        Args:
            headers (Dict[str, str]): Request headers from client.

        Raises:
            None
        """
        pass

