from django.urls import path
from .handlers import AdminBookingListHandler, AdminBookingDetailHandler

urlpatterns = [
    path("bookings/", AdminBookingListHandler.as_view(), name="admin-booking-list"),
    path("bookings/<int:booking_id>/", AdminBookingDetailHandler.as_view(), name="admin-booking-detail"),
]
