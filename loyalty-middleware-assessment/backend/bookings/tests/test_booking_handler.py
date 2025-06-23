import json
from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase, Client
from tenants.models import Tenant


class BookingHandlerTests(TestCase):
    """
    Tests for POST /api/bookings/ endpoint, focusing on tenant-specific logic,
    approval thresholds, and cabin class enforcement.

    Covers:
    - Successful booking with confirmation
    - Booking requiring approval
    - Cabin class rejection
    """

    def setUp(self):
        """Set up test client, tenant, headers, and reusable payload."""
        self.client = Client()
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)
        self.next_week = self.today + timedelta(days=7)

        # Create CoffeeChain tenant with cabin class rules
        self.tenant = Tenant.objects.create(
            name="CoffeeChain",
            slug="coffeechain",
            auth_method="api_key",
            base_url="https://mock.coffeechain.com",
            config={
                "auth_header": "X-CC-API-Key",
                "id_header": "X-CC-Member-ID",
                "api_key": "test-key",
                "approval_threshold": 10000,
                "allowed_cabin_class": "economy"
            }
        )

        # DRF test client uses HTTP_ prefix for headers
        self.auth_headers = {
            "HTTP_X_CC_API_KEY": "test-key",
            "HTTP_X_CC_MEMBER_ID": "member123",
            "HTTP_X_TENANT_ID": "coffeechain"
        }

        # Reusable base payload
        self.valid_payload = {
            "flight_id": "test-offer-id",
            "cabin_class": "economy",
            "passengers": [
                {
                    "first_name": "Alice",
                    "last_name": "Smith"
                }
            ],
            "payment": {
                "amount": 9000,
                "currency": "stars"
            },
            "contact": {
                "email": "alice@example.com",
                "phone": "1234567890"
            }
        }

        # Mocked Duffel offer used by all test cases
        self.mock_offer_data = {
            "slices": [
                {
                    "segments": [
                        {
                            "origin": {"iata_code": "JFK"},
                            "destination": {"iata_code": "LAX"},
                            "departing_at": "2025-07-01T08:00:00Z",
                            "passengers": [{"cabin_class": "economy"}]
                        }
                    ]
                }
            ]
        }

    @patch("bookings.utils.booking_logic.get_offer_by_id")
    @patch("bookings.services.strategies.coffeechain_strategy.CoffeeChainStrategy.to_usd", return_value=9000)
    @patch("bookings.services.strategies.coffeechain_strategy.CoffeeChainStrategy.deduct_points")
    @patch("bookings.services.strategies.coffeechain_strategy.CoffeeChainStrategy.requires_approval", return_value=False)
    def test_create_booking_success_confirmed(
        self, mock_approval, mock_deduct, mock_usd, mock_get_offer
    ):
        """
        Test that a booking is created with status 'confirmed' if no approval is required.

        Mocks:
            - get_offer_by_id
            - to_usd
            - deduct_points
            - requires_approval
        """
        mock_get_offer.return_value = self.mock_offer_data

        response = self.client.post(
            "/api/bookings/",
            data=json.dumps(self.valid_payload),
            content_type="application/json",
            **self.auth_headers
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["data"]["status"], "confirmed")
        self.assertNotIn("approval_required", response.json()["data"])

    @patch("bookings.utils.booking_logic.get_offer_by_id")
    @patch("bookings.services.strategies.coffeechain_strategy.CoffeeChainStrategy.to_usd", return_value=20000)
    @patch("bookings.services.strategies.coffeechain_strategy.CoffeeChainStrategy.deduct_points")
    @patch("bookings.services.strategies.coffeechain_strategy.CoffeeChainStrategy.requires_approval", return_value=True)
    def test_create_booking_pending_if_approval_required(
        self, mock_approval, mock_deduct, mock_usd, mock_get_offer
    ):
        """
        Test that a booking is marked as 'pending_approval' if approval is required.

        Mocks:
            - get_offer_by_id
            - to_usd
            - deduct_points
            - requires_approval
        """
        self.valid_payload["payment"]["amount"] = 20000
        mock_get_offer.return_value = self.mock_offer_data

        response = self.client.post(
            "/api/bookings/",
            data=json.dumps(self.valid_payload),
            content_type="application/json",
            **self.auth_headers
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["data"]["status"], "pending_approval")
        self.assertTrue(response.json()["data"]["approval_required"])

    @patch("bookings.utils.booking_logic.get_offer_by_id")
    def test_cabin_class_not_allowed_returns_400(self, mock_get_offer):
        """
        Test that a booking with a disallowed cabin class is rejected with 400.

        Mocks:
            - get_offer_by_id returns offer with 'business' class.
        """
        mock_get_offer.return_value = {
            "slices": [
                {
                    "segments": [
                        {
                            "origin": {"iata_code": "JFK"},
                            "destination": {"iata_code": "LAX"},
                            "departing_at": "2025-07-01T08:00:00Z",
                            "passengers": [{"cabin_class": "business"}]
                        }
                    ]
                }
            ]
        }

        response = self.client.post(
            "/api/bookings/",
            data=json.dumps(self.valid_payload),
            content_type="application/json",
            **self.auth_headers
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("not allowed", response.json()["error"]["detail"])
