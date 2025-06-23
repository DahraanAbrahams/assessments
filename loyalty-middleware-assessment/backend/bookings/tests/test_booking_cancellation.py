"""
Booking Cancellation Tests

Covers:
- Standard cancellation
- Cancellation with refund
- Error cases: already cancelled, invalid booking
"""

import json
from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase, Client
from bookings.models import Booking
from tenants.models import Tenant


class BookingCancelHandlerTests(TestCase):
    """
    Unit tests for cancelling bookings and processing refunds.
    """

    def setUp(self):
        self.client = Client()

        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)

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
            }
        )

        self.headers = {
            "HTTP_X_TENANT_ID": self.tenant.slug,
            "HTTP_X_CC_API_KEY": "test-key",
            "HTTP_X_CC_MEMBER_ID": "member123",
        }

        self.booking = Booking.objects.create(
            tenant=self.tenant,
            member_id="member123",
            origin="CPT",
            destination="JNB",
            departure_date=self.tomorrow,
            cabin_class="economy",
            num_passengers=1,
            amount=9000,
            loyalty_currency="stars",
            status="confirmed"
        )

    def test_cancel_booking_without_refund(self):
        """
        Should cancel booking and return 200 with cancellation status.
        """
        response = self.client.post(
            f"/api/bookings/{self.booking.id}/cancel",
            data=json.dumps({"reason": "test"}),
            content_type="application/json",
            **self.headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["status"], "cancelled")

    @patch("bookings.services.strategies.coffeechain_strategy.CoffeeChainStrategy.refund_points")
    def test_cancel_booking_with_refund(self, mock_refund):
        """
        Should cancel booking and return refund section in response.
        """
        response = self.client.post(
            f"/api/bookings/{self.booking.id}/cancel",
            data=json.dumps({"reason": "test", "refund_requested": True}),
            content_type="application/json",
            **self.headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["status"], "cancelled")
        self.assertIn("refund", data)
        self.assertEqual(data["refund"]["status"], "processed")
        mock_refund.assert_called_once_with(self.booking.amount)

    def test_cancel_already_cancelled_booking(self):
        """
        Should return 400 if booking was already cancelled.
        """
        self.booking.status = "cancelled"
        self.booking.save()

        response = self.client.post(
            f"/api/bookings/{self.booking.id}/cancel",
            data=json.dumps({"reason": "repeat cancel"}),
            content_type="application/json",
            **self.headers
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("already cancelled", response.json()["error"]["detail"])

    def test_cancel_nonexistent_booking(self):
        """
        Should return 404 for invalid booking ID.
        """
        response = self.client.post(
            "/api/bookings/9999/cancel",
            data=json.dumps({"reason": "invalid"}),
            content_type="application/json",
            **self.headers
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["error"]["detail"].lower())
