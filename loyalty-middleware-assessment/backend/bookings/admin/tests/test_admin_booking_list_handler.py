from datetime import timedelta
from django.utils import timezone
from django.test import TestCase
from bookings.models import Booking
from tenants.models import Tenant


class AdminBookingListHandlerTests(TestCase):
    """
    Unit tests for the AdminBookingListHandler.

    These tests verify the behaviour of the `/api/v1/admin/bookings/` endpoint,
    including support for filtering by tenant, status, date range, and combinations.
    """

    def setUp(self):
        """
        Set up test data for all test cases.

        Creates:
            - 2 tenants: CoffeeChain and TelcoCorp
            - 3 bookings with varying attributes across those tenants
        """
        self.tenant1 = Tenant.objects.create(name="CoffeeChain", slug="coffeechain")
        self.tenant2 = Tenant.objects.create(name="TelcoCorp", slug="telcocorp")

        now = timezone.now()

        self.booking1 = Booking.objects.create(
            tenant=self.tenant1,
            member_id="M123",
            status="confirmed",
            origin="CPT",
            destination="JNB",
            departure_date=now.date(),
            return_date=now.date() + timedelta(days=2),
            cabin_class="economy",
            num_passengers=1,
            amount=100,
            loyalty_currency="Stars",
            airline="CC",
            flight_number="CC123",
            reference="REF-001",
        )
        self.booking1.created_at = now - timedelta(days=2)
        self.booking1.save(update_fields=["created_at"])

        self.booking2 = Booking.objects.create(
            tenant=self.tenant1,
            member_id="M456",
            status="cancelled",
            origin="JNB",
            destination="CPT",
            departure_date=now.date(),
            return_date=now.date() + timedelta(days=3),
            cabin_class="business",
            num_passengers=2,
            amount=200,
            loyalty_currency="Stars",
            airline="CC",
            flight_number="CC456",
            reference="REF-002",
        )
        self.booking2.created_at = now - timedelta(days=1)
        self.booking2.save(update_fields=["created_at"])

        self.booking3 = Booking.objects.create(
            tenant=self.tenant2,
            member_id="M789",
            status="confirmed",
            origin="CPT",
            destination="LHR",
            departure_date=now.date(),
            return_date=now.date() + timedelta(days=7),
            cabin_class="economy",
            num_passengers=1,
            amount=300,
            loyalty_currency="Points",
            airline="TC",
            flight_number="TC789",
            reference="REF-003",
        )
        self.booking3.created_at = now
        self.booking3.save(update_fields=["created_at"])

    def test_get_all_bookings(self):
        """
        Test retrieving all bookings without any filters.

        Returns:
            - 200 OK
            - All bookings across tenants (3 total)
        """
        response = self.client.get("/api/v1/admin/bookings/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["bookings"]), 3)
        self.assertEqual(response.data["data"]["pagination"]["total"], 3)
        self.assertEqual(response.data["data"]["pagination"]["offset"], 0)

    def test_filter_by_tenant(self):
        """
        Test filtering bookings by tenant slug.

        Query Params:
            - tenant=coffeechain

        Returns:
            - 200 OK
            - Only bookings for tenant1 (CoffeeChain)
        """
        response = self.client.get("/api/v1/admin/bookings/?tenant=coffeechain")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["bookings"]), 2)
        for booking in response.data["data"]["bookings"]:
            self.assertEqual(booking["tenant_slug"], "coffeechain")

    def test_filter_by_status(self):
        """
        Test filtering bookings by booking status.

        Query Params:
            - status=confirmed

        Returns:
            - 200 OK
            - Only bookings with status 'confirmed'
        """
        response = self.client.get("/api/v1/admin/bookings/?status=confirmed")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["bookings"]), 2)
        for booking in response.data["data"]["bookings"]:
            self.assertEqual(booking["status"], "confirmed")

    def test_filter_by_date_range(self):
        """
        Test filtering bookings by creation date range.

        Query Params:
            - from_date=YYYY-MM-DD
            - to_date=YYYY-MM-DD

        Returns:
            - 200 OK
            - Only bookings created within the specified date window
        """
        from_date = (timezone.now() - timedelta(days=2)).date().isoformat()
        to_date = timezone.now().date().isoformat()

        response = self.client.get(f"/api/v1/admin/bookings/?from_date={from_date}&to_date={to_date}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["bookings"]), 3)

    def test_combined_filters(self):
        """
        Test filtering by both tenant and booking status.

        Query Params:
            - tenant=coffeechain
            - status=cancelled

        Returns:
            - 200 OK
            - Only bookings for CoffeeChain with status 'cancelled'
        """
        response = self.client.get("/api/v1/admin/bookings/?tenant=coffeechain&status=cancelled")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["bookings"]), 1)
        booking = response.data["data"]["bookings"][0]
        self.assertEqual(booking["status"], "cancelled")
        self.assertEqual(booking["tenant_slug"], "coffeechain")
