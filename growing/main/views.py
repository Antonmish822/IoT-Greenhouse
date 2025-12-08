# main/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse


def login_view(request):
    return render(request, 'main/login.html')


def dashboard(request):
    return render(request, 'main/dashboard.html')


def notifications(request):
    return render(request, 'main/notifications.html')


def add_device(request):
    return render(request, 'main/add_device.html')

def greenhouse_detail(request):
    return render(request, 'main/greenhouse_detail.html')

def add_greenhouse(request):
    return render(request, 'main/add_greenhouse.html')

def logout_view(request):
    logout(request)
    return redirect('login')