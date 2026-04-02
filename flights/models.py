from django.db import models
from django.core.validators import RegexValidator


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

    def __str__(self):
        return f"{self.id} : {self.origin} to {self.destination}"

    def is_full(self):
        return self.passengers.count() >= self.capacity

    def is_bookable(self):
        return self.status == 'SCHEDULED' and not self.is_full()

    def next_seat(self, seat_class):
        prefix = {'FIRST': 'F', 'BUSINESS': 'B', 'ECONOMY': 'E'}[seat_class]
        existing = (
            self.passengers
            .filter(seat_class=seat_class)
            .values_list('seat_number', flat=True)
        )
        numbers = []
        for s in existing:
            try:
                numbers.append(int(s[1:]))
            except (ValueError, IndexError):
                pass
        next_num = max(numbers, default=0) + 1
        return f"{prefix}{next_num}"


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