from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index_flights"),
    path("search/", views.search, name="search"),
    path("<int:flight_id>", views.flight, name="flight"),
    path("<int:flight_id>/book", views.book, name="book"),
    path("<int:flight_id>/remove/<int:passenger_id>", views.remove, name="remove"),
    path("passenger/<int:passenger_id>", views.passenger, name="passenger"),
    path("passenger/<int:passenger_id>/remove/<int:flight_id>",
         views.remove_flight_from_passenger, name="remove_flight_from_passenger"),
]