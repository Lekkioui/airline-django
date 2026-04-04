import re
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from .models import Flight, Airport, Passenger

VALID_TRANSITIONS = {
    'SCHEDULED': ['BOARDING', 'CANCELLED'],
    'BOARDING':  ['DEPARTED', 'CANCELLED'],
    'DEPARTED':  [],
    'CANCELLED': [],
}


def index(request):
    return render(request, "flights/index.html", {
        'flights': Flight.objects.all()
    })


def search(request):
    airports = Airport.objects.all()
    flights = None
    query = {
        'origin': request.GET.get('origin', '').strip(),
        'destination': request.GET.get('destination', '').strip(),
        'status': request.GET.get('status', '').strip(),
    }

    if 'origin' in request.GET or 'destination' in request.GET or 'status' in request.GET:
        flights = Flight.objects.all()
        if query['origin']:
            flights = flights.filter(origin__id=query['origin'])
        if query['destination']:
            flights = flights.filter(destination__id=query['destination'])
        if query['status']:
            flights = flights.filter(status=query['status'])

    return render(request, 'flights/search.html', {
        'airports': airports,
        'flights': flights,
        'query': query,
        'status_choices': Flight.STATUS_CHOICES,
    })


def flight(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    passengers = flight.passengers.all()
    next_statuses = VALID_TRANSITIONS.get(flight.status, [])
    return render(request, 'flights/flight.html', {
        'flight': flight,
        'passengers': passengers,
        'next_statuses': next_statuses,
    })


def update_status(request, flight_id):
    if request.method != "POST":
        return HttpResponseRedirect(reverse('flight', args=(flight_id,)))

    flight = get_object_or_404(Flight, pk=flight_id)
    new_status = request.POST.get('status', '').strip()
    error = None

    allowed = VALID_TRANSITIONS.get(flight.status, [])

    if not new_status:
        error = "No status provided."
    elif new_status not in allowed:
        error = f"Cannot transition from {flight.status} to {new_status}."
    else:
        flight.status = new_status
        flight.save()
        return HttpResponseRedirect(reverse('flight', args=(flight.id,)))

    passengers = flight.passengers.all()
    next_statuses = VALID_TRANSITIONS.get(flight.status, [])
    return render(request, 'flights/flight.html', {
        'flight': flight,
        'passengers': passengers,
        'next_statuses': next_statuses,
        'status_error': error,
    })


def passenger(request, passenger_id):
    passenger = get_object_or_404(Passenger, id=passenger_id)
    flights = passenger.flights.all()
    return render(request, 'flights/passenger.html', {
        'passenger': passenger,
        'flights': flights,
    })


def remove_flight_from_passenger(request, passenger_id, flight_id):
    if request.method == "POST":
        passenger = get_object_or_404(Passenger, pk=passenger_id)
        flight = get_object_or_404(Flight, pk=flight_id)
        passenger.flights.remove(flight)
        return HttpResponseRedirect(reverse('passenger', args=(passenger.id,)))


def book(request, flight_id):
    if request.method != "POST":
        return HttpResponseRedirect(reverse('flight', args=(flight_id,)))

    flight = get_object_or_404(Flight, pk=flight_id)
    error = None

    if not flight.is_bookable():
        error = "This flight is full." if flight.is_full() else f"Booking unavailable — status is {flight.status}."

    first      = request.POST.get('first', '').strip()
    last       = request.POST.get('last', '').strip()
    email      = request.POST.get('email', '').strip().lower()
    passport   = request.POST.get('passport_number', '').strip().upper()
    seat_class = request.POST.get('seat_class', 'ECONOMY')

    if not error:
        if not all([first, last, email, passport]):
            error = "All fields are required."
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            error = "Invalid email format."
        elif not re.match(r'^[A-Z]{2}\d{6}$', passport):
            error = "Passport must be 2 uppercase letters followed by 6 digits (e.g. AB123456)."
        elif seat_class not in ('ECONOMY', 'BUSINESS', 'FIRST'):
            error = "Invalid seat class."

    if not error:
        if Passenger.objects.filter(email=email).exists():
            existing = Passenger.objects.get(email=email)
            if flight.passengers.filter(pk=existing.pk).exists():
                error = "This passenger is already booked on this flight."
            else:
                existing.flights.add(flight)
                return HttpResponseRedirect(reverse('flight', args=(flight.id,)))
        elif Passenger.objects.filter(passport_number=passport).exists():
            error = f"Passport number {passport} is already registered to another passenger."

    if not error:
        seat_number = flight.next_seat(seat_class)
        passenger = Passenger.objects.create(
            first=first, last=last,
            email=email,
            passport_number=passport,
            seat_class=seat_class,
            seat_number=seat_number,
        )
        passenger.flights.add(flight)
        return HttpResponseRedirect(reverse('flight', args=(flight.id,)))

    next_statuses = VALID_TRANSITIONS.get(flight.status, [])
    return render(request, 'flights/flight.html', {
        'flight': flight,
        'passengers': flight.passengers.all(),
        'next_statuses': next_statuses,
        'error': error,
        'open_modal': True,
        'form_data': {
            'first': first, 'last': last,
            'email': email, 'passport_number': passport,
            'seat_class': seat_class,
        }
    })


def remove(request, flight_id, passenger_id):
    if request.method == "POST":
        flight = get_object_or_404(Flight, pk=flight_id)
        passenger = get_object_or_404(Passenger, pk=passenger_id)
        passenger.flights.remove(flight)
        return HttpResponseRedirect(reverse('flight', args=(flight.id,)))