"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from core.handlers import HealthCheckHandler

# Define the Swagger schema view directly
schema_view = get_schema_view(
    openapi.Info(
        title="Loyalty Middleware API",
        default_version="v1",
        description="Multi-tenant loyalty booking API with per-tenant rules and authentication.",
        terms_of_service="https://example.com/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="MIT"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path("api/v1/health", HealthCheckHandler.as_view(), name="health-check-v1"),
    path("api/v1/tenants/", include("tenants.urls")),
    path("api/", include("bookings.urls")),
    path("api/v1/flights/", include("flights.urls")),
    path("api/v1/admin/", include("bookings.admin.urls")),

    # Swagger/OpenAPI endpoints
    re_path(r"^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
