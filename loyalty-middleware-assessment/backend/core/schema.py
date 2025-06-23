from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Loyalty Middleware API",
        default_version="v1",
        description="Multi-tenant API for booking flights with loyalty currencies.",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)
