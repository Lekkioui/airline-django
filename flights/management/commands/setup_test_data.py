# ../airline-django/flights/management/commands/setup_test_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from flights.models import Airport, Flight, Passenger

class Command(BaseCommand):
    help = "Configure les données pour les tests automatisés"

    def handle(self, *args, **kwargs):
        # Nettoyage
        User.objects.all().delete()
        Airport.objects.all().delete()

        # Admin
        User.objects.create_superuser('anasse', 'anasse@gmail.com', 'anasse')

        # Data
        jfk = Airport.objects.create(code='JFK', city='New York City')
        lhr = Airport.objects.create(code='LHR', city='London')
        f = Flight.objects.create(origin=jfk, destination=lhr, duration=415)
        
        for i in range(10):
            Passenger.objects.create(first=f'Passenger{i}', last='Test')
            
        self.stdout.write(self.style.SUCCESS('Données de test initialisées avec succès'))