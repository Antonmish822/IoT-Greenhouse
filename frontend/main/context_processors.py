from django.conf import settings


def backend_url(request):
    return {
        "BACKEND_URL": getattr(settings, "BACKEND_URL", "http://127.0.0.1:8001"),
    }
