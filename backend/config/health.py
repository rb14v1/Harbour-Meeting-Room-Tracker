from django.db import connection
from django.http import HttpResponse, JsonResponse


class HealthCheckMiddleware:
    """Answer platform probes before host validation, sessions or auth run.

    /healthz  liveness: process is up. No database access.
    /readyz   readiness: database reachable.
    Container Apps probes use the pod IP as Host, which ALLOWED_HOSTS would reject.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/healthz":
            return HttpResponse("ok", content_type="text/plain")
        if request.path == "/readyz":
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
            except Exception:
                return JsonResponse({"status": "unavailable"}, status=503)
            return JsonResponse({"status": "ok"})
        return self.get_response(request)
