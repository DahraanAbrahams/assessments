from datetime import date, timedelta
from django.test import TestCase, Client
from tenants.models import Tenant
from bookings.models import Booking


class BookingSearchHandlerTests(TestCase):
    """
    Unit tests for BookingSearchHandler endpoint.

    Tests search behavior using partial `member_id` matches,
    scoped per tenant.
    """

    def setUp(self):
        """
        Create a test tenant, headers, and sample bookings.
        """
        self.client = Client()

        self.tenant = Tenant.objects.create(
            name="CoffeeChain",
            slug="coffeechain",
            auth_method="api_key",
            base_url="https://api.coffeechain.com",
            config={
                "api_key": "test-key",
                "auth_header": "X-CC-API-Key",
                "id_header": "X-CC-Member-ID",
                "allowed_cabin_class": "economy",
            },
        )

        self.headers = {
            "HTTP_X_TENANT_ID": self.tenant.slug,
            "HTTP_X_CC_API_KEY": self.tenant.config["api_key"],
        }

        today = date.today()
        departure = today + timedelta(days=1)

        # Create matching and non-matching bookings
        Booking.objects.create(
            tenant=self.tenant,
            member_id="user_12345",
            origin="CPT",
            destination="JNB",
            departure_date=departure,
            cabin_class="economy",
            num_passengers=1,
            amount=8000,
            loyalty_currency="stars",
            status="confirmed",
        )
        Booking.objects.create(
            tenant=self.tenant,
            member_id="guest_999",
            origin="CPT",
            destination="JNB",
            departure_date=departure,
            cabin_class="economy",
            num_passengers=1,
            amount=7000,
            loyalty_currency="stars",
            status="confirmed",
        )

    def test_search_returns_matching_results(self):
        """
        Should return bookings matching partial member_id.
        """
        response = self.client.get("/api/bookings/search?q=user", **self.headers)
        self.assertEqual(response.status_code, 200)
        results = response.json()["data"]["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["member_id"], "user_12345")

    def test_search_no_match_returns_empty_list(self):
        """
        Should return an empty list if no bookings match query.
        """
        response = self.client.get("/api/bookings/search?q=foobar", **self.headers)
        self.assertEqual(response.status_code, 200)
        results = response.json()["data"]["results"]
        self.assertEqual(results, [])

    def test_search_without_q_param_returns_400(self):
        """
        Should return a validation error if query param is missing.
        """
        response = self.client.get("/api/bookings/search", **self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Query parameter 'q' is required", response.json()["error"]["detail"])
