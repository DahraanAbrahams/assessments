from rest_framework import serializers
from bookings.models import Booking
from tenants.serializers import TenantSerializer


class AdminBookingSerializer(serializers.ModelSerializer):
    """
    Admin serializer for booking records across all tenants.

    This serializer includes:
        - Booking metadata
        - Nested tenant object (excluding config and timestamps)

    The tenant is serialized using the full TenantSerializer but stripped
    down in the final response to only include relevant metadata
    (e.g., id, name, slug). This avoids exposing sensitive or verbose fields
    like config, created_at, and updated_at.

    Attributes:
        tenant (TenantSerializer): Nested read-only tenant data attached to the booking.
    """

    tenant = TenantSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "tenant",
            "member_id",
            "status",
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
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        """
        Customize the serialized output to exclude verbose or sensitive tenant fields.

        This method modifies the default serialized representation by removing
        unnecessary keys from the nested tenant object such as 'config',
        'created_at', and 'updated_at'.

        Args:
            instance (Booking): The booking model instance being serialized.

        Returns:
            dict: A dictionary representing the serialized booking with a trimmed tenant object.
        """
        rep = super().to_representation(instance)

        if "tenant" in rep and isinstance(rep["tenant"], dict):
            rep["tenant"].pop("config", None)
            rep["tenant"].pop("created_at", None)
            rep["tenant"].pop("updated_at", None)

        return rep
