from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from django.utils.timezone import now


class HealthCheckHandler(APIView):
    """
    Health check endpoint for service monitoring.

    This handler serves as a public endpoint to verify that the backend
    is responsive and running as expected.

    Attributes:
        authentication_classes (list): Empty list disables DRF authentication.
        permission_classes (list): Empty list allows unrestricted access.
    """

    authentication_classes = []  # Disable authentication entirely for this endpoint
    permission_classes = []  # Allow all clients regardless of permissions

    def get(self, request):
        """
        Handle GET requests to the health check endpoint.

        Returns:
            Response: JSON payload with service status metadata, including:
                - `status`: A simple status string ("ok").
                - `timestamp`: ISO-8601 formatted UTC timestamp.
                - `environment`: Current running environment (e.g., development, test).
                - `version`: API version number.
        """
        return Response({
            "status": "ok",
            "timestamp": now().isoformat(),
            "environment": settings.ENVIRONMENT,
            "version": settings.VERSION,
        })
