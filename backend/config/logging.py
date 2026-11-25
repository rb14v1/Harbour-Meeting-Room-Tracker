"""Structured JSON logging with a per-request correlation ID."""
import contextvars
import logging
import uuid
from datetime import datetime, timezone

from pythonjsonlogger.json import JsonFormatter as _BaseJsonFormatter

REQUEST_ID_HEADER = "HTTP_X_REQUEST_ID"
RESPONSE_HEADER = "X-Request-ID"

_request_id = contextvars.ContextVar("request_id", default="-")


def get_request_id() -> str:
    return _request_id.get()


class RequestIDFilter(logging.Filter):
    """Attach the current request ID to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = _request_id.get()
        return True


class JsonFormatter(_BaseJsonFormatter):
    """One JSON object per line with timestamp, level, message and request_id."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["request_id"] = getattr(record, "request_id", _request_id.get())
        # Drop non-serialisable Django objects attached to request logs.
        log_record.pop("request", None)
        log_record.pop("server_time", None)


class RequestIDMiddleware:
    """Read or generate an X-Request-ID and expose it to logs and the response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = (request.META.get(REQUEST_ID_HEADER) or "").strip()
        request_id = incoming[:128] if incoming else uuid.uuid4().hex
        request.request_id = request_id
        token = _request_id.set(request_id)
        try:
            response = self.get_response(request)
            response[RESPONSE_HEADER] = request_id
            return response
        finally:
            _request_id.reset(token)
