"""
RFC 7807-compliant error response utilities.

Provides a standardized interface to return or raise structured error responses
using the `application/problem+json` format as defined in RFC 7807:
https://datatracker.ietf.org/doc/html/rfc7807
"""

from typing import Union

from django.http import JsonResponse
from rest_framework.response import Response

from utils.error_types import (
    VALIDATION_ERROR,
    UNAUTHORIZED,
    FORBIDDEN,
    NOT_FOUND,
    INTERNAL_ERROR,
    RATE_LIMIT,
)
from utils.exceptions import ProblemDetailException
from utils.trace import generate_trace_id


def build_problem_response(
    *,
    type_: str,
    title: str,
    status: int,
    detail: str,
    instance: str,
    extra: dict = None,
    use_drf: bool = True,
) -> Union[Response, JsonResponse]:
    """
    Constructs and returns an RFC 7807-compliant error response.

    Args:
        type_ (str): A URI reference identifying the problem type.
        title (str): A short, human-readable summary of the problem.
        status (int): The HTTP status code.
        detail (str): A human-readable explanation specific to this occurrence of the problem.
        instance (str): A URI reference that identifies the specific occurrence of the problem.
        extra (dict, optional): Additional fields to include in the response body.
        use_drf (bool): Whether to return a DRF Response or Django JsonResponse.

    Returns:
        Union[Response, JsonResponse]: Structured error response.
    """
    problem = {
        "error": {
            "type": type_,
            "title": title,
            "status": status,
            "detail": detail,
            "instance": instance,
            "trace_id": generate_trace_id(),
        }
    }

    if extra:
        problem["error"].update(extra)

    if use_drf:
        return Response(problem, status=status)
    return JsonResponse(problem, status=status)


# ------------------------------------------------------------------------------
#             Convenience Wrappers: Raise Variants (used in logic flow)
# ------------------------------------------------------------------------------

def validation_error(detail: str, instance: str, extra: dict = None) -> None:
    """Raises a 400 Validation Error."""
    raise ProblemDetailException(
        type_=VALIDATION_ERROR,
        title="Validation Error",
        status=400,
        detail=detail,
        instance=instance,
        extra=extra,
    )


def unauthorized_error(detail: str, instance: str, extra: dict = None) -> None:
    """Raises a 401 Unauthorized Error."""
    raise ProblemDetailException(
        type_=UNAUTHORIZED,
        title="Unauthorized",
        status=401,
        detail=detail,
        instance=instance,
        extra=extra,
    )


def forbidden_error(detail: str, instance: str, extra: dict = None) -> None:
    """Raises a 403 Forbidden Error."""
    raise ProblemDetailException(
        type_=FORBIDDEN,
        title="Forbidden",
        status=403,
        detail=detail,
        instance=instance,
        extra=extra,
    )


def not_found_error(detail: str, instance: str, extra: dict = None) -> None:
    """Raises a 404 Not Found Error."""
    raise ProblemDetailException(
        type_=NOT_FOUND,
        title="Not Found",
        status=404,
        detail=detail,
        instance=instance,
        extra=extra,
    )


def internal_server_error(detail: str, instance: str, extra: dict = None) -> None:
    """Raises a 500 Internal Server Error."""
    raise ProblemDetailException(
        type_=INTERNAL_ERROR,
        title="Internal Server Error",
        status=500,
        detail=detail,
        instance=instance,
        extra=extra,
    )


def service_unavailable_error(detail: str, instance: str, extra: dict = None) -> None:
    """Raises a 503 Service Unavailable Error."""
    raise ProblemDetailException(
        type_="https://api.loyalty-middleware.com/errors/service-unavailable",
        title="Service Unavailable",
        status=503,
        detail=detail,
        instance=instance,
        extra=extra,
    )


def rate_limit_error(detail: str, instance: str, extra: dict = None) -> None:
    """Raises a 429 Rate Limit Exceeded Error."""
    raise ProblemDetailException(
        type_=RATE_LIMIT,
        title="Rate Limit Exceeded",
        status=429,
        detail=detail,
        instance=instance,
        extra=extra,
    )


def missing_tenant_header_error(instance: str, extra: dict = None) -> None:
    """Raises a 400 Bad Request error when the X-Tenant-ID header is missing."""
    raise ProblemDetailException(
        type_="https://api.loyalty-middleware.com/errors/missing-tenant-header",
        title="Missing Tenant ID",
        status=400,
        detail="Missing required X-Tenant-ID header.",
        instance=instance,
        extra=extra,
    )


# ------------------------------------------------------------------------------
#   Return-based variants for internal DRF error handling or tests
# ------------------------------------------------------------------------------

def return_validation_error(detail: str, instance: str, extra: dict = None, use_drf: bool = True) -> Response:
    """
    Returns a 400 Validation Error as a response (instead of raising it).

    Args:
        detail (str): Description of the validation issue.
        instance (str): Request URI that caused the error.
        extra (dict, optional): Additional fields to include.
        use_drf (bool): Whether to return a DRF Response (default) or Django JsonResponse.

    Returns:
        Response: RFC 7807-compliant error response.
    """
    return build_problem_response(
        type_=VALIDATION_ERROR,
        title="Validation Error",
        status=400,
        detail=detail,
        instance=instance,
        extra=extra,
        use_drf=use_drf,
    )
