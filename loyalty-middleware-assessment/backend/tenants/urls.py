from django.urls import path
from tenants.handlers import TenantListHandler

urlpatterns = [
    path("", TenantListHandler.as_view(), name="tenant-list"),
]
