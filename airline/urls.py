from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('flights/', include('flights.urls')),
    path('users/', include('users.urls')),
    path('', lambda request: redirect('index_flights'), name='home'),
]