from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("notifications/", views.notifications, name="notifications"),
    path("add_device/", views.add_device, name="add_device"),
    path("logout/", views.logout_view, name="logout"),
    path("greenhouse_detail/", views.greenhouse_detail, name="greenhouse_detail"),
    path("profile/", views.profile, name="profile"),
]
