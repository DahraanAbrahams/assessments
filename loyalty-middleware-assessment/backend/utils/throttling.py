from rest_framework.throttling import SimpleRateThrottle
from rest_framework.request import Request
from typing import Optional


class TenantThrottle(SimpleRateThrottle):
    """
    A custom rate throttle that enforces per-tenant request limits.

    This throttle dynamically sets the request rate limit based on each
    tenant's configuration, using their `rate_limit_per_minute` field.

    The cache key combines the tenant slug and client IP to ensure fair
    distribution across users/IPs within the same tenant.

    Throttling Lifecycle:
        1. DRF initializes the view → calls `get_throttles()` → loads TenantThrottle
        2. DRF calls `get_cache_key()` → returns a key like "throttle_coffeechain_127.0.0.1"
        3. DRF:
            - Checks cache: `cache.get(key)`
            - If missing: `cache.set(key, 1, duration)`
            - If exists: `count += 1`, `cache.set(key, count, duration)`
            - Allows or blocks the request based on configured limits
    """

    scope = "tenant"

    def get_cache_key(self, request: Request, view) -> Optional[str]:
        """
        Generates a cache key used to throttle requests per tenant and IP address.

        Args:
            request (Request): The current HTTP request object.
            view (APIView): The DRF view being accessed.

        Returns:
            Optional[str]: A unique cache key if the tenant is available,
            otherwise None to bypass throttling.
        """
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return None

        # Store tenant instance on self so DRF can track usage per scope
        self.tenant = tenant
        rate_limit = getattr(tenant, "rate_limit_per_minute", 100)

        # Convert limit into DRF string format (e.g., "2/min")
        self.rate = f"{rate_limit}/min"

        # Parse into number of allowed requests and time window
        self.num_requests, self.duration = self.parse_rate(self.rate)

        # Use client IP to help isolate per-user behaviour within the tenant
        ident = self.get_ident(request)

        # Return unique cache key like "throttle_coffeechain_127.0.0.1"
        return f"throttle_{tenant.slug}_{ident}"
