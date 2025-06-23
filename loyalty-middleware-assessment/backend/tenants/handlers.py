from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from tenants.models import Tenant
from tenants.serializers import TenantSerializer
from utils.rfc7807 import missing_tenant_header_error


class TenantListHandler(APIView):
    """
    API endpoint to list all registered tenants and their configurations.

    This endpoint returns metadata and config values for each known tenant.

    Authentication:
        None (open for admin/dev debugging)

    Returns:
        200 OK: List of tenants with their metadata and config.
    """

    def get(self, request):
        """
        Handle GET request for listing all tenant configurations.

        Requires 'X-Internal-Access: true' header for security.

        Args:
            request (Request): DRF request object.

        Returns:
            Response: Serialized list of tenants with config details.
        """
        internal_header = request.headers.get("X-Internal-Access")
        if internal_header != "true":
            return missing_tenant_header_error(
                detail="Missing or invalid internal access header.",
                instance=request.path,
            )

        tenants = Tenant.objects.all()
        serializer = TenantSerializer(tenants, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)
