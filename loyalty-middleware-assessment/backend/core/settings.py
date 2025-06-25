from pathlib import Path
from decouple import config
from corsheaders.defaults import default_headers, default_methods

# ===================================================
#               BASE DIRECTORY
# ===================================================
BASE_DIR = Path(__file__).resolve().parent.parent


# ===================================================
#               SECURITY SETTINGS
# ===================================================
SECRET_KEY = config("SECRET_KEY", default="unsafe-default-key")

DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = ["*"]


# ===================================================
#               APPLICATION DEFINITION
# ===================================================
INSTALLED_APPS = [
    # Django core apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party apps
    'rest_framework',
    "drf_yasg",
    "corsheaders",

    # Project-specific apps
    "bookings",
    "flights",
    "tenants",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",

    'corsheaders.middleware.CorsMiddleware',

    # Custom middleware for multi-tenant request handling
    "tenants.utils.middleware.TenantMiddleware",

    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
CORS_ALLOW_HEADERS = list(default_headers) + [
    'X-Internal-Access',
]

CORS_ALLOW_METHODS = list(default_methods) + [
    'OPTIONS',
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# WSGI entry point for deployment (e.g., gunicorn)
WSGI_APPLICATION = "core.wsgi.application"


# ===================================================
#               DRF CONFIGURATION
# ===================================================
REST_FRAMEWORK = {
    # Use RFC 7807-compliant exception responses
    "EXCEPTION_HANDLER": "utils.exception_handler.rfc7807_exception_handler",

    # Apply tenant-based rate limiting
    "DEFAULT_THROTTLE_CLASSES": [
        "utils.throttling.TenantThrottle",
    ],

    # Default global throttle rate (can be overridden per tenant)
    "DEFAULT_THROTTLE_RATES": {
        "tenant": "100/min",  # Fallback limit
    },
}


# ===================================================
#               DATABASE CONFIGURATION
# ===================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DATABASE_NAME"),
        "USER": config("DATABASE_USER"),
        "PASSWORD": config("DATABASE_PASSWORD"),
        "HOST": config("DATABASE_HOST"),
        "PORT": config("DATABASE_PORT", cast=int),
    }
}


# ===================================================
#               PASSWORD VALIDATION
# ===================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ===================================================
#               INTERNATIONALIZATION
# ===================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ===================================================
#               STATIC FILES
# ===================================================
STATIC_URL = "static/"


# ===================================================
#               DEFAULT PRIMARY KEY FIELD TYPE
# ===================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ===================================================
#               EXTERNAL SERVICE CONFIG
# ===================================================
DUFFEL_API_KEY = config("DUFFEL_API_KEY")
DUFFEL_API_URL = config("DUFFEL_API_URL")
DUFFEL_API_VERSION = config("DUFFEL_API_VERSION")

COFFEECHAIN_API_URL = config("COFFEECHAIN_API_URL")
TELCOCORP_API_URL = config("TELCOCORP_API_URL")
FINTECHAPP_API_URL = config("FINTECHAPP_API_URL")

COFFEECHAIN_API_KEY = config("COFFEECHAIN_API_KEY")
TELCOCORP_CLIENT_ID = config("TELCOCORP_CLIENT_ID")
TELCOCORP_CLIENT_SECRET = config("TELCOCORP_CLIENT_SECRET")
FINTECHAPP_JWT_SECRET = config("FINTECHAPP_JWT_SECRET")


# ===================================================
#               APP ENVIRONMENT SETTINGS
# ===================================================
LOG_LEVEL = config("LOG_LEVEL", default="INFO")
ENVIRONMENT = config("ENVIRONMENT", default="development")
VERSION = config("VERSION", default="v1")


# ===================================================
#               RATE LIMITING CONFIG
# ===================================================
# Default per-tenant rate limit if not configured
RATE_LIMIT = config("RATE_LIMIT", default=100, cast=int)


# ===================================================
#               DJANGO CACHING CONFIG
# ===================================================
# Use local in-memory cache for request throttling, etc.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-loyalty-cache",
        "TIMEOUT": 300,  # Cache timeout in seconds (5 minutes)
    }
}


# ===================================================
#               SWAGGER / DRF-YASG SETTINGS
# ===================================================
SWAGGER_SETTINGS = {
    "USE_SESSION_AUTH": False,
    "SECURITY_DEFINITIONS": {
        "Tenant Header": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Tenant-ID",
            "description": "Tenant slug: `coffeechain`, `telcocorp`, or `fintechapp`",
        },
        "CoffeeChain API Key": {
            "type": "apiKey",
            "in": "header",
            "name": "X-CC-API-Key",
            "description": "API Key for CoffeeChain: `test_cc_api_key_12345`",
        },
        "CoffeeChain Member ID": {
            "type": "apiKey",
            "in": "header",
            "name": "X-CC-Member-ID",
            "description": "CoffeeChain Member ID (e.g. `CC1234567`)",
        },
        "TelcoCorp Bearer Token": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "OAuth2",
            "description": "OAuth2 Bearer token for TelcoCorp (get from /oauth/token)",
        },
        "TelcoCorp Customer ID": {
            "type": "apiKey",
            "in": "header",
            "name": "X-TC-Customer-ID",
            "description": "TelcoCorp Customer ID (e.g. `TC-ABC123`)",
        },
        "FintechApp JWT Token": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token for FintechApp",
        },
        "FintechApp User ID": {
            "type": "apiKey",
            "in": "header",
            "name": "X-FA-User-ID",
            "description": "FintechApp User ID (e.g. `FA_12345678`)",
        },
    },
    "DEFAULT_MODEL_RENDERING": "example",
    "DOC_EXPANSION": "none",
}
