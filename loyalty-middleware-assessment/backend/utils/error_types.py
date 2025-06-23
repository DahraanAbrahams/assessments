"""
Defines RFC 7807 problem type URIs used across the Loyalty Middleware API.

Each constant here serves as a machine-readable URI to uniquely identify
a specific category of error, as per the RFC 7807 problem+json specification.

This file allows consistent use of standard error types across all handlers,
middleware, and exception logic.
"""

# Base URI prefix for all error types used in this middleware system
BASE_URI = "https://api.loyalty-middleware.com/errors"


# ===========================================================
# General application-level errors
# ===========================================================

VALIDATION_ERROR = f"{BASE_URI}/validation-error"
UNAUTHORIZED = f"{BASE_URI}/unauthorized"
FORBIDDEN = f"{BASE_URI}/forbidden"
NOT_FOUND = f"{BASE_URI}/not-found"
RATE_LIMIT = f"{BASE_URI}/rate-limit"
INTERNAL_ERROR = f"{BASE_URI}/internal-error"


# ===========================================================
# Tenant and middleware-specific errors
# ===========================================================

MISSING_TENANT_HEADER = f"{BASE_URI}/missing-tenant-header"
INVALID_TENANT = f"{BASE_URI}/invalid-tenant"
INVALID_TENANT_CONFIG = f"{BASE_URI}/invalid-tenant-config"


# ===========================================================
# Errors from external dependencies (e.g., Duffel API)
# ===========================================================

DUFFEL_TIMEOUT = f"{BASE_URI}/duffel-timeout"
DUFFEL_ERROR = f"{BASE_URI}/duffel-bad-gateway"


# ===========================================================
# Domain-specific business rule violations
# ===========================================================

INVALID_CABIN_CLASS = f"{BASE_URI}/invalid-cabin-class"
INSUFFICIENT_BALANCE = f"{BASE_URI}/insufficient-balance"
BOOKING_LIMIT_EXCEEDED = f"{BASE_URI}/booking-limit"
CASHBACK_RULE = f"{BASE_URI}/cashback-violation"
APPROVAL_REQUIRED = f"{BASE_URI}/approval-required"


# ===========================================================
# Mapping from DRF status codes to error types
# ===========================================================

STATUS_CODE_TO_TYPE = {
    400: VALIDATION_ERROR,
    401: UNAUTHORIZED,
    403: FORBIDDEN,
    404: NOT_FOUND,
    429: RATE_LIMIT,
    500: INTERNAL_ERROR,
}
