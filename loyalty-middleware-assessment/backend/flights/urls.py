from django.urls import path
from flights.handlers import FlightSearchHandler

urlpatterns = [
    path("search", FlightSearchHandler.as_view(), name="flight-search"),
]
