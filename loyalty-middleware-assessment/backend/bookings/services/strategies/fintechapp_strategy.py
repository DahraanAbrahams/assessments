"""
FintechApp Loyalty Strategy Implementation.

Handles FintechApp-specific logic for authentication (JWT),
loyalty balance management, and applies a 2% cashback on bookings.
"""

import requests
from django.conf import settings
from typing import Dict, Any, Optional

from tenants.models import Tenant
from utils.exceptions import ProblemDetailException
from utils.rfc7807 import (
    unauthorized_error,
    forbidden_error,
    service_unavailable_error,
)
from bookings.services.strategies.base_strategy import LoyaltyStrategy


class FintechAppStrategy(LoyaltyStrategy):
    """
    Loyalty strategy implementation for the FintechApp tenant.

    This strategy authenticates using a JWT token and user ID,
    fetches and deducts coin balances, and applies 2% cashback on all bookings.

    Attributes:
        BASE_URL (str): Base URL for the FintechApp mock API.
    """

    BASE_URL = settings.FINTECHAPP_API_URL

    def __init__(self, tenant: Tenant, config: Dict[str, Any], auth: Dict[str, str]) -> None:
        """
        Initialize the FintechApp strategy.

        Args:
            tenant (Tenant): The tenant making the request.
            config (Dict[str, Any]): Tenant-specific configuration.
            auth (Dict[str, str]): Authentication context (JWT token, user ID).
        """
        super().__init__(tenant, config, auth)
        self.token = auth.get("jwt_token")

    def _headers(self) -> Dict[str, str]:
        """
        Constructs authenticated headers using JWT, user ID, and device ID.

        Returns:
            Dict[str, str]: Request headers for FintechApp APIs.
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            self.tenant.config["id_header"]: self.auth.get("user_id"),
        }
        if device_id := self.auth.get("device_id"):
            headers["X-FA-Device-ID"] = device_id
        return headers

    def get_balance(self) -> int:
        """
        Retrieve the user's current loyalty coin balance.

        Returns:
            int: Current available coins.

        Raises:
            ProblemDetailException: On auth failure or service error.
        """
        self.validate_jwt()
        user_id = self.auth.get("user_id")
        url = f"{self.BASE_URL}/api/v1/users/{user_id}/coins"

        try:
            response = requests.get(url, headers=self._headers(), timeout=5)
            if response.status_code == 401:
                raise unauthorized_error("Invalid JWT token or user ID", instance=url)
            if not response.ok:
                raise service_unavailable_error("Unable to fetch FintechApp balance", instance=url)
            return response.json().get("balance", 0)
        except requests.RequestException:
            raise service_unavailable_error("Connection error while fetching FintechApp balance", instance=url)

    def deduct_points(self, amount: int, reference: Optional[str] = None, description: Optional[str] = None) -> None:
        """
        Deduct coins from the user's FintechApp balance.

        Args:
            amount (int): Amount of coins to deduct.
            reference (str, optional): Booking reference (ignored for FintechApp).
            description (str, optional): Description (ignored for FintechApp).
        """
        self.validate_jwt()
        user_id = self.auth.get("user_id")
        url = f"{self.BASE_URL}/api/v1/users/{user_id}/coins/deduct"

        payload = {
            "amount": amount,
            "reference_id": reference or "booking",
            "description": description or "Flight booking"
        }

        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=5)
            if response.status_code == 403:
                raise forbidden_error("Insufficient balance", instance=url)
            if response.status_code == 401:
                raise unauthorized_error("Invalid JWT token or user ID", instance=url)
            if not response.ok:
                raise service_unavailable_error("Failed to deduct coins from FintechApp", instance=url)
        except requests.RequestException:
            raise service_unavailable_error("Connection error during coin deduction", instance=url)


    def requires_approval(self, amount: int, reference: Optional[str] = None) -> bool:
        """
        Indicates whether the booking requires manual approval.

        FintechApp does not require approval for any bookings.

        Args:
            amount (int): Loyalty amount (not used).
            reference (str, optional): Booking reference (ignored for FintechApp).

        Returns:
            bool: Always False for FintechApp.
        """
        return False

    def refund_points(self, amount: int) -> None:
        """
        Refund coins to the user's FintechApp account.

        Args:
            amount (int): Coins to refund.

        Raises:
            NotImplementedError: Refund logic is not yet implemented for FintechApp.
        """
        raise NotImplementedError("Refunds are not yet supported for FintechApp.")

    def authenticate(self, headers: Dict[str, str]) -> None:
        """
        No-op method. FintechApp uses JWT validation via validate_jwt().

        Args:
            headers (Dict[str, str]): Request headers from client.
        """
        pass

    def validate_jwt(self) -> None:
        """
        Validate the JWT token and session_id with the FintechApp API.
        Raises unauthorized ProblemDetailException if invalid.
        """
        url = f"{self.tenant.base_url}/api/v1/sessions/validate"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "user_id": self.auth.get("user_id"),
            "session_id": self.auth.get("session_id"),
            "device_id": self.auth.get("device_id"),
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            print(f"🔍 [FintechApp] Validation response status: {response.status_code}")
            print(f"🔍 [FintechApp] Validation response body: {response.text}")
        except Exception as e:
            raise ProblemDetailException(
                status=503,
                title="Token Validation Failed",
                detail="Could not connect to FintechApp session validator.",
                type_="about:blank",
                instance=url,
            )

        if response.status_code != 200:
            raise ProblemDetailException(
                status=401,
                title="Unauthorized",
                detail="Invalid token or session.",
                type_="about:blank",
                instance=url,
            )

        new_token = response.json().get("jwt_token")
        if new_token:
            self.token = new_token
