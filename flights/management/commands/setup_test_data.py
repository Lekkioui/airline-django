from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from flights.models import Airport, Flight, Passenger

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        Passenger.objects.all().delete()
        Flight.objects.all().delete()
        Airport.objects.all().delete()
        User.objects.filter(username='anasse').delete()

        User.objects.create_superuser('anasse', 'anasse@gmail.com', 'anasse')
        jfk = Airport.objects.create(code='JFK', city='New York City')
        lhr = Airport.objects.create(code='LHR', city='London')
        Flight.objects.create(origin=jfk, destination=lhr, duration=415)

        for i in range(15):
            Passenger.objects.create(first=f'Passenger{i}', last='Test')