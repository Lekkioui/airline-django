from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User


def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))
    return HttpResponseRedirect(reverse('index_flights'))


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return HttpResponseRedirect(reverse('index_flights'))
        else:
            return render(request, 'users/login.html', {
                "message": "Invalid credentials"
            })
    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))


def register_view(request):
    if request.method == 'POST':
        username   = request.POST.get('username', '').strip()
        email      = request.POST.get('email', '').strip()
        password   = request.POST.get('password', '').strip()
        password2  = request.POST.get('password2', '').strip()
        error      = None

        if not all([username, email, password, password2]):
            error = "All fields are required."
        elif password != password2:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif User.objects.filter(username=username).exists():
            error = f"Username '{username}' is already taken."
        elif User.objects.filter(email=email).exists():
            error = "An account with this email already exists."

        if error:
            return render(request, 'users/register.html', {
                'error': error,
                'form_data': {
                    'username': username,
                    'email': email,
                }
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=False,
        )
        login(request, user)
        return HttpResponseRedirect(reverse('index_flights'))

    return render(request, 'users/register.html')