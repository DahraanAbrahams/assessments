import os
import django
import logging
from decouple import config

# Set the Django settings module so ORM and models can be used in this standalone script
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

# Configure root logger using environment-defined log level
logging.basicConfig(
    level=getattr(logging, config("LOG_LEVEL", default="INFO").upper()),
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

from tenants.models import Tenant


def seed_tenants() -> None:
    """
    Seed initial tenant data into the database using environment-configured values.

    This function will create or update three predefined tenants: CoffeeChain, TelcoCorp,
    and FintechApp. Each tenant has its own authentication method, rate limit, and config
    dictionary.

    It uses Django's `update_or_create()` to ensure idempotency (safe to run multiple times).

    Environment Variables:
        - COFFEECHAIN_API_URL
        - COFFEECHAIN_API_KEY
        - TELCOCORP_API_URL
        - FINTECHAPP_API_URL

    Raises:
        django.core.exceptions.ImproperlyConfigured: If any required env var is missing.
    """
    logger.info("Starting tenant seeding...")

    tenants = [
        {
            "name": "CoffeeChain",
            "slug": "coffeechain",
            "auth_method": "api_key",
            "base_url": config("COFFEECHAIN_API_URL"),
            "rate_limit_per_minute": 100,
            "config": {
                "currency": "Stars",
                "currency_to_usd": 0.01,
                "approval_threshold": 50000,
                "id_header": "X-CC-Member-ID",
                "auth_header": "X-CC-API-Key",
                "api_key": config("COFFEECHAIN_API_KEY"),
            },
        },
        {
            "name": "TelcoCorp",
            "slug": "telcocorp",
            "auth_method": "oauth2",
            "base_url": config("TELCOCORP_API_URL"),
            "rate_limit_per_minute": 50,
            "config": {
                "currency": "Points",
                "currency_to_usd": 0.01,
                "allowed_cabin_class": "economy",
                "id_header": "X-TC-Customer-ID",
                "client_id": config("TELCOCORP_CLIENT_ID"),
                "client_secret": config("TELCOCORP_CLIENT_SECRET"),
            },
        },
        {
            "name": "FintechApp",
            "slug": "fintechapp",
            "auth_method": "jwt",
            "base_url": config("FINTECHAPP_API_URL"),
            "rate_limit_per_minute": 200,
            "config": {
                "currency": "Coins",
                "currency_to_usd": 1.0,
                "id_header": "X-FA-User-ID",
                "user_id_header": "X-FA-User-ID",
                "jwt_header": "Authorization",
            },
        },
    ]

    # Loop through each tenant and create or update based on slug
    for data in tenants:
        tenant, created = Tenant.objects.update_or_create(slug=data["slug"], defaults=data)
        if created:
            logger.info(f"Created tenant: {tenant.slug}")
        else:
            logger.info(f"Updated tenant: {tenant.slug}")

    logger.info("Tenant seeding complete.")


if __name__ == "__main__":
    seed_tenants()
