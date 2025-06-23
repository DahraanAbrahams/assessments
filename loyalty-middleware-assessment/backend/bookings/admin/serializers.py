from rest_framework import serializers
from bookings.models import Booking


class AdminBookingSerializer(serializers.ModelSerializer):
    """
    Serializer for admin view of bookings.

    Includes key details useful for filtering, auditing, and analysis:
        - Tenant slug
        - Loyalty and passenger info
        - Flight info
        - Booking reference and timestamps
    """

    tenant_slug = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "member_id",
            "tenant_slug",
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

    def get_tenant_slug(self, obj):
        return obj.tenant.slug if obj.tenant else None
