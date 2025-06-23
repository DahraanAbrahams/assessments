from django.db import models


class Tenant(models.Model):
    """
    Represents a third-party enterprise tenant (loyalty partner) in the system.

    Each tenant has its own authentication method, currency configuration, and business rules.
    Configuration values that vary per tenant are stored in the `config` field as a flexible JSON object.

    Example tenants include:
    - CoffeeChain (API Key, Stars)
    - TelcoCorp (OAuth2, Points)
    - FintechApp (JWT, Coins)
    """

    AUTH_METHOD_CHOICES = [
        ("api_key", "API Key"),
        ("oauth2", "OAuth 2.0"),
        ("jwt", "JWT"),
    ]

    name = models.CharField(
        max_length=100,
        help_text="Display name of the tenant, e.g. 'CoffeeChain'"
    )
    slug = models.SlugField(
        unique=True,
        help_text="Unique identifier used in headers and URL routing, e.g. 'coffeechain'"
    )
    auth_method = models.CharField(
        max_length=20,
        choices=AUTH_METHOD_CHOICES,
        help_text="Authentication mechanism used by the tenant's API"
    )
    base_url = models.URLField(
        help_text="Base URL of the tenant's loyalty program API"
    )
    rate_limit_per_minute = models.PositiveIntegerField(
        default=100,
        help_text="Maximum number of allowed requests per minute for this tenant"
    )
    config = models.JSONField(
        default=dict,
        help_text="Flexible per-tenant configuration (e.g., currency, ID headers, special rules)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_currency(self) -> str:
        """Returns the loyalty currency used by the tenant."""
        return self.config.get("currency")

    def get_usd_rate(self) -> float:
        """Returns the exchange rate from loyalty currency to USD."""
        return float(self.config.get("currency_to_usd", 1.0))

    def requires_approval(self, amount: float) -> bool:
        """
        Determines whether a booking exceeds the tenant's approval threshold.

        Args:
            amount (float): Loyalty amount (in tenant's currency units)

        Returns:
            bool: True if approval is required, False otherwise.
        """
        threshold = self.config.get("approval_threshold")
        return threshold is not None and amount > threshold

    def is_valid_cabin_class(self, cabin: str) -> bool:
        """
        Validates if the given cabin class is allowed for this tenant.

        If tenant has no cabin class restriction, all values are valid.
        Returns False if `cabin` is None or does not match allowed value.

        Args:
            cabin (str): Cabin class to validate (e.g., 'economy').

        Returns:
            bool: Whether the cabin class is allowed.
        """
        allowed = self.config.get("allowed_cabin_class")
        if not cabin:
            return False
        return allowed is None or cabin.lower() == allowed.lower()

    def get_id_header(self) -> str:
        """
        Returns the name of the tenant-specific header used for identifying the user/member.

        Returns:
            str: Header key (e.g., 'X-CC-Member-ID')
        """
        return self.config.get("id_header")

    def get_auth_header(self) -> str:
        """
        Returns the name of the tenant-specific authentication header, if applicable.

        Returns:
            str: Header key (e.g., 'X-CC-API-Key') or None
        """
        return self.config.get("auth_header")

    def get_cashback_rate(self) -> float:
        """
        Returns the cashback percentage to apply for bookings (as a decimal).

        Currently only FintechApp applies 2% cashback on all bookings.
        Returns:
            float: Cashback rate (e.g., 0.02 for 2%).
        """
        return 0.02 if self.slug == "fintechapp" else 0.0
