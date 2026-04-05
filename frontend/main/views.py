# main/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import logout


def login_view(request):
    return render(request, "main/login.html")


def dashboard(request):
    return render(request, "main/dashboard.html")


def notifications(request):
    return render(request, "main/notifications.html")


def add_device(request):
    return render(request, "main/add_device.html")


def greenhouse_detail(request):
    return render(request, "main/greenhouse_detail.html")


def profile(request):
    return render(request, "main/profile.html")


def logout_view(request):
    logout(request)
    return redirect("login")
