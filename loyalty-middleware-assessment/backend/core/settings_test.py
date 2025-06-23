"""
Test settings for the loyalty middleware system.

Overrides only what is necessary for running tests against a dedicated database.
"""

from .settings import *  # noqa
from decouple import config

# Test-specific database configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("TEST_DATABASE_NAME", default="test_loyalty_db"),
        "USER": config("DATABASE_USER"),
        "PASSWORD": config("DATABASE_PASSWORD"),
        "HOST": config("DATABASE_HOST", default="mysql"),
        "PORT": config("DATABASE_PORT", cast=int, default=3306),
        "OPTIONS": {
            "autocommit": True,
        },
    }
}

# Enable debug mode and mark environment
DEBUG = True
ENVIRONMENT = "test"
