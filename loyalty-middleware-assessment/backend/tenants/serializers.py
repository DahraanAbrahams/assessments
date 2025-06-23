from rest_framework import serializers
from tenants.models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    """
    Serializer for the Tenant model.

    This serializer exposes the core tenant metadata and ensures the
    `config` field is a valid dictionary. It is used for read and write
    operations involving tenant configuration.

    Fields:
        id (int): Auto-incremented primary key.
        name (str): Human-readable name of the tenant (e.g., "CoffeeChain").
        slug (str): Unique identifier used in headers and lookups (e.g., "coffeechain").
        config (dict): JSON field storing tenant-specific config (e.g., API keys, rate limits).
        created_at (datetime): Timestamp when the tenant was created.
        updated_at (datetime): Timestamp when the tenant was last updated.
    """

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "slug",
            "config",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_config(self, value: dict) -> dict:
        """
        Optionally validate the structure of the `config` JSON field.

        Ensures the config is a dictionary. This method can be extended
        to enforce required keys, validate data types, or apply
        tenant-specific schema rules.

        Args:
            value (dict): The config payload submitted in the request.

        Returns:
            dict: The validated config dictionary.

        Raises:
            serializers.ValidationError: If the input is not a dictionary.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Config must be a valid JSON object.")
        return value
