from rest_framework import serializers
from bookings.models import Booking
from tenants.serializers import TenantSerializer


class PassengerSerializer(serializers.Serializer):
    """
    Minimal passenger serializer for assessment.
    """
    first_name = serializers.CharField()
    last_name = serializers.CharField()


class PaymentSerializer(serializers.Serializer):
    """
    Minimal payment serializer for assessment.
    """
    amount = serializers.IntegerField()
    currency = serializers.CharField()


class ContactSerializer(serializers.Serializer):
    """
    Minimal contact serializer for assessment.
    """
    email = serializers.EmailField()
    phone = serializers.CharField()


class BookingCreateSerializer(serializers.Serializer):
    """
    Simplified serializer for booking creation (assessment version).

    Required Fields:
        - flight_id: Duffel offer ID
        - cabin_class: 'economy' or 'business'
        - passengers: List with first and last names
        - payment: amount and currency only
        - contact: phone and email
    """
    flight_id = serializers.CharField()
    cabin_class = serializers.ChoiceField(choices=["economy", "business"])
    passengers = PassengerSerializer(many=True)
    payment = PaymentSerializer()
    contact = ContactSerializer()

    def validate(self, data):
        if not data["passengers"]:
            raise serializers.ValidationError("At least one passenger must be included.")
        if data["payment"]["amount"] <= 0:
            raise serializers.ValidationError("Payment amount must be greater than zero.")
        return data



class BookingDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for returning detailed booking data in GET/list endpoints.

    Fields:
        id (int): Internal booking ID.
        tenant (dict): Serialized tenant object.
        member_id (str): Loyalty member ID.
        origin (str): Departure airport code.
        destination (str): Arrival airport code.
        departure_date (date): Departure date.
        return_date (date): Optional return date.
        cabin_class (str): Cabin class ('economy', 'business').
        num_passengers (int): Passenger count.
        amount (Decimal): Loyalty amount.
        loyalty_currency (str): Loyalty currency name.
        airline (str): Optional airline code.
        flight_number (str): Optional flight number.
        reference (str): Optional external reference.
        status (str): Booking status.
        created_at (datetime): Creation timestamp.
        updated_at (datetime): Last modified timestamp.
    """

    tenant = TenantSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "tenant",
            "member_id",
            "origin",
            "destination",
            "departure_date",
            "return_date",
            "cabin_class",
            "num_passengers",
            "amount",
            "loyalty_currency",
            "airline",
            "flight_number",
            "reference",
            "status",
            "created_at",
            "updated_at",
        ]
