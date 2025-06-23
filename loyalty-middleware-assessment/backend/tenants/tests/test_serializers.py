import unittest
from tenants.serializers import TenantSerializer


class TenantSerializerTests(unittest.TestCase):
    """
    Unit tests for the TenantSerializer using Python's built-in unittest library.

    These tests validate the behavior of the serializer under different `config` inputs,
    including valid JSON objects and malformed types.
    """

    def setUp(self) -> None:
        """
        Set up shared test data.

        Creates a base dictionary representing a valid tenant payload.
        """
        self.valid_data: dict = {
            "name": "CoffeeChain",
            "slug": "coffeechain",
            "config": {
                "api_key": "test_key",
                "some_setting": True
            },
        }

    def test_valid_data_is_valid(self) -> None:
        """
        Test that the serializer accepts valid data.

        Asserts:
            - is_valid() returns True
            - serializer.errors is empty
        """
        serializer = TenantSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_config_is_not_valid(self) -> None:
        """
        Test that a non-dict `config` field results in validation failure.

        Asserts:
            - is_valid() returns False
            - 'config' is present in serializer.errors
        """
        invalid_data: dict = self.valid_data.copy()
        invalid_data["config"] = "not_a_dict"  # Should trigger config validation failure

        serializer = TenantSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("config", serializer.errors)
