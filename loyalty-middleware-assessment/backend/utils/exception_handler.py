"""
Custom exception handler integration for Django REST Framework.

This module overrides DRF's default exception handler and reformats
errors into RFC 7807 Problem Details responses for consistency across the API.

References:
- https://tools.ietf.org/html/rfc7807
- https://www.django-rest-framework.org/api-guide/exceptions/
"""

from rest_framework.views import exception_handler as drf_default_exception_handler
from rest_framework.response import Response

from utils.rfc7807 import build_problem_response
from utils.error_types import STATUS_CODE_TO_TYPE, INTERNAL_ERROR
from utils.exceptions import ProblemDetailException


def rfc7807_exception_handler(exc, context):
    """
    Django REST Framework exception handler that returns structured RFC 7807 errors.

    This function is intended to be registered in Django settings as:
        REST_FRAMEWORK = {
            "EXCEPTION_HANDLER": "utils.exception_handler.rfc7807_exception_handler"
        }

    It supports two modes of operation:
        1. Handles standard DRF exceptions (validation, auth, etc.)
        2. Supports manually raised ProblemDetailException for structured control flow

    Args:
        exc (Exception): The raised exception instance.
        context (dict): Context including view, request, and traceback information.

    Returns:
        Response | None: A DRF Response with problem+json structure,
                         or None to allow default Django fallback (500 page).
    """
    # NEW: Handle structured RFC 7807 exceptions explicitly raised in code
    if isinstance(exc, ProblemDetailException):
        return Response(data=exc.detail, status=exc.status_code)

    # Let DRF handle standard exceptions (e.g., serializer/permission/auth)
    response = drf_default_exception_handler(exc, context)

    if response is None:
        # Unexpected exceptions (e.g., ZeroDivisionError) will fall back to Django's 500
        return None

    # Extract request path for the `instance` field (defaults to "/" if missing)
    request = context.get("request")
    path = request.path if request else "/"

    # Get the "detail" string used by DRF in most error responses
    detail = response.data.get("detail", "An error occurred.")

    # Preserve any detailed errors for inclusion under "errors" key
    errors = response.data if isinstance(response.data, dict) else {}

    # Use DRF’s built-in default message or fallback
    title = getattr(exc, "default_detail", "Unhandled error")

    # Resolve the error type URI from status code
    error_type = STATUS_CODE_TO_TYPE.get(response.status_code, INTERNAL_ERROR)

    # Return an RFC 7807-compliant response using our core utility
    return build_problem_response(
        type_=error_type,
        title=title,
        status=response.status_code,
        detail=str(detail),
        instance=path,
        extra={"errors": errors},
        use_drf=True,
    )
