import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from flights.models import Airport, Flight, Passenger, Booking
from datetime import date, timedelta
from decimal import Decimal

FIRST_NAMES = [
    'James', 'Emma', 'Oliver', 'Sophia', 'William', 'Isabella', 'Benjamin',
    'Mia', 'Lucas', 'Charlotte', 'Henry', 'Amelia', 'Alexander', 'Harper',
    'Mason', 'Evelyn', 'Ethan', 'Abigail', 'Daniel', 'Emily', 'Michael',
    'Elizabeth', 'Logan', 'Sofia', 'Jackson', 'Avery', 'Sebastian', 'Ella',
    'Jack', 'Scarlett', 'Aiden', 'Grace', 'Owen', 'Chloe', 'Samuel',
    'Victoria', 'Joseph', 'Riley', 'John', 'Aria', 'David', 'Lily',
    'Wyatt', 'Eleanor', 'Matthew', 'Hannah', 'Luke', 'Lillian', 'Asher',
    'Addison', 'Carter', 'Aubrey', 'Julian', 'Ellie', 'Grayson', 'Stella',
    'Leo', 'Natalie', 'Jayden', 'Zoe', 'Gabriel', 'Leah', 'Isaac', 'Hazel',
    'Levi', 'Violet', 'Anthony', 'Aurora', 'Dylan', 'Savannah', 'Lincoln',
    'Audrey', 'Ryan', 'Brooklyn', 'Nathan', 'Bella', 'Camden', 'Claire',
    'Connor', 'Skylar', 'Eli', 'Lucy', 'Caleb', 'Paisley', 'Nolan', 'Everly',
    'Aaron', 'Anna', 'Landon', 'Caroline', 'Adrian', 'Genesis', 'Jonathan',
    'Aaliyah', 'Nolan', 'Kennedy', 'Jeremiah', 'Kinsley', 'Easton', 'Allison',
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
    'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
    'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
    'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark',
    'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young', 'Allen', 'King',
    'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores', 'Green',
    'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell',
    'Carter', 'Roberts', 'Lekkioui', 'Benali', 'Alaoui', 'Tazi', 'Chraibi',
    'Mansouri', 'Idrissi', 'Berrada', 'Lamrani', 'Kettani', 'Fassi',
]


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write('Clearing existing data...')
        Booking.objects.all().delete()
        Passenger.objects.all().delete()
        Flight.objects.all().delete()
        Airport.objects.all().delete()
        User.objects.filter(username='anasse').delete()

        User.objects.create_superuser('anasse', 'anasse@gmail.com', 'anasse')

        airports_data = [
            ('JFK', 'New York City'), ('LHR', 'London'), ('CDG', 'Paris'),
            ('DXB', 'Dubai'), ('HND', 'Tokyo'), ('LAX', 'Los Angeles'),
            ('SIN', 'Singapore'), ('IST', 'Istanbul'), ('CMN', 'Casablanca'),
            ('AMS', 'Amsterdam'), ('FRA', 'Frankfurt'), ('BCN', 'Barcelona'),
            ('MAD', 'Madrid'), ('FCO', 'Rome'), ('BKK', 'Bangkok'),
        ]

        airports = {}
        for code, city in airports_data:
            airports[code] = Airport.objects.create(code=code, city=city)

        routes = [
            ('JFK', 'LHR', 415), ('JFK', 'CDG', 430), ('JFK', 'AMS', 420),
            ('JFK', 'FRA', 480), ('JFK', 'MAD', 450), ('JFK', 'FCO', 500),
            ('LHR', 'DXB', 390), ('LHR', 'HND', 680), ('LHR', 'SIN', 720),
            ('LHR', 'CMN', 180), ('LHR', 'JFK', 415), ('LHR', 'BKK', 660),
            ('CDG', 'DXB', 360), ('CDG', 'CMN', 150), ('CDG', 'IST', 210),
            ('CDG', 'BCN', 130), ('CDG', 'FCO', 140), ('CDG', 'BKK', 660),
            ('DXB', 'HND', 540), ('DXB', 'SIN', 270), ('DXB', 'LAX', 810),
            ('DXB', 'CMN', 420), ('DXB', 'BKK', 360), ('DXB', 'FCO', 300),
            ('LAX', 'JFK', 310), ('LAX', 'HND', 600), ('LAX', 'SIN', 870),
            ('LAX', 'CDG', 660), ('LAX', 'LHR', 640), ('LAX', 'DXB', 810),
            ('SIN', 'HND', 360), ('SIN', 'LHR', 750), ('SIN', 'BKK', 150),
            ('SIN', 'DXB', 270),
            ('IST', 'CDG', 195), ('IST', 'DXB', 240), ('IST', 'CMN', 270),
            ('IST', 'FRA', 210), ('IST', 'AMS', 230), ('IST', 'FCO', 180),
            ('CMN', 'CDG', 150), ('CMN', 'LHR', 180), ('CMN', 'BCN', 120),
            ('CMN', 'DXB', 420), ('CMN', 'MAD', 110), ('CMN', 'FCO', 200),
            ('AMS', 'JFK', 420), ('AMS', 'DXB', 360), ('AMS', 'SIN', 720),
            ('FRA', 'JFK', 480), ('FRA', 'DXB', 330), ('FRA', 'HND', 660),
            ('BCN', 'CMN', 120), ('BCN', 'CDG', 130), ('BCN', 'IST', 240),
            ('MAD', 'JFK', 450), ('MAD', 'CMN', 110), ('MAD', 'CDG', 140),
            ('FCO', 'JFK', 500), ('FCO', 'DXB', 300), ('FCO', 'CDG', 140),
            ('BKK', 'SIN', 150), ('BKK', 'HND', 360), ('BKK', 'LHR', 660),
        ]

        capacities = [30, 35, 40, 45, 50, 60, 75, 80]
        today = date.today()
        start_date = today - timedelta(days=15)
        end_date   = today + timedelta(days=60)

        flights_created = []
        current = start_date

        self.stdout.write('Generating flights...')
        while current <= end_date:
            if current < today:
                n = random.randint(8, 10)
            elif current == today:
                n = random.randint(10, 12)
            else:
                n = random.randint(12, 15)

            daily_routes = random.sample(routes, k=min(n, len(routes)))

            for origin_code, dest_code, duration in daily_routes:
                if current < today:
                    status = random.choices(['DEPARTED', 'CANCELLED'], weights=[85, 15])[0]
                elif current == today:
                    status = random.choices(['SCHEDULED', 'BOARDING', 'DEPARTED'], weights=[50, 35, 15])[0]
                else:
                    status = random.choices(['SCHEDULED', 'CANCELLED'], weights=[92, 8])[0]

                f = Flight.objects.create(
                    origin=airports[origin_code],
                    destination=airports[dest_code],
                    duration=duration,
                    status=status,
                    capacity=random.choice(capacities),
                    departure_date=current,
                )
                flights_created.append(f)

            current += timedelta(days=1)

        # Passagers sur 40 vols SCHEDULED avec taux d'occupation variés
        self.stdout.write('Adding passengers...')

        bookable = [f for f in flights_created
                    if f.status in ('SCHEDULED', 'BOARDING')
                    and f.departure_date >= today][:40]

        used_emails    = set()
        used_passports = set()
        total_pax      = 0

        for flight in bookable:
            # Taux d'occupation aléatoire : 20% à 90%
            occupancy_rate = random.uniform(0.20, 0.90)
            n_passengers   = int(flight.capacity * occupancy_rate)

            # Répartition par classe
            n_first    = max(1, int(n_passengers * 0.10))
            n_business = max(1, int(n_passengers * 0.25))
            n_economy  = n_passengers - n_first - n_business

            class_counts = [
                ('FIRST',    n_first),
                ('BUSINESS', n_business),
                ('ECONOMY',  n_economy),
            ]

            for seat_class, count in class_counts:
                for _ in range(count):
                    first = random.choice(FIRST_NAMES)
                    last  = random.choice(LAST_NAMES)

                    # Email unique
                    base_email = f"{first.lower()}.{last.lower()}"
                    email = f"{base_email}{random.randint(100,9999)}@airline.com"
                    while email in used_emails:
                        email = f"{base_email}{random.randint(100,9999)}@airline.com"
                    used_emails.add(email)

                    # Passport unique
                    letters = random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ') + \
                              random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')
                    digits  = str(random.randint(100000, 999999))
                    passport = letters + digits
                    while passport in used_passports:
                        letters  = random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ') + \
                                   random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')
                        passport = letters + str(random.randint(100000, 999999))
                    used_passports.add(passport)

                    seat_number = flight.next_seat(seat_class)
                    if seat_number is None:
                        break

                    p = Passenger.objects.create(
                        first=first, last=last,
                        email=email,
                        passport_number=passport,
                        seat_class=seat_class,
                        seat_number=seat_number,
                    )
                    p.flights.add(flight)
                    price = flight.get_price(seat_class)
                    Booking.objects.create(
                        passenger=p,
                        flight=flight,
                        seat_class=seat_class,
                        seat_number=seat_number,
                        price_paid=price,
                    )
                    total_pax += 1

        total_flights = len(flights_created)
        self.stdout.write(self.style.SUCCESS(
            f'Done! {total_flights} flights, {total_pax} passengers, '
            f'{Booking.objects.count()} bookings created.'
        ))

        # Vols dédiés aux tests avec statuts garantis
        self.stdout.write('Creating dedicated test flights...')

        jfk = airports['JFK']
        lhr = airports['LHR']
        cdg = airports['CDG']
        ist = airports['IST']

        # Vol SCHEDULED avec passagers — pour test_add_passenger, test_status
        test_flight_scheduled = Flight.objects.create(
            origin=jfk, destination=lhr,
            duration=415, status='SCHEDULED',
            capacity=50, departure_date=today + timedelta(days=1),
        )

        # Passagers fixes avec données connues pour les tests
        test_passengers = [
            ('Harry',    'Potter',   'harry@hogwarts.com',    'HP123456', 'ECONOMY'),
            ('Hermione', 'Granger',  'hermione@hogwarts.com', 'HG123456', 'BUSINESS'),
            ('Ron',      'Weasley',  'ron@hogwarts.com',      'RW123456', 'ECONOMY'),
            ('Albus',    'Dumbledore','albus@hogwarts.com',   'AD123456', 'FIRST'),
            ('Severus',  'Snape',    'severus@hogwarts.com',  'SS123456', 'BUSINESS'),
        ]

        test_passenger_obj = None
        for first, last, email, passport, seat_class in test_passengers:
            # Vérifier que l'email n'est pas déjà utilisé
            if email in used_emails or passport in used_passports:
                continue
            used_emails.add(email)
            used_passports.add(passport)

            seat_number = test_flight_scheduled.next_seat(seat_class)
            p = Passenger.objects.create(
                first=first, last=last, email=email,
                passport_number=passport, seat_class=seat_class,
                seat_number=seat_number,
            )
            p.flights.add(test_flight_scheduled)
            price = test_flight_scheduled.get_price(seat_class)
            Booking.objects.create(
                passenger=p, flight=test_flight_scheduled,
                seat_class=seat_class, seat_number=seat_number,
                price_paid=price,
            )
            if test_passenger_obj is None:
                test_passenger_obj = p

        # Vol BOARDING
        test_flight_boarding = Flight.objects.create(
            origin=cdg, destination=lhr,
            duration=90, status='BOARDING',
            capacity=40, departure_date=today,
        )

        # Vol DEPARTED
        test_flight_departed = Flight.objects.create(
            origin=lhr, destination=cdg,
            duration=90, status='DEPARTED',
            capacity=40, departure_date=today - timedelta(days=1),
        )

        # Vol CANCELLED
        test_flight_cancelled = Flight.objects.create(
            origin=ist, destination=cdg,
            duration=210, status='CANCELLED',
            capacity=50, departure_date=today + timedelta(days=2),
        )

        # Écrire les IDs dans un fichier pour Robot Framework
        import os
        rf_vars_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '..', '..', '..', 'airline-automation',
            'resources', 'test_flight_ids.resource'
        )
        rf_vars_path = os.path.normpath(rf_vars_path)

        with open(rf_vars_path, 'w') as f:
            f.write("*** Variables ***\n")
            f.write(f"${{TEST_FLIGHT_SCHEDULED_ID}}      {test_flight_scheduled.id}\n")
            f.write(f"${{TEST_FLIGHT_BOARDING_ID}}       {test_flight_boarding.id}\n")
            f.write(f"${{TEST_FLIGHT_DEPARTED_ID}}       {test_flight_departed.id}\n")
            f.write(f"${{TEST_FLIGHT_CANCELLED_ID}}      {test_flight_cancelled.id}\n")
            f.write(f"${{TEST_FLIGHT_SCHEDULED_URL}}     ${{BASE_URL}}/flights/{test_flight_scheduled.id}\n")
            f.write(f"${{TEST_FLIGHT_BOARDING_URL}}      ${{BASE_URL}}/flights/{test_flight_boarding.id}\n")
            f.write(f"${{TEST_FLIGHT_DEPARTED_URL}}      ${{BASE_URL}}/flights/{test_flight_departed.id}\n")
            f.write(f"${{TEST_FLIGHT_CANCELLED_URL}}     ${{BASE_URL}}/flights/{test_flight_cancelled.id}\n")
            f.write(f"${{TEST_PASSENGER_ID}}             {test_passenger_obj.id if test_passenger_obj else ''}\n")
            f.write(f"${{TEST_PASSENGER_EMAIL}}          harry@hogwarts.com\n")
            f.write(f"${{TEST_PASSENGER_FIRST}}          Harry\n")
            f.write(f"${{TEST_PASSENGER_LAST}}           Potter\n")

        self.stdout.write(self.style.SUCCESS(
            f'Test flights: SCHEDULED={test_flight_scheduled.id}, '
            f'BOARDING={test_flight_boarding.id}, '
            f'DEPARTED={test_flight_departed.id}, '
            f'CANCELLED={test_flight_cancelled.id}'
        ))
        self.stdout.write(self.style.SUCCESS(f'RF variables written to: {rf_vars_path}'))