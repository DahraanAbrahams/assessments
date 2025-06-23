"""
Base Strategy Class for Tenant Loyalty Integrations.

Defines a common interface that all tenant-specific loyalty strategies
(e.g., CoffeeChain, TelcoCorp, FintechApp) must implement. Handles loyalty
currency logic such as authentication, balance checks, point deductions,
refunds, approval thresholds, and conversions to USD.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any
from tenants.models import Tenant


class LoyaltyStrategy(ABC):
    """
    Abstract base class defining the interface for tenant-specific loyalty logic.

    Each tenant must implement this interface to encapsulate business-specific
    rules and integration logic for loyalty bookings (e.g. point handling,
    cashback, approvals).

    Attributes:
        tenant (Tenant): The tenant instance making the request.
        config (Dict[str, Any]): Tenant configuration from the database.
        auth (Dict[str, str]): Authentication-related fields from request headers.
    """

    def __init__(self, tenant: Tenant, config: Dict[str, Any], auth: Dict[str, str]) -> None:
        """
        Initialize the strategy with tenant-specific data.

        Args:
            tenant (Tenant): The tenant making the request.
            config (Dict[str, Any]): The configuration dictionary for the tenant.
            auth (Dict[str, str]): Parsed auth headers for this tenant (e.g. member ID, token).
        """
        self.tenant = tenant
        self.config = config
        self.auth = auth

    @abstractmethod
    def authenticate(self, headers: Dict[str, str]) -> None:
        """
        Perform any tenant-specific authentication or validation using request headers.

        Args:
            headers (Dict[str, str]): The request headers provided by the client.

        Raises:
            Exception: If authentication fails or headers are invalid.
        """
        pass

    @abstractmethod
    def get_balance(self) -> int:
        """
        Retrieve the user's current loyalty balance.

        Returns:
            int: The available loyalty currency balance.

        Raises:
            Exception: If the balance cannot be fetched or the member is invalid.
        """
        pass

    @abstractmethod
    def deduct_points(self, amount: int) -> None:
        """
        Deduct loyalty currency from the user's account.

        Args:
            amount (int): The number of points to deduct.

        Raises:
            Exception: If deduction fails due to authentication, balance, or API failure.
        """
        pass

    @abstractmethod
    def refund_points(self, amount: int) -> None:
        """
        Refund loyalty currency back to the user's account.

        Args:
            amount (int): The number of points to refund.

        Raises:
            Exception: If refund fails or is not supported by the provider.
        """
        pass

    @abstractmethod
    def requires_approval(self, amount: int, reference: str = None) -> bool:
        """
        Determine if a booking requires manual approval based on loyalty amount.

        Args:
            amount (int): The total loyalty currency amount for the booking.
            reference (str, optional): The booking reference, if available.

        Returns:
            bool: True if approval is required, False otherwise.
        """
        pass

    def to_usd(self, amount: Decimal) -> Decimal:
        """
        Convert tenant-specific loyalty amount to its USD equivalent.

        This allows consistent calculations for cashback, receipts, etc.

        Args:
            amount (Decimal): Loyalty amount in native units (e.g. stars, coins).

        Returns:
            Decimal: USD equivalent of the loyalty amount.

        Raises:
            NotImplementedError: If conversion is not defined for the tenant.
        """
        slug = self.tenant.slug
        if slug == "coffeechain":
            return amount * Decimal("0.01")  # 1 star = $0.01
        elif slug == "telcocorp":
            return amount / Decimal("100")   # 100 points = $1
        elif slug == "fintechapp":
            return amount                    # 1 coin = $1
        else:
            raise NotImplementedError(f"to_usd() not implemented for tenant: {slug}")

    def apply_cashback(self, amount: Decimal) -> Decimal:
        """
        Apply tenant-specific cashback logic to the loyalty amount.

        FintechApp gives 2% cashback on bookings. Other tenants return original amount.

        Args:
            amount (Decimal): Original loyalty amount (pre-cashback).

        Returns:
            Decimal: Adjusted loyalty amount after applying cashback (if any).
        """
        slug = self.tenant.slug
        if slug == "fintechapp":
            return amount * Decimal("0.98")  # Apply 2% cashback
        return amount
