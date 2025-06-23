from django.urls import path
from bookings.handlers import BookingHandler, BookingDetailHandler, BookingCancelHandler, BookingSearchHandler

urlpatterns = [
    path("bookings/", BookingHandler.as_view(), name="booking-handler"),
    path("bookings/<int:booking_id>/", BookingDetailHandler.as_view(), name="booking-detail-handler"),
    path("bookings/<int:booking_id>/cancel", BookingCancelHandler.as_view(), name="booking-cancel-handler"),
    path("bookings/search", BookingSearchHandler.as_view(), name="booking-search-handler"),
]
