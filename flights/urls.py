from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index_flights"),
    path("search/", views.search, name="search"),
    path("<int:flight_id>", views.flight, name="flight"),
    path("<int:flight_id>/book", views.book, name="book"),
    path("<int:flight_id>/remove/<int:passenger_id>", views.remove, name="remove"),
]