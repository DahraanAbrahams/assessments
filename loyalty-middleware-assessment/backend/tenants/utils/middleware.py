from typing import Optional, Dict
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse, HttpRequest, HttpResponse
from tenants.models import Tenant


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware that identifies and authenticates tenants based on the `X-Tenant-ID` header.

    Responsibilities:
    - Extracts and attaches the tenant object to the request.
    - Enforces authentication rules per tenant (e.g., API key or bearer token).
    - Injects a helper (`request.get_tenant_auth_headers`) for outbound API calls.

    Skips processing for explicitly exempted paths (e.g., health check).
    """

    EXEMPT_PATHS = {"/api/v1/health"}

    def process_request(self, request: HttpRequest) -> Optional[JsonResponse]:
        """
        Middleware entrypoint for each incoming request.

        Args:
            request (HttpRequest): Incoming request object.

        Returns:
            Optional[JsonResponse]: JSON error response if tenant validation or authentication fails,
            otherwise None to proceed with the request lifecycle.
        """
        if (
                request.path in self.EXEMPT_PATHS or
                request.path.startswith("/swagger") or
                request.path.startswith("/redoc") or
                request.path.startswith("/swagger.json") or
                request.path.startswith("/swagger.yaml") or
                (request.path.startswith("/api/v1/tenants") and request.headers.get("X-Internal-Access") == "true")
        ):
            return None

        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            return self.json_error(
                type_="https://api.loyalty-middleware.com/errors/missing-tenant-header",
                title="Missing Tenant ID",
                status=400,
                detail="Missing required X-Tenant-ID header.",
                instance=request.path,
            )

        try:
            tenant = Tenant.objects.get(slug=tenant_id)
        except Tenant.DoesNotExist:
            return self.json_error(
                type_="https://api.loyalty-middleware.com/errors/invalid-tenant",
                title="Invalid Tenant",
                status=404,
                detail=f"No tenant found for identifier '{tenant_id}'.",
                instance=request.path,
            )

        if not isinstance(tenant.config, dict):
            return self.json_error(
                type_="https://api.loyalty-middleware.com/errors/invalid-tenant-config",
                title="Invalid Tenant Configuration",
                status=500,
                detail=f"Tenant '{tenant.slug}' has malformed config. Expected a dictionary.",
                instance=request.path,
            )

        # Attach the tenant object and outbound header helper to the request
        request.tenant = tenant
        request.get_tenant_auth_headers = lambda member_id=None, token=None: self.get_auth_headers(
            tenant, member_id, token
        )

        # Perform inbound authentication based on the tenant's auth method
        auth_method = tenant.auth_method

        if auth_method == "api_key":
            auth_header = tenant.get_auth_header()
            expected_token = tenant.config.get("api_key")
            incoming_token = request.headers.get(auth_header)

            if not incoming_token or incoming_token != expected_token:
                return self.json_error(
                    type_="https://api.loyalty-middleware.com/errors/unauthorized",
                    title="Unauthorized",
                    status=401,
                    detail=f"Missing or invalid auth header: {auth_header}",
                    instance=request.path,
                )

        elif auth_method in ["jwt", "oauth2"]:
            incoming_auth = request.headers.get("Authorization", "")
            if not incoming_auth.startswith("Bearer "):
                return self.json_error(
                    type_="https://api.loyalty-middleware.com/errors/unauthorized",
                    title="Unauthorized",
                    status=401,
                    detail="Missing or malformed Bearer token.",
                    instance=request.path,
                )

        return None

    def json_error(
        self,
        *,
        type_: str,
        title: str,
        status: int,
        detail: str,
        instance: str,
    ) -> JsonResponse:
        """
        Constructs a structured JSON error response in RFC 7807 format.

        Args:
            type_ (str): A URI reference that identifies the problem type.
            title (str): A short, human-readable summary of the problem.
            status (int): HTTP status code.
            detail (str): Explanation of the specific error.
            instance (str): The request path where the error occurred.

        Returns:
            JsonResponse: Structured RFC 7807-compliant error payload.
        """
        return JsonResponse(
            {
                "error": {
                    "type": type_,
                    "title": title,
                    "status": status,
                    "detail": detail,
                    "instance": instance,
                }
            },
            status=status,
        )

    def get_auth_headers(
        self,
        tenant: Tenant,
        member_id: Optional[str] = None,
        token: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Constructs outbound headers based on tenant-specific auth rules.

        Args:
            tenant (Tenant): The tenant object.
            member_id (Optional[str]): The loyalty member or customer ID.
            token (Optional[str]): JWT or OAuth2 token, if applicable.

        Returns:
            Dict[str, str]: Dictionary of headers to attach to outbound API calls.
        """
        headers: Dict[str, str] = {}

        if not isinstance(tenant.config, dict):
            return headers

        if tenant.slug == "coffeechain":
            headers["X-CC-API-Key"] = tenant.config.get("api_key", "")
            if member_id:
                headers["X-CC-Member-ID"] = member_id

        elif tenant.slug == "telcocorp":
            if token:
                headers["Authorization"] = f"Bearer {token}"
            if member_id:
                headers["X-TC-Customer-ID"] = member_id

        elif tenant.slug == "fintechapp":
            if token:
                headers["Authorization"] = f"Bearer {token}"
            if member_id:
                headers["X-FA-User-ID"] = member_id

        return headers
