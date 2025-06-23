from django.urls import path
from .handlers import AdminBookingListHandler

urlpatterns = [
    path("bookings/", AdminBookingListHandler.as_view(), name="admin-booking-list"),
]
