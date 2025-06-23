import unittest
from unittest.mock import patch, Mock
from decimal import Decimal

from django.test import TestCase
from tenants.models import Tenant
from bookings.services.strategies.resolver import get_loyalty_strategy
from utils.rfc7807 import ProblemDetailException


class LoyaltyStrategyRefundTests(TestCase):
    """
    Tests for refund_points behaviour across tenant loyalty strategies.
    """

    def setUp(self):
        self.coffeechain = Tenant.objects.create(
            name="CoffeeChain",
            slug="coffeechain",
            auth_method="api_key",
            base_url="https://api.coffeechain.com",
            config={
                "api_key": "test-key",
                "auth_header": "X-CC-API-Key",
                "id_header": "X-CC-Member-ID"
            },
        )

        self.telcocorp = Tenant.objects.create(
            name="TelcoCorp",
            slug="telcocorp",
            auth_method="oauth2",
            base_url="https://api.telcocorp.com",
            config={
                "client_id": "test-client-id",
                "client_secret": "test-secret",
                "id_header": "X-TC-Customer-ID"
            },
        )

        self.fintechapp = Tenant.objects.create(
            name="FintechApp",
            slug="fintechapp",
            auth_method="jwt",
            base_url="https://api.fintechapp.com",
            config={
                "jwt_header": "X-FINTECH-JWT",
                "id_header": "X-FINTECH-USER-ID"
            },
        )

    @patch("bookings.services.strategies.coffeechain_strategy.requests.post")
    def test_coffeechain_refund_success(self, mock_post):
        """
        Should refund points successfully for CoffeeChain strategy.
        """
        mock_post.return_value.ok = True
        mock_post.return_value.status_code = 200

        auth = {"api_key": "test-key", "member_id": "abc123"}
        strategy = get_loyalty_strategy(self.coffeechain, auth)
        strategy.refund_points(9500)  # Should not raise

        mock_post.assert_called_once()
        self.assertIn("amount", mock_post.call_args.kwargs["json"])

    def test_telcocorp_refund_not_supported(self):
        """
        Should raise NotImplementedError for TelcoCorp refund.
        """
        auth = {"customer_id": "user456"}
        strategy = get_loyalty_strategy(self.telcocorp, auth)
        with self.assertRaises(NotImplementedError):
            strategy.refund_points(5000)

    def test_fintechapp_refund_not_supported(self):
        """
        Should raise NotImplementedError for FintechApp refund.
        """
        auth = {"jwt_token": "token123", "user_id": "user789"}
        strategy = get_loyalty_strategy(self.fintechapp, auth)
        with self.assertRaises(NotImplementedError):
            strategy.refund_points(5000)

    @patch("requests.post")
    def test_refund_failure_raises_problem_exception(self, mock_post):
        """Refund failure should raise a 503 ProblemDetailException."""
        mock_post.return_value.ok = False
        mock_post.return_value.status_code = 422

        tenant = Tenant.objects.get(slug="coffeechain")
        strategy = get_loyalty_strategy(tenant, {
            "api_key": "test_cc_api_key_12345",
            "member_id": "CC1234567"
        })

        with self.assertRaises(ProblemDetailException) as context:
            strategy.refund_points(amount=10000)

        self.assertEqual(context.exception.status_code, 503)
        self.assertIn("Refund failed", context.exception.detail["error"]["detail"])
