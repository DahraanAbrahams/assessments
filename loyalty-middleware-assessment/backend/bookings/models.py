from django.db import models
from tenants.models import Tenant


class Booking(models.Model):
    """
    Represents a flight booking made using loyalty rewards through a tenant's program.

    This model captures detailed metadata about the flight, passenger, loyalty transaction,
    and third-party integration (e.g. Duffel), supporting auditing and external traceability.

    Attributes:
        id (int): Primary key for the booking.
        tenant (Tenant): Foreign key to the associated tenant (e.g. CoffeeChain).
        member_id (str): Identifier of the loyalty member (e.g. program-specific user ID).
        origin (str): IATA code of the departure airport (e.g. 'CPT').
        destination (str): IATA code of the arrival airport (e.g. 'JNB').
        departure_date (date): Date of outbound flight.
        return_date (Optional[date]): Date of return flight if round-trip; null if one-way.
        cabin_class (str): Cabin class selected for the flight (e.g. 'economy').
        num_passengers (int): Number of passengers included in the booking.
        amount (Decimal): Loyalty amount redeemed for the booking.
        loyalty_currency (str): The name of the loyalty currency used (e.g. 'Stars').
        airline (Optional[str]): Airline code used for the booking (e.g. 'BA', 'LH').
        flight_number (Optional[str]): Flight number from the airline or aggregator.
        reference (Optional[str]): External booking reference ID (e.g. Duffel or airline).
        status (str): Booking status. One of: 'pending', 'confirmed', 'failed', 'cancelled'.
        created_at (datetime): Timestamp when the booking was created.
        updated_at (datetime): Timestamp when the booking was last updated.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.BigAutoField(primary_key=True)

    # Tenant and loyalty member info
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="bookings",
        help_text="Owning tenant for this booking (e.g. CoffeeChain)"
    )
    member_id = models.CharField(
        max_length=100,
        help_text="Loyalty member or user ID (e.g. CoffeeChain Member ID)"
    )

    # Flight and itinerary details
    origin = models.CharField(max_length=3, help_text="IATA origin airport code (e.g. CPT)")
    destination = models.CharField(max_length=3, help_text="IATA destination airport code (e.g. JNB)")
    departure_date = models.DateField(help_text="Outbound departure date")
    return_date = models.DateField(
        null=True,
        blank=True,
        help_text="Return date (if round trip). Leave blank for one-way."
    )
    cabin_class = models.CharField(max_length=20, help_text="Cabin class (e.g. economy, business)")
    num_passengers = models.PositiveIntegerField(default=1, help_text="Number of passengers")

    # Loyalty and pricing
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Loyalty amount spent (e.g. 1200 points)"
    )
    loyalty_currency = models.CharField(
        max_length=20,
        help_text="The loyalty currency used (e.g. Stars, Points, Coins)"
    )

    # External metadata
    airline = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Airline code (e.g. BA, LH)"
    )
    flight_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Flight number assigned by airline"
    )
    reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="External reference ID from provider (e.g. Duffel booking ID)"
    )

    # Lifecycle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Current status of the booking"
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the booking was cancelled"
    )

    # Refund tracking (optional for assessment but matches API spec)
    refund_status = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Status of refund processing (e.g. processed, pending, failed)"
    )

    refund_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount refunded to loyalty account"
    )

    refund_processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when refund was processed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.status.upper()}] {self.tenant.slug} {self.member_id} | {self.origin} → {self.destination}"

