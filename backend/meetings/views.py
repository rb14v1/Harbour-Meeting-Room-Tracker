from datetime import date, datetime, time

from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from meetings import reports, services
from meetings.exceptions import UnprocessableEntity
from meetings.models import Booking, Room
from meetings.serializers import BookingReadSerializer, BookingWriteSerializer, RoomSerializer
from meetings.services import now_local


def _parse_day(value: str, field: str = "date") -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValidationError({field: "must be a valid date (YYYY-MM-DD)"})


def _parse_time(value: str, field: str) -> time:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except (TypeError, ValueError):
        raise ValidationError({field: "must be a valid time (HH:MM)"})


def _flag(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes")


def _get_booking(pk: int) -> Booking:
    booking = Booking.objects.select_related("room", "employee").filter(pk=pk).first()
    if booking is None:
        raise NotFound("Booking not found")
    return booking


class Health(APIView):
    def get(self, request):
        return Response({"status": "ok"})


class Dashboard(APIView):
    def get(self, request):
        now = now_local()
        day = _parse_day(request.query_params["date"]) if request.query_params.get("date") else now.date()
        return Response(reports.dashboard_summary(day, now))


class RoomList(APIView):
    def get(self, request):
        rooms = Room.objects.all()
        if not _flag(request.query_params.get("include_inactive"), True):
            rooms = rooms.filter(status=Room.Status.ACTIVE)
        return Response(RoomSerializer(rooms, many=True).data)

    def post(self, request):
        serializer = RoomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room = serializer.save()
        return Response(RoomSerializer(room).data, status=201)


class RoomDetail(APIView):
    def _get_room(self, pk: int) -> Room:
        room = Room.objects.filter(pk=pk).first()
        if room is None:
            raise NotFound("Room not found")
        return room

    def get(self, request, pk):
        return Response(RoomSerializer(self._get_room(pk)).data)

    def put(self, request, pk):
        room = self._get_room(pk)
        serializer = RoomSerializer(room, data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(RoomSerializer(serializer.save()).data)

    def delete(self, request, pk):
        room = self._get_room(pk)
        count = room.bookings.count()
        if count:
            room.status = Room.Status.INACTIVE
            room.save(update_fields=["status"])
            return Response({
                "deleted": False, "deactivated": True,
                "message": f"Room has {count} booking record(s), so it was deactivated instead of deleted.",
            })
        room.delete()
        return Response({"deleted": True, "deactivated": False, "message": "Room deleted."})


class Availability(APIView):
    def get(self, request):
        params = request.query_params
        missing = {k: "is required" for k in ("date", "start", "end") if not params.get(k)}
        if missing:
            raise ValidationError(missing)
        day = _parse_day(params["date"])
        start = _parse_time(params["start"], "start")
        end = _parse_time(params["end"], "end")
        if end <= start:
            raise UnprocessableEntity("end must be later than start")

        capacity = params.get("capacity")
        try:
            capacity = int(capacity) if capacity else None
        except ValueError:
            raise ValidationError({"capacity": "must be a whole number"})

        return Response(services.room_availability(
            day, start, end, capacity=capacity, search=params.get("search"),
            facilities=params.getlist("facilities"),
        ))


class BookingList(APIView):
    VIEWS = ("all", "upcoming", "past", "cancelled")

    def get(self, request):
        params = request.query_params
        view = params.get("view", "all")
        if view not in self.VIEWS:
            raise ValidationError({"view": f"must be one of {', '.join(self.VIEWS)}"})
        room_id = params.get("room_id")
        try:
            room_id = int(room_id) if room_id else None
        except ValueError:
            raise ValidationError({"room_id": "must be a whole number"})
        day = _parse_day(params["date"]) if params.get("date") else None

        bookings = services.list_bookings(view, params.get("search"), room_id, day)
        return Response(BookingReadSerializer(bookings, many=True).data)

    def post(self, request):
        serializer = BookingWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = services.create_booking(serializer.validated_data)
        return Response(BookingReadSerializer(_get_booking(booking.pk)).data, status=201)


class BookingDetail(APIView):
    def get(self, request, pk):
        return Response(BookingReadSerializer(_get_booking(pk)).data)

    def put(self, request, pk):
        booking = _get_booking(pk)
        serializer = BookingWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.update_booking(booking, serializer.validated_data)
        return Response(BookingReadSerializer(_get_booking(pk)).data)


class BookingCancel(APIView):
    def post(self, request, pk):
        booking = _get_booking(pk)
        services.cancel_booking(booking)
        return Response(BookingReadSerializer(_get_booking(pk)).data)


class ReportSummary(APIView):
    def get(self, request):
        return Response(reports.reports_summary(now_local().date()))
