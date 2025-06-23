from django.test import TestCase, RequestFactory
from django.http import JsonResponse, HttpRequest, HttpResponse
from tenants.models import Tenant
from tenants.utils.middleware import TenantMiddleware


class TenantMiddlewareTests(TestCase):
    """
    Unit tests for the TenantMiddleware.

    These tests validate middleware behavior under different request conditions, such as:
    - Valid tenant header
    - Missing or unknown tenant
    - Malformed config
    """

    def setUp(self) -> None:
        """
        Set up the test environment.

        - Initializes a request factory.
        - Creates a mock tenant ("coffeechain").
        - Prepares a no-op middleware response lambda that returns a simple JsonResponse.
        """
        self.factory = RequestFactory()
        self.middleware = TenantMiddleware(get_response=lambda r: JsonResponse({"ok": True}))

        self.tenant = Tenant.objects.create(
            name="CoffeeChain",
            slug="coffeechain",
            config={"api_key": "secret-key"},
        )

    def test_valid_tenant_sets_request_tenant(self) -> None:
        """
        Test that a valid tenant slug in `X-Tenant-ID` header correctly attaches
        the tenant object to `request.tenant`.

        Asserts:
            - 200 OK response
            - `request.tenant.slug` matches expected slug
        """
        request: HttpRequest = self.factory.get("/any", HTTP_X_TENANT_ID="coffeechain")
        response: HttpResponse = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(getattr(request, "tenant").slug, "coffeechain")

    def test_missing_tenant_header_returns_400(self) -> None:
        """
        Test that a missing `X-Tenant-ID` header results in a 400 Bad Request.

        Middleware should return an RFC 7807-formatted response indicating the header is missing.
        """
        request: HttpRequest = self.factory.get("/any")
        response: HttpResponse = self.middleware(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("missing-tenant-header", response.content.decode())

    def test_unknown_tenant_returns_404(self) -> None:
        """
        Test that a nonexistent tenant slug results in a 404 Not Found.

        Middleware should return an RFC 7807-formatted response indicating tenant not found.
        """
        request: HttpRequest = self.factory.get("/any", HTTP_X_TENANT_ID="doesnotexist")
        response: HttpResponse = self.middleware(request)

        self.assertEqual(response.status_code, 404)
        self.assertIn("invalid-tenant", response.content.decode())

    def test_malformed_config_returns_500(self) -> None:
        """
        Test that a non-dictionary config on the tenant model results in a 500 Internal Server Error.

        Middleware should return an RFC 7807-formatted response indicating the config is invalid.
        """
        self.tenant.config = "should-be-a-dict"
        self.tenant.save()

        request: HttpRequest = self.factory.get("/any", HTTP_X_TENANT_ID="coffeechain")
        response: HttpResponse = self.middleware(request)

        self.assertEqual(response.status_code, 500)
        self.assertIn("invalid-tenant-config", response.content.decode())
