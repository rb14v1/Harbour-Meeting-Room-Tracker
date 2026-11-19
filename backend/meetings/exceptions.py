from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler as drf_exception_handler


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict"
    default_code = "conflict"


class UnprocessableEntity(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Unprocessable entity"
    default_code = "unprocessable"


def exception_handler(exc, context):
    """Keep the API's error format: {"detail": "message"} or {"detail": [{"field", "message"}]}."""
    if isinstance(exc, ValidationError):
        items = []
        for field, messages in _flatten(exc.detail):
            for message in messages:
                items.append({"field": field, "message": str(message)})
        from rest_framework.response import Response
        return Response({"detail": items}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return drf_exception_handler(exc, context)


def _flatten(detail, prefix=""):
    """Yield (field, [messages]) pairs from DRF's nested error structure."""
    if isinstance(detail, dict):
        for key, value in detail.items():
            yield from _flatten(value, f"{prefix}.{key}" if prefix else key)
    elif isinstance(detail, list):
        if all(isinstance(item, str) or hasattr(item, "code") for item in detail):
            yield prefix or "body", [str(item) for item in detail]
        else:
            for item in detail:
                yield from _flatten(item, prefix)
    else:
        yield prefix or "body", [str(detail)]
