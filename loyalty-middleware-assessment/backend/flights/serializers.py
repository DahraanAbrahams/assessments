from rest_framework import serializers
from typing import Dict, Any


class PassengerCountSerializer(serializers.Serializer):
    """
    Serializer for validating the passenger counts in a flight search request.

    Fields:
        adults (int): Required. Must be >= 1.
        children (int): Optional. Must be >= 0. Defaults to 0.
        infants (int): Optional. Must be >= 0. Defaults to 0.
    """

    adults = serializers.IntegerField(min_value=1, required=True)
    children = serializers.IntegerField(min_value=0, required=False, default=0)
    infants = serializers.IntegerField(min_value=0, required=False, default=0)


class FlightSearchRequestSerializer(serializers.Serializer):
    """
    Serializer for validating flight search input from clients.

    Fields:
        origin (str): IATA code of the origin airport.
        destination (str): IATA code of the destination airport.
        departure_date (date): Outbound flight departure date.
        return_date (date): Optional. Return flight date.
        passengers (PassengerCountSerializer): Nested object with passenger counts.
        cabin_class (str): Cabin class. One of: economy, premium_economy, business, first.
        currency (str): ISO currency code (e.g., USD).

    Raises:
        serializers.ValidationError: If return date is earlier than departure date.
    """

    origin = serializers.CharField(max_length=3)
    destination = serializers.CharField(max_length=3)
    departure_date = serializers.DateField()
    return_date = serializers.DateField(required=False, allow_null=True)
    passengers = PassengerCountSerializer()
    cabin_class = serializers.ChoiceField(choices=["economy", "premium_economy", "business", "first"])
    currency = serializers.CharField(max_length=3)

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform cross-field validation.

        Ensures return_date (if provided) is not earlier than departure_date.

        Args:
            data (dict): Validated input data.

        Returns:
            dict: Cleaned and validated data.

        Raises:
            serializers.ValidationError: If return_date < departure_date.
        """
        return_date = data.get("return_date")
        departure_date = data["departure_date"]

        if return_date and return_date < departure_date:
            raise serializers.ValidationError("Return date cannot be before departure date.")

        return data
