from logging import config

from django.db import models
from django.core.validators import RegexValidator
import uuid
from decimal import Decimal


CABIN_CONFIG = {
    'FIRST':    {'rows': range(1, 4),   'cols': ['A', 'C']},
    'BUSINESS': {'rows': range(4, 9),   'cols': ['A', 'B', 'D', 'E']},
    'ECONOMY':  {'rows': range(9, 26),  'cols': ['A', 'B', 'C', 'D', 'E', 'F']},
}
class Airport(models.Model):
    code = models.CharField(max_length=3)
    city = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.city} ({self.code})"


class Flight(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('BOARDING', 'Boarding'),
        ('DEPARTED', 'Departed'),
        ('CANCELLED', 'Cancelled'),
    ]


    origin = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="departures")
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="arrivals")
    duration = models.IntegerField()
    capacity = models.IntegerField(default=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    departure_date = models.DateField(null=True, blank=True)
    base_price = models.DecimalField(max_digits=8, decimal_places=2, default=300.00)

    def __str__(self):
        return f"{self.id} : {self.origin} to {self.destination}"

    def is_full(self):
        return self.passengers.count() >= self.capacity

    def is_bookable(self):
        return self.status == 'SCHEDULED' and not self.is_full()

    def all_seats(self, seat_class):
        config = CABIN_CONFIG[seat_class]
        return [f"{row}{col}" for row in config['rows'] for col in config['cols']]

    def taken_seats(self, seat_class):
        return list(
            self.passengers
            .filter(seat_class=seat_class)
            .values_list('seat_number', flat=True)
        )

    def next_seat(self, seat_class):
        taken = self.taken_seats(seat_class)
        for seat in self.all_seats(seat_class):
            if seat not in taken:
                return seat
        return None

    def seats_available(self, seat_class):
        return len(self.all_seats(seat_class)) - len(self.taken_seats(seat_class))

    def seats_taken_count(self, seat_class):
        return len(self.taken_seats(seat_class))

    def get_seat_map(self):
        result = {}
        for cls in ['FIRST', 'BUSINESS', 'ECONOMY']:
            taken = self.taken_seats(cls)
            config = CABIN_CONFIG[cls]
            rows = []
            for row in config['rows']:
                seats = []
                for col in config['cols']:
                    seat_num = f"{row}{col}"
                    seats.append({
                        'number': seat_num,
                        'taken': seat_num in taken,
                    })
                rows.append({'row': row, 'seats': seats})
            result[cls] = {
                'rows': rows,
                'cols': config['cols'],
                'available': self.seats_available(cls),
                'taken': self.seats_taken_count(cls),
            }
        return result
    
    def occupancy_rate(self):
        total = self.passengers.count()
        if self.capacity == 0:
            return 0
        return total / self.capacity

    def get_price(self, seat_class):
        base_multipliers = {
            'ECONOMY':  Decimal('1.0'),
            'BUSINESS': Decimal('2.8'),
            'FIRST':    Decimal('5.2'),
        }
        occ = self.occupancy_rate()
        if occ < 0.30:
            demand_multiplier = Decimal('1.0')
        elif occ < 0.50:
            demand_multiplier = Decimal('1.2')
        elif occ < 0.70:
            demand_multiplier = Decimal('1.5')
        elif occ < 0.85:
            demand_multiplier = Decimal('1.8')
        else:
            demand_multiplier = Decimal('2.2')

        price = Decimal(str(self.base_price)) * base_multipliers[seat_class] * demand_multiplier
        return price.quantize(Decimal('0.01'))


class Passenger(models.Model):
    SEAT_CLASS_CHOICES = [
        ('ECONOMY', 'Economy'),
        ('BUSINESS', 'Business'),
        ('FIRST', 'First Class'),
    ]

    passport_validator = RegexValidator(
        regex=r'^[A-Z]{2}\d{6}$',
        message="Passport must be 2 uppercase letters followed by 6 digits (e.g. AB123456)."
    )

    first = models.CharField(max_length=64)
    last = models.CharField(max_length=64)
    email = models.EmailField(unique=True, default='')
    passport_number = models.CharField(
        max_length=8,
        unique=True,
        validators=[passport_validator],
        default=''
    )
    seat_class = models.CharField(max_length=20, choices=SEAT_CLASS_CHOICES, default='ECONOMY')
    seat_number = models.CharField(max_length=10, blank=True, default='')
    flights = models.ManyToManyField(Flight, blank=True, related_name="passengers")

    def __str__(self):
        return f"{self.first} {self.last}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    ]

    reference = models.CharField(max_length=12, unique=True, editable=False)
    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE, related_name='bookings')
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='bookings')
    seat_class = models.CharField(max_length=20)
    seat_number = models.CharField(max_length=10)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')
    price_paid = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = 'BK-' + uuid.uuid4().hex[:6].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.passenger} on FL{self.flight.id}"