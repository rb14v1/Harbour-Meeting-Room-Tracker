from datetime import date, datetime, time

from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework.exceptions import NotFound

from meetings.exceptions import Conflict, UnprocessableEntity
from meetings.models import Booking, Employee, Room


def now_local() -> datetime:
    return datetime.now()


def has_ended(day: date, end: time, now: datetime) -> bool:
    if day != now.date():
        return day < now.date()
    return end <= now.time()


def booking_flags(booking: Booking, now: datetime) -> dict:
    ended = has_ended(booking.booking_date, booking.end_time, now)
    can_edit = booking.status == Booking.Status.CONFIRMED and not ended
    return {"is_past": ended, "can_edit": can_edit, "can_cancel": can_edit}


def _ensure_bookable_slot(day: date, start: time, now: datetime) -> None:
    if day < now.date():
        raise UnprocessableEntity("Booking date cannot be in the past")
    if day == now.date() and start <= now.time():
        raise UnprocessableEntity("Start time has already passed for today")


def _overlapping(room: Room, day: date, start: time, end: time, exclude_pk=None):
    # Overlap rule: existing.start < new.end AND existing.end > new.start.
    # Back-to-back meetings (10-11 then 11-12) do not overlap.
    qs = Booking.objects.filter(
        room=room, booking_date=day, status=Booking.Status.CONFIRMED,
        start_time__lt=end, end_time__gt=start,
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.order_by("start_time").first()


def _save_booking(data: dict, booking: Booking | None) -> Booking:
    day, start, end = data["booking_date"], data["start_time"], data["end_time"]
    with transaction.atomic():
        # Locking the room row serialises concurrent bookings for the same room.
        room = Room.objects.select_for_update().filter(pk=data["room_id"]).first()
        if room is None:
            raise NotFound("Room not found")
        if room.status != Room.Status.ACTIVE:
            raise Conflict(f"{room.room_name} is inactive and cannot be booked")

        employee, _ = Employee.objects.update_or_create(
            email=data["employee_email"].lower(),
            defaults={"employee_name": data["employee_name"], "department": data["department"]},
        )

        clash = _overlapping(room, day, start, end, exclude_pk=booking.pk if booking else None)
        if clash:
            raise Conflict(
                f"Room already booked {clash.start_time:%H:%M}-{clash.end_time:%H:%M} ({clash.meeting_title})"
            )

        if booking is None:
            booking = Booking()
        booking.room = room
        booking.employee = employee
        booking.meeting_title = data["meeting_title"]
        booking.booking_date = day
        booking.start_time = start
        booking.end_time = end
        try:
            # Savepoint: the exclusion constraint is the final guard against races.
            with transaction.atomic():
                booking.save()
        except IntegrityError:
            raise Conflict("Room already booked for part of this time")
    return booking


def create_booking(data: dict) -> Booking:
    _ensure_bookable_slot(data["booking_date"], data["start_time"], now_local())
    return _save_booking(data, None)


def update_booking(booking: Booking, data: dict) -> Booking:
    if booking.status != Booking.Status.CONFIRMED:
        raise Conflict("Cancelled bookings cannot be edited")
    if has_ended(booking.booking_date, booking.end_time, now_local()):
        raise Conflict("Past bookings cannot be edited")
    _ensure_bookable_slot(data["booking_date"], data["start_time"], now_local())
    return _save_booking(data, booking)


def cancel_booking(booking: Booking) -> Booking:
    if booking.status == Booking.Status.CANCELLED:
        raise Conflict("Booking is already cancelled")
    if has_ended(booking.booking_date, booking.end_time, now_local()):
        raise Conflict("Past bookings cannot be cancelled")
    booking.status = Booking.Status.CANCELLED
    booking.save(update_fields=["status"])
    return booking


def list_bookings(view: str = "all", search: str | None = None, room_id: int | None = None,
                  day: date | None = None):
    now = now_local()
    today, now_t = now.date(), now.time()
    qs = Booking.objects.select_related("room", "employee")
    confirmed = Q(status=Booking.Status.CONFIRMED)

    if view == "upcoming":
        qs = qs.filter(confirmed & (Q(booking_date__gt=today) | Q(booking_date=today, end_time__gt=now_t)))
    elif view == "past":
        qs = qs.filter(confirmed & (Q(booking_date__lt=today) | Q(booking_date=today, end_time__lte=now_t)))
    elif view == "cancelled":
        qs = qs.filter(status=Booking.Status.CANCELLED)

    if search and search.strip():
        qs = qs.filter(employee__employee_name__icontains=search.strip())
    if room_id:
        qs = qs.filter(room_id=room_id)
    if day:
        qs = qs.filter(booking_date=day)
    return qs[:500]


def room_availability(day: date, start: time, end: time, capacity: int | None = None,
                      search: str | None = None, facilities: list[str] | None = None) -> list[dict]:
    wanted = [f.strip().lower() for f in (facilities or []) if f.strip()]
    term = (search or "").strip().lower()

    clashes_by_room: dict[int, list[dict]] = {}
    clashes = Booking.objects.filter(
        booking_date=day, status=Booking.Status.CONFIRMED, start_time__lt=end, end_time__gt=start,
    ).order_by("start_time")
    for c in clashes:
        clashes_by_room.setdefault(c.room_id, []).append({
            "meeting_title": c.meeting_title,
            "start_time": c.start_time.strftime("%H:%M"),
            "end_time": c.end_time.strftime("%H:%M"),
        })

    results = []
    for room in Room.objects.all():
        if term and term not in room.room_name.lower():
            continue
        if capacity and room.capacity < capacity:
            continue
        room_facilities = split_facilities(room.facilities)
        have = {f.lower() for f in room_facilities}
        if wanted and not all(w in have for w in wanted):
            continue
        conflicts = clashes_by_room.get(room.pk, [])
        if room.status != Room.Status.ACTIVE:
            state = "Inactive"
        elif conflicts:
            state = "Occupied"
        else:
            state = "Available"
        results.append({
            "room_id": room.pk,
            "room_name": room.room_name,
            "location": room.location,
            "capacity": room.capacity,
            "facilities": room_facilities,
            "status": room.status,
            "available": state == "Available",
            "state": state,
            "conflicts": conflicts,
        })
    return results


def split_facilities(raw: str) -> list[str]:
    return [f.strip() for f in (raw or "").split(",") if f.strip()]
