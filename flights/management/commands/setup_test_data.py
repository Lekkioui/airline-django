from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from flights.models import Airport, Flight, Passenger

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Suppression propre (Ordre important pour les clés étrangères)
        Passenger.objects.all().delete()
        Flight.objects.all().delete()
        Airport.objects.all().delete()
        User.objects.filter(username='anasse').delete()

        # Création des données de base
        User.objects.create_superuser('anasse', 'anasse@gmail.com', 'anasse')
        jfk = Airport.objects.create(code='JFK', city='New York City')
        lhr = Airport.objects.create(code='LHR', city='London')
        f = Flight.objects.create(origin=jfk, destination=lhr, duration=415)
        
        # On crée exactement 10 passagers pour tes tests de logique
        for i in range(10):
            Passenger.objects.create(first=f'Passenger{i}', last='Test')