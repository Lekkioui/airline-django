from decimal import Decimal, InvalidOperation
import re
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from .models import Flight, Airport, Passenger, Booking
from django.core.paginator import Paginator
from datetime import date
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required, user_passes_test


VALID_TRANSITIONS = {
    'SCHEDULED': ['BOARDING', 'CANCELLED'],
    'BOARDING':  ['DEPARTED', 'CANCELLED'],
    'DEPARTED':  [],
    'CANCELLED': [],
}


def admin_required(view_func):
    return user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url='/users/login'
    )(view_func)

@login_required(login_url='/users/login')
def index(request):
    airports = Airport.objects.all().order_by('city')
    flights = Flight.objects.select_related('origin', 'destination').all()

    origin      = request.GET.get('origin', '').strip()
    destination = request.GET.get('destination', '').strip()
    status      = request.GET.get('status', '').strip()
    date_filter = request.GET.get('date', '').strip()
    period      = request.GET.get('period', '').strip()
    sort        = request.GET.get('sort', 'departure_date')
    order       = request.GET.get('order', 'asc')

    if origin:
        flights = flights.filter(origin__id=origin)
    if destination:
        flights = flights.filter(destination__id=destination)
    if status:
        flights = flights.filter(status=status)

    today = date.today()

    if date_filter:
        flights = flights.filter(departure_date=date_filter)
    elif period == 'today':
        flights = flights.filter(departure_date=today)
    elif period == 'week':
        flights = flights.filter(departure_date__gte=today, departure_date__lte=today + timedelta(days=7))
    elif period == 'month':
        flights = flights.filter(departure_date__gte=today, departure_date__lte=today + timedelta(days=30))
    else:
        flights = flights.filter(departure_date__gte=today)

    sort_field = sort if order == 'asc' else f'-{sort}'
    try:
        flights = flights.order_by(sort_field)
    except Exception:
        flights = flights.order_by('departure_date')

    from django.db.models import Count, Q
    stats = {
        'total':     Flight.objects.count(),
        'scheduled': Flight.objects.filter(status='SCHEDULED').count(),
        'boarding':  Flight.objects.filter(status='BOARDING').count(),
        'departed':  Flight.objects.filter(status='DEPARTED').count(),
        'cancelled': Flight.objects.filter(status='CANCELLED').count(),
    }

    paginator = Paginator(flights, 20)
    page_num  = request.GET.get('page', 1)
    page_obj  = paginator.get_page(page_num)

    return render(request, "flights/index.html", {
        'page_obj':       page_obj,
        'airports':       airports,
        'stats':          stats,
        'status_choices': Flight.STATUS_CHOICES,
        'today':          today,
        'query': {
            'origin': origin, 'destination': destination,
            'status': status, 'date': date_filter,
            'sort': sort, 'order': order,
            'period': period,
        },
    })

@login_required(login_url='/users/login')
def search(request):
    airports = Airport.objects.all()
    flights = None
    query = {
        'origin': request.GET.get('origin', '').strip(),
        'destination': request.GET.get('destination', '').strip(),
        'status': request.GET.get('status', '').strip(),
        'date': request.GET.get('date', '').strip(),
    }

    if request.GET:
        flights = Flight.objects.all()
        if query['origin']:
            flights = flights.filter(origin__id=query['origin'])
        if query['destination']:
            flights = flights.filter(destination__id=query['destination'])
        if query['status']:
            flights = flights.filter(status=query['status'])
        if query['date']:
            flights = flights.filter(departure_date=query['date'])

    return render(request, 'flights/search.html', {
        'airports': airports,
        'flights': flights,
        'query': query,
        'status_choices': Flight.STATUS_CHOICES,
    })

@login_required(login_url='/users/login')
def flight(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    passengers = flight.passengers.all()
    next_statuses = VALID_TRANSITIONS.get(flight.status, [])
    return render(request, 'flights/flight.html', {
        'flight': flight,
        'passengers': passengers,
        'next_statuses': next_statuses,
    })

@login_required(login_url='/users/login')
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

@login_required(login_url='/users/login')
def passenger(request, passenger_id):
    passenger = get_object_or_404(Passenger, id=passenger_id)
    flights = passenger.flights.all()
    return render(request, 'flights/passenger.html', {
        'passenger': passenger,
        'flights': flights,
    })

@login_required(login_url='/users/login')
def remove_flight_from_passenger(request, passenger_id, flight_id):
    if request.method == "POST":
        passenger = get_object_or_404(Passenger, pk=passenger_id)
        flight = get_object_or_404(Flight, pk=flight_id)
        passenger.flights.remove(flight)
        return HttpResponseRedirect(reverse('passenger', args=(passenger.id,)))

@login_required(login_url='/users/login')
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

@login_required(login_url='/users/login')
def remove(request, flight_id, passenger_id):
    if request.method == "POST":
        flight = get_object_or_404(Flight, pk=flight_id)
        passenger = get_object_or_404(Passenger, pk=passenger_id)
        passenger.flights.remove(flight)
        return HttpResponseRedirect(reverse('flight', args=(flight.id,)))

@login_required(login_url='/users/login')
def seat_map(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    if not flight.is_bookable():
        return HttpResponseRedirect(reverse('flight', args=(flight_id,)))

    seat_map_data = flight.get_seat_map()

    prices = {
        'FIRST':    flight.get_price('FIRST'),
        'BUSINESS': flight.get_price('BUSINESS'),
        'ECONOMY':  flight.get_price('ECONOMY'),
    }

    occ_rate = round(flight.occupancy_rate() * 100, 0)

    return render(request, 'flights/seat_map.html', {
        'flight':     flight,
        'seat_map':   seat_map_data,
        'prices':     prices,
        'occ_rate':   occ_rate,
        'class_list': [
            ('FIRST',    'First Class', '👑'),
            ('BUSINESS', 'Business',    '💼'),
            ('ECONOMY',  'Economy',     '✈️'),
        ],
    })

@login_required(login_url='/users/login')
def booking_confirm(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)

    if request.method == 'GET':
        seat_class    = request.GET.get('seat_class', 'ECONOMY')
        selected_seat = request.GET.get('seat', '')
        if flight.seats_available(seat_class) <= 0:
            return HttpResponseRedirect(reverse('seat_map', args=(flight_id,)))
        price = flight.get_price(seat_class)
        return render(request, 'flights/booking_confirm.html', {
            'flight':            flight,
            'seat_class':        seat_class,
            'selected_seat':     selected_seat,
            'seat_class_display': dict(Passenger.SEAT_CLASS_CHOICES)[seat_class],
            'price':             price,
        })

    if request.method == 'POST':
        seat_class    = request.POST.get('seat_class', 'ECONOMY')
        selected_seat = request.POST.get('selected_seat', '').strip()
        first         = request.POST.get('first', '').strip()
        last          = request.POST.get('last', '').strip()
        email         = request.POST.get('email', '').strip().lower()
        passport      = request.POST.get('passport_number', '').strip().upper()
        error         = None

        if not all([first, last, email, passport]):
            error = "All fields are required."
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            error = "Invalid email format."
        elif not re.match(r'^[A-Z]{2}\d{6}$', passport):
            error = "Passport must be 2 uppercase letters followed by 6 digits."
        elif flight.seats_available(seat_class) <= 0:
            error = "No seats available in this class."

        if error:
            return render(request, 'flights/booking_confirm.html', {
                'flight': flight,
                'seat_class': seat_class,
                'selected_seat': selected_seat,
                'seat_class_display': dict(Passenger.SEAT_CLASS_CHOICES)[seat_class],
                'error': error,
                'form_data': {
                    'first': first, 'last': last,
                    'email': email, 'passport_number': passport,
                },
            })

        if Passenger.objects.filter(email=email).exists():
            passenger_obj = Passenger.objects.get(email=email)
            if flight.passengers.filter(pk=passenger_obj.pk).exists():
                error = "This passenger is already booked on this flight."
                return render(request, 'flights/booking_confirm.html', {
                    'flight': flight,
                    'seat_class': seat_class,
                    'selected_seat': selected_seat,
                    'seat_class_display': dict(Passenger.SEAT_CLASS_CHOICES)[seat_class],
                    'error': error,
                })
        elif Passenger.objects.filter(passport_number=passport).exists():
            error = f"Passport {passport} is already registered to another passenger."
            return render(request, 'flights/booking_confirm.html', {
                'flight': flight,
                'seat_class': seat_class,
                'selected_seat': selected_seat,
                'seat_class_display': dict(Passenger.SEAT_CLASS_CHOICES)[seat_class],
                'error': error,
            })
        else:
            if selected_seat and selected_seat not in flight.taken_seats(seat_class):
                seat_number = selected_seat
            else:
                seat_number = flight.next_seat(seat_class)

            passenger_obj = Passenger.objects.create(
                first=first, last=last,
                email=email,
                passport_number=passport,
                seat_class=seat_class,
                seat_number=seat_number,
            )

        passenger_obj.flights.add(flight)
        try:
            price = Decimal(request.POST.get('price', '0'))
        except InvalidOperation:
            price = flight.get_price(seat_class)
        booking = Booking.objects.create(
            passenger=passenger_obj,
            flight=flight,
            seat_class=seat_class,
            seat_number=passenger_obj.seat_number,
            price_paid=price,
        )
        return HttpResponseRedirect(reverse('booking_success', args=(booking.reference,)))

@login_required(login_url='/users/login')
def booking_success(request, reference):
    booking = get_object_or_404(Booking, reference=reference)
    return render(request, 'flights/booking_success.html', {
        'booking': booking,
    })

@login_required(login_url='/users/login')
def booking_cancel(request, reference):
    booking = get_object_or_404(Booking, reference=reference)
    if request.method == 'POST':
        booking.status = 'CANCELLED'
        booking.save()
        booking.passenger.flights.remove(booking.flight)
        return HttpResponseRedirect(reverse('flight', args=(booking.flight.id,)))
    return render(request, 'flights/booking_cancel.html', {
        'booking': booking,
    })

@admin_required
def dashboard(request):
    from django.db.models import Count, Avg, Sum, F
    from datetime import date, timedelta

    today = date.today()

    # KPIs globaux
    total_flights     = Flight.objects.count()
    total_passengers  = Passenger.objects.count()
    total_bookings    = Booking.objects.count()
    cancelled_count   = Flight.objects.filter(status='CANCELLED').count()
    scheduled_count   = Flight.objects.filter(status='SCHEDULED').count()
    boarding_count    = Flight.objects.filter(status='BOARDING').count()
    departed_count    = Flight.objects.filter(status='DEPARTED').count()

    # Vols aujourd'hui
    today_flights     = Flight.objects.filter(departure_date=today)
    today_total       = today_flights.count()
    today_scheduled   = today_flights.filter(status='SCHEDULED').count()
    today_boarding    = today_flights.filter(status='BOARDING').count()
    today_departed    = today_flights.filter(status='DEPARTED').count()
    today_cancelled   = today_flights.filter(status='CANCELLED').count()

    # Taux d'occupation moyen sur vols avec passagers
    flights_with_pax = Flight.objects.annotate(
        pax_count=Count('passengers')
    ).filter(pax_count__gt=0)

    occ_rates = []
    for f in flights_with_pax:
        occ_rates.append(f.pax_count / f.capacity * 100)
    avg_occupancy = round(sum(occ_rates) / len(occ_rates), 1) if occ_rates else 0

    # Occupation par jour sur 14 prochains jours
    daily_data = []
    for i in range(14):
        d = today + timedelta(days=i)
        day_flights = Flight.objects.filter(departure_date=d).annotate(
            pax_count=Count('passengers')
        )
        day_total_cap = sum(f.capacity for f in day_flights)
        day_total_pax = sum(f.pax_count for f in day_flights)
        day_flight_count = day_flights.count()
        occ = round(day_total_pax / day_total_cap * 100, 1) if day_total_cap > 0 else 0
        daily_data.append({
            'date':       d.strftime('%d %b'),
            'flights':    day_flight_count,
            'passengers': day_total_pax,
            'occupancy':  occ,
            'flights_pct': min(round(day_flight_count / 15 * 100), 100),
        })

    # Top 10 routes par nombre de passagers
    top_routes = Flight.objects.annotate(
        pax_count=Count('passengers')
    ).filter(pax_count__gt=0).order_by('-pax_count').select_related(
        'origin', 'destination'
    )[:10]

    # Vols presque pleins (>80%) parmi les SCHEDULED
    almost_full = []
    scheduled_flights = Flight.objects.filter(
        status='SCHEDULED',
        departure_date__gte=today
    ).annotate(pax_count=Count('passengers')).select_related(
        'origin', 'destination'
    )
    for f in scheduled_flights:
        if f.capacity > 0:
            rate = f.pax_count / f.capacity * 100
            if rate >= 70:
                almost_full.append({
                    'flight': f,
                    'rate': round(rate, 0),
                    'pax': f.pax_count,
                })
    almost_full = sorted(almost_full, key=lambda x: x['rate'], reverse=True)[:8]

    # Répartition par classe
    economy_pax  = Passenger.objects.filter(seat_class='ECONOMY').count()
    business_pax = Passenger.objects.filter(seat_class='BUSINESS').count()
    first_pax    = Passenger.objects.filter(seat_class='FIRST').count()

    # Top aéroports par trafic
    top_origins = Airport.objects.annotate(
        dep_count=Count('departures')
    ).order_by('-dep_count')[:6]

    total_revenue = Booking.objects.filter(
    status='CONFIRMED',
    price_paid__isnull=False
    ).aggregate(total=Sum('price_paid'))['total'] or 0
    total_revenue = round(total_revenue, 2)

    return render(request, 'flights/dashboard.html', {
        'today': today,
        # KPIs
        'total_flights':    total_flights,
        'total_passengers': total_passengers,
        'total_bookings':   total_bookings,
        'cancelled_count':  cancelled_count,
        'scheduled_count':  scheduled_count,
        'boarding_count':   boarding_count,
        'departed_count':   departed_count,
        'avg_occupancy':    avg_occupancy,
        'total_revenue': total_revenue,
        # Today
        'today_total':     today_total,
        'today_scheduled': today_scheduled,
        'today_boarding':  today_boarding,
        'today_departed':  today_departed,
        'today_cancelled': today_cancelled,
        # Charts
        'daily_data':   daily_data,
        'top_routes':   top_routes,
        'almost_full':  almost_full,
        # Classes
        'economy_pax':  economy_pax,
        'business_pax': business_pax,
        'first_pax':    first_pax,
        # Airports
        'top_origins':  top_origins,
    })

@login_required(login_url='/users/login')
def boarding_pass_pdf(request, reference):
    booking = get_object_or_404(Booking, reference=reference)
    return render(request, 'flights/boarding_pass.html', {
        'booking': booking,
    })