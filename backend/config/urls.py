from django.urls import include, path

urlpatterns = [
    path("api/", include("meetings.urls")),
    # Prometheus metrics at /metrics (text/plain; version=0.0.4).
    path("", include("django_prometheus.urls")),
]
