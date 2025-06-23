"""
Strategy Resolver for Tenant Loyalty Integrations.

Provides a factory method for dynamically selecting the appropriate
LoyaltyStrategy implementation based on the tenant slug.
"""

from bookings.services.strategies.base_strategy import LoyaltyStrategy
from bookings.services.strategies.coffeechain_strategy import CoffeeChainStrategy
from bookings.services.strategies.telcocorp_strategy import TelcoCorpStrategy
from bookings.services.strategies.fintechapp_strategy import FintechAppStrategy
from tenants.models import Tenant


def get_loyalty_strategy(tenant: Tenant, auth: dict) -> LoyaltyStrategy:
    """
    Factory method to retrieve the correct LoyaltyStrategy implementation
    for the given tenant.

    Args:
        tenant (Tenant): The tenant making the request.
        auth (dict): Parsed authentication values for the tenant (e.g., member ID, token).

    Returns:
        LoyaltyStrategy: An instantiated strategy for the given tenant.

    Raises:
        NotImplementedError: If no strategy is registered for the given tenant slug.
    """
    print(f"[DEBUG] Strategy resolver auth: {auth}")

    slug = tenant.slug.lower()

    if slug == "coffeechain":
        strategy = CoffeeChainStrategy(tenant, tenant.config, auth)
    elif slug == "telcocorp":
        strategy = TelcoCorpStrategy(tenant, tenant.config, auth)
    elif slug == "fintechapp":
        strategy = FintechAppStrategy(tenant, tenant.config, auth)
    else:
        raise NotImplementedError(f"No loyalty strategy implemented for tenant: {slug}")

    strategy.tenant = tenant  # Patch in the tenant object for use in base methods
    return strategy