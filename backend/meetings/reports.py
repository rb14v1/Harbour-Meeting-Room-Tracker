from datetime import date, datetime, timedelta

from django.db.models import Count, Q

from meetings.models import Booking, Employee, Room
from meetings.services import split_facilities

UTILISATION_WINDOW_DAYS = 30
WORK_MINUTES_PER_DAY = (18 - 8) * 60  # 08:00-18:00


def _minutes(booking) -> int:
    return (booking.end_time.hour * 60 + booking.end_time.minute) - (
        booking.start_time.hour * 60 + booking.start_time.minute)


def dashboard_summary(day: date, now: datetime) -> dict:
    rooms = list(Room.objects.all())
    active = [r for r in rooms if r.status == Room.Status.ACTIVE]
    confirmed_today = Booking.objects.filter(booking_date=day, status=Booking.Status.CONFIRMED)

    overview = []
    occupied_count = 0
    is_today = day == now.date()
    now_t = now.time()
    for room in active:
        todays = [b for b in confirmed_today if b.room_id == room.pk]
        current = next((b for b in todays if b.start_time <= now_t < b.end_time), None) if is_today else None
        upcoming = sorted(
            (b for b in todays if (b.end_time > now_t if is_today else True) and b is not current),
            key=lambda b: b.start_time,
        )
        nxt = upcoming[0] if upcoming else None
        if current:
            occupied_count += 1
        overview.append({
            "room_id": room.pk,
            "room_name": room.room_name,
            "location": room.location,
            "capacity": room.capacity,
            "facilities": split_facilities(room.facilities),
            "status": room.status,
            "occupied_now": current is not None,
            "current_meeting": ({"meeting_title": current.meeting_title,
                                 "end_time": current.end_time.strftime("%H:%M")} if current else None),
            "next_meeting": ({"meeting_title": nxt.meeting_title,
                              "start_time": nxt.start_time.strftime("%H:%M"),
                              "end_time": nxt.end_time.strftime("%H:%M")} if nxt else None),
        })

    upcoming_today = [b for b in confirmed_today.select_related("room", "employee")
                      .order_by("start_time") if (b.end_time > now_t if is_today else True)][:6]
    recent = Booking.objects.select_related("room", "employee").order_by("-pk")[:8]

    return {
        "date": day.isoformat(),
        "total_rooms": len(rooms),
        "active_rooms": len(active),
        "inactive_rooms": len(rooms) - len(active),
        "available_now": len(active) - occupied_count if is_today else len(active),
        "occupied_now": occupied_count,
        "bookings_today": confirmed_today.count(),
        "upcoming_meetings": [{
            "booking_id": b.pk, "room_name": b.room.room_name, "employee_name": b.employee.employee_name,
            "meeting_title": b.meeting_title, "booking_date": b.booking_date.isoformat(),
            "start_time": b.start_time.strftime("%H:%M"), "end_time": b.end_time.strftime("%H:%M"),
        } for b in upcoming_today],
        "recent_activity": [{
            "booking_id": b.pk, "room_name": b.room.room_name, "employee_name": b.employee.employee_name,
            "meeting_title": b.meeting_title, "booking_date": b.booking_date.isoformat(),
            "start_time": b.start_time.strftime("%H:%M"), "end_time": b.end_time.strftime("%H:%M"),
            "status": b.status, "created_at": b.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        } for b in recent],
        "room_overview": overview,
    }


def reports_summary(today: date) -> dict:
    confirmed = Booking.objects.filter(status=Booking.Status.CONFIRMED)

    day_counts = {row["booking_date"]: row["n"] for row in confirmed.filter(
        booking_date__range=(today - timedelta(days=6), today)
    ).values("booking_date").annotate(n=Count("pk"))}
    daily = [{"label": (today - timedelta(days=i)).isoformat(),
              "count": day_counts.get(today - timedelta(days=i), 0)} for i in range(6, -1, -1)]

    week_start = today - timedelta(days=today.weekday())
    weekly = []
    for i in range(3, -1, -1):
        ws = week_start - timedelta(weeks=i)
        we = ws + timedelta(days=6)
        weekly.append({"label": f"{ws.isoformat()} to {we.isoformat()}",
                       "count": confirmed.filter(booking_date__range=(ws, we)).count()})

    top = (confirmed.values("room__room_name")
           .annotate(n=Count("pk")).order_by("-n", "room__room_name").first())

    window_start = today - timedelta(days=UTILISATION_WINDOW_DAYS - 1)
    window = list(confirmed.filter(booking_date__gte=window_start).select_related("room"))
    minutes_by_room: dict[int, int] = {}
    for b in window:
        minutes_by_room[b.room_id] = minutes_by_room.get(b.room_id, 0) + _minutes(b)
    capacity_minutes = WORK_MINUTES_PER_DAY * UTILISATION_WINDOW_DAYS
    utilisation = [{
        "room_name": r.room_name,
        "status": r.status,
        "booked_hours": round(minutes_by_room.get(r.pk, 0) / 60, 1),
        "utilisation_pct": round(100 * minutes_by_room.get(r.pk, 0) / capacity_minutes, 1),
    } for r in Room.objects.order_by("room_name")]

    employees = []
    for e in Employee.objects.annotate(
        confirmed_n=Count("bookings", filter=Q(bookings__status=Booking.Status.CONFIRMED)),
        cancelled_n=Count("bookings", filter=Q(bookings__status=Booking.Status.CANCELLED)),
    ).filter(Q(confirmed_n__gt=0) | Q(cancelled_n__gt=0)):
        minutes = sum(_minutes(b) for b in e.bookings.filter(status=Booking.Status.CONFIRMED))
        employees.append({
            "employee_name": e.employee_name, "department": e.department,
            "confirmed": e.confirmed_n, "cancelled": e.cancelled_n,
            "hours": round(minutes / 60, 1),
        })
    employees.sort(key=lambda x: (-x["confirmed"], x["employee_name"]))

    return {
        "daily": daily,
        "weekly": weekly,
        "most_booked_room": ({"room_name": top["room__room_name"], "count": top["n"]} if top else None),
        "utilisation": utilisation,
        "utilisation_window_days": UTILISATION_WINDOW_DAYS,
        "employees": employees[:20],
    }
