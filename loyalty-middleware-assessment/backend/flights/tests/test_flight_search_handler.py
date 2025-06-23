import json
from datetime import date, timedelta
from unittest.mock import patch

from django.test.utils import override_settings
from django.core.cache import cache

from django.conf import settings
from rest_framework.test import APITestCase, APIClient

from tenants.models import Tenant


class FlightSearchHandlerTests(APITestCase):
    """
    Test suite for flight search functionality via FlightSearchHandler.

    Covers:
    - Valid search
    - Missing tenant
    - Invalid input payloads
    - Caching behaviour
    """

    def setUp(self):
        self.client = APIClient()
        cache.clear()
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)
        self.next_week = self.today + timedelta(days=7)

        self.tenant = Tenant.objects.create(
            name="CoffeeChain",
            slug="coffeechain",
            auth_method="api_key",
            base_url="https://api.coffeechain.com",
            config={
                "api_key": "test-key",
                "auth_header": "X-CC-API-Key",
                "id_header": "X-CC-Member-ID",
                "approval_threshold": 10000,
                "allowed_cabin_class": "economy"
            },
            rate_limit_per_minute = 2,
        )

        self.auth_header = {
            "HTTP_X_TENANT_ID": self.tenant.slug,
            "HTTP_X_CC_API_KEY": "test-key"
        }

        self.valid_payload = {
            "origin": "CPT",
            "destination": "JNB",
            "departure_date": str(self.tomorrow),
            "return_date": str(self.next_week),
            "passengers": {"adults": 1, "children": 0, "infants": 0},
            "cabin_class": "economy",
            "currency": "USD"
        }

    @patch("flights.handlers.search_flights")
    def test_valid_flight_search_returns_200(self, mock_search):
        """Valid payload should return 200 and offers."""
        mock_search.return_value = {"data": {"offers": [{"id": "offer_123"}]}}

        response = self.client.post(
            "/api/v1/flights/search",
            data=json.dumps(self.valid_payload),
            content_type="application/json",
            **self.auth_header
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("offers", response.json())

    def test_missing_tenant_returns_400(self):
        """
        Should return 400 if the request is missing the X-Tenant-ID header.

        This test ensures that the TenantMiddleware intercepts the request
        and returns a structured RFC 7807-style error response when the
        required tenant header is absent.
        """
        response = self.client.post(
            "/api/v1/flights/search",
            data=json.dumps(self.valid_payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        body = response.json()  # safer than accessing .content directly
        self.assertIn("Missing required X-Tenant-ID header", body["error"]["detail"])

    def test_invalid_payload_returns_400(self):
        """Invalid payload should trigger 400 validation error."""
        payload = self.valid_payload.copy()
        del payload["origin"]  # remove required field

        response = self.client.post(
            "/api/v1/flights/search",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_header
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Validation Error", response.json()["error"]["title"])

    def test_return_date_before_departure_raises_error(self):
        """Return date before departure should be rejected."""
        payload = self.valid_payload.copy()
        payload["return_date"] = str(self.today)

        response = self.client.post(
            "/api/v1/flights/search",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_header
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Return date cannot be before departure date", str(response.content))

    @patch("flights.handlers.search_flights")
    def test_cached_flight_search_uses_cache(self, mock_cache_get):
        """Should use cached response if available."""
        mock_cache_get.return_value = {"data": {"offers": [{"id": "cached_offer"}]}}

        response = self.client.post(
            "/api/v1/flights/search",
            data=json.dumps(self.valid_payload),
            content_type="application/json",
            **self.auth_header
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["offers"][0]["id"], "cached_offer")

    def test_invalid_tenant_returns_404(self):
        """Should return 404 if X-Tenant-ID does not match a known tenant."""
        response = self.client.post(
            "/api/v1/flights/search",
            data=json.dumps(self.valid_payload),
            content_type="application/json",
            **{"HTTP_X_TENANT_ID": "unknowncorp"},
        )

        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertIn("No tenant found", body["error"]["detail"])

    def test_malformed_tenant_config_returns_500(self):
        """Should return 500 if tenant config is not a dict."""
        Tenant.objects.create(slug="brokenconfig", config="not-a-dict", auth_method="api_key")

        response = self.client.post(
            "/api/v1/flights/search",
            data=json.dumps(self.valid_payload),
            content_type="application/json",
            **{"HTTP_X_TENANT_ID": "brokenconfig"},
        )

        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertIn("malformed config", body["error"]["detail"])

    def test_invalid_api_key_returns_401(self):
        """Should return 401 if API key is missing or incorrect for api_key-auth tenants."""
        response = self.client.post(
            "/api/v1/flights/search",
            data=json.dumps(self.valid_payload),
            content_type="application/json",
            **{
                "HTTP_X_TENANT_ID": "coffeechain",
                "HTTP_X_CC_API_KEY": "wrong-key"
            },
        )

        self.assertEqual(response.status_code, 401)
        body = response.json()
        self.assertIn("Missing or invalid auth header", body["error"]["detail"])

    def test_invalid_bearer_token_returns_401(self):
        """Should return 401 if Authorization header is missing or malformed for JWT tenants."""
        Tenant.objects.create(
            slug="telcocorp",
            config={"some_oauth": "value"},
            auth_method="jwt"
        )

        response = self.client.post(
            "/api/v1/flights/search",
            data=json.dumps(self.valid_payload),
            content_type="application/json",
            **{
                "HTTP_X_TENANT_ID": "telcocorp",
                "HTTP_AUTHORIZATION": "Token abc123"  # should be Bearer
            },
        )

        self.assertEqual(response.status_code, 401)
        body = response.json()
        self.assertIn("malformed Bearer token", body["error"]["detail"])

    @override_settings(
        CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
        REST_FRAMEWORK={
            **settings.REST_FRAMEWORK,
            "DEFAULT_THROTTLE_CLASSES": ["utils.throttling.TenantThrottle"],
            "DEFAULT_THROTTLE_RATES": {"tenant": "2/min"},
        }
    )
    @patch("flights.handlers.search_flights")
    def test_rate_limiting_per_tenant(self, mock_search):
        mock_search.return_value = {"data": {"offers": [{"id": "off_123"}]}}

        for i in range(2):
            response = self.client.post(
                "/api/v1/flights/search",
                data=json.dumps(self.valid_payload),
                content_type="application/json",
                **self.auth_header,
                REMOTE_ADDR="127.0.0.1",
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/api/v1/flights/search",
            data=json.dumps(self.valid_payload),
            content_type="application/json",
            **self.auth_header,
            REMOTE_ADDR="127.0.0.1",
        )

        self.assertEqual(response.status_code, 429)
