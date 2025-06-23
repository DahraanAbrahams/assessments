from drf_yasg import openapi

TENANT_HEADERS = [
    openapi.Parameter(
        "X-Tenant-ID",
        openapi.IN_HEADER,
        description="Tenant ID (e.g. coffeechain, telcocorp, fintechapp)",
        type=openapi.TYPE_STRING,
        required=True
    ),
    openapi.Parameter(
        "X-CC-API-Key",
        openapi.IN_HEADER,
        description="API Key for CoffeeChain",
        type=openapi.TYPE_STRING,
        required=False
    ),
    openapi.Parameter(
        "X-CC-Member-ID",
        openapi.IN_HEADER,
        description="Member ID for CoffeeChain",
        type=openapi.TYPE_STRING,
        required=False
    ),
    openapi.Parameter(
        "X-TC-Customer-ID",
        openapi.IN_HEADER,
        description="Customer ID for TelcoCorp",
        type=openapi.TYPE_STRING,
        required=False
    ),
    openapi.Parameter(
        "X-FA-User-ID",
        openapi.IN_HEADER,
        description="User ID for FintechApp",
        type=openapi.TYPE_STRING,
        required=False
    ),
    openapi.Parameter(
        "Authorization",
        openapi.IN_HEADER,
        description="Bearer token (for TelcoCorp or FintechApp)",
        type=openapi.TYPE_STRING,
        required=False
    ),
]
