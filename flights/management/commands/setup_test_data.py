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

        # Aéroports
        jfk = Airport.objects.create(code='JFK', city='New York City')
        lhr = Airport.objects.create(code='LHR', city='London')
        cdg = Airport.objects.create(code='CDG', city='Paris')
        dxb = Airport.objects.create(code='DXB', city='Dubai')
        hnd = Airport.objects.create(code='HND', city='Tokyo')
        lax = Airport.objects.create(code='LAX', city='Los Angeles')
        sin = Airport.objects.create(code='SIN', city='Singapore')
        ist = Airport.objects.create(code='IST', city='Istanbul')

        # Vols
        flights_data = [
            (jfk, lhr, 415, 'SCHEDULED', 50),
            (cdg, dxb, 360, 'SCHEDULED', 40),
            (lhr, hnd, 680, 'BOARDING',  30),
            (lax, jfk, 310, 'SCHEDULED', 60),
            (dxb, sin, 270, 'DEPARTED',  45),
            (hnd, lax, 540, 'SCHEDULED', 35),
            (ist, cdg, 195, 'CANCELLED', 50),
            (sin, lhr, 750, 'SCHEDULED', 40),
        ]

        flights = []
        for origin, dest, duration, status, capacity in flights_data:
            f = Flight.objects.create(
                origin=origin,
                destination=dest,
                duration=duration,
                status=status,
                capacity=capacity,
            )
            flights.append(f)

        # Passengers uniquement sur le premier vol (pour les tests)
        flight = flights[0]
        passengers_data = [
            ('Harry',     'Potter',     'harry@hogwarts.com',     'HP123456', 'ECONOMY'),
            ('Hermione',  'Granger',    'hermione@hogwarts.com',  'HG123456', 'BUSINESS'),
            ('Ron',       'Weasley',    'ron@hogwarts.com',       'RW123456', 'ECONOMY'),
            ('Albus',     'Dumbledore', 'albus@hogwarts.com',     'AD123456', 'FIRST'),
            ('Severus',   'Snape',      'severus@hogwarts.com',   'SS123456', 'BUSINESS'),
            ('Draco',     'Malfoy',     'draco@hogwarts.com',     'DM123456', 'FIRST'),
            ('Luna',      'Lovegood',   'luna@hogwarts.com',      'LL123456', 'ECONOMY'),
            ('Neville',   'Longbottom', 'neville@hogwarts.com',   'NL123456', 'ECONOMY'),
            ('Ginny',     'Weasley',    'ginny@hogwarts.com',     'GW123456', 'BUSINESS'),
            ('Sirius',    'Black',      'sirius@hogwarts.com',    'SB123456', 'FIRST'),
            ('Rubeus',    'Hagrid',     'rubeus@hogwarts.com',    'RH123456', 'ECONOMY'),
            ('Minerva',   'McGonagall', 'minerva@hogwarts.com',   'MM123456', 'BUSINESS'),
            ('Tom',       'Riddle',     'tom@hogwarts.com',       'TR123456', 'FIRST'),
            ('Bellatrix', 'Lestrange',  'bellatrix@hogwarts.com', 'BL123456', 'ECONOMY'),
            ('Cedric',    'Diggory',    'cedric@hogwarts.com',    'CD123456', 'BUSINESS'),
        ]

        for first, last, email, passport, seat_class in passengers_data:
            seat_number = flight.next_seat(seat_class)
            p = Passenger.objects.create(
                first=first, last=last,
                email=email,
                passport_number=passport,
                seat_class=seat_class,
                seat_number=seat_number,
            )
            p.flights.add(flight)

        self.stdout.write(self.style.SUCCESS(
            f'Test data created: {len(flights)} flights, {len(passengers_data)} passengers'
        ))