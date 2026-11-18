from datetime import timedelta

from app.config import WORK_END, WORK_START
from app.database import read_connection
from app.services.rooms import room_status_at
from app.utils import now_local, parse_time_minutes

UTILISATION_WINDOW_DAYS = 30


def _working_minutes() -> int:
    return parse_time_minutes(WORK_END) - parse_time_minutes(WORK_START)


def dashboard_summary(date_str: str | None = None) -> dict:
    from app.utils import parse_date
    now = now_local()
    day = parse_date(date_str) if date_str else now.date()
    with read_connection() as conn:
        rooms = [dict(r) for r in conn.execute(
            "SELECT room_id, room_name, location, capacity, facilities, status FROM rooms ORDER BY room_name COLLATE NOCASE")]
        for r in rooms:
            r["facilities"] = [f.strip() for f in (r["facilities"] or "").split(",") if f.strip()]
        bookings_today = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE booking_date = ? AND status = 'Confirmed'", (day.isoformat(),)
        ).fetchone()[0]
        upcoming = [dict(r) for r in conn.execute(
            """
            SELECT b.booking_id, r.room_name, e.employee_name, b.meeting_title, b.booking_date,
                   b.start_time, b.end_time
            FROM bookings b JOIN rooms r ON r.room_id = b.room_id JOIN employees e ON e.employee_id = b.employee_id
            WHERE b.status = 'Confirmed' AND b.booking_date = ? AND b.end_time > ?
            ORDER BY b.start_time LIMIT 6
            """,
            (day.isoformat(), now.strftime("%H:%M") if day == now.date() else "00:00"),
        )]
        recent = [dict(r) for r in conn.execute(
            """
            SELECT b.booking_id, r.room_name, e.employee_name, b.meeting_title, b.booking_date,
                   b.start_time, b.end_time, b.status, b.created_at
            FROM bookings b JOIN rooms r ON r.room_id = b.room_id JOIN employees e ON e.employee_id = b.employee_id
            ORDER BY b.booking_id DESC LIMIT 8
            """
        )]

    active = [r for r in rooms if r["status"] == "Active"]
    overview = room_status_at(now.date(), now, active) if day == now.date() else [
        {**r, "occupied_now": False, "current_meeting": None, "next_meeting": None} for r in active]
    occupied = sum(1 for r in overview if r["occupied_now"])
    return {
        "date": day.isoformat(),
        "total_rooms": len(rooms),
        "active_rooms": len(active),
        "inactive_rooms": len(rooms) - len(active),
        "available_now": len(active) - occupied if day == now.date() else len(active),
        "occupied_now": occupied,
        "bookings_today": bookings_today,
        "upcoming_meetings": upcoming,
        "recent_activity": recent,
        "room_overview": overview,
    }


def reports_summary() -> dict:
    today = now_local().date()
    with read_connection() as conn:
        daily_rows = {r["d"]: r["n"] for r in conn.execute(
            "SELECT booking_date AS d, COUNT(*) AS n FROM bookings WHERE status='Confirmed' "
            "AND booking_date BETWEEN ? AND ? GROUP BY booking_date",
            ((today - timedelta(days=6)).isoformat(), today.isoformat()))}
        daily = []
        for i in range(6, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            daily.append({"label": d, "count": daily_rows.get(d, 0)})

        week_start = today - timedelta(days=today.weekday())
        weekly = []
        for i in range(3, -1, -1):
            ws = week_start - timedelta(weeks=i)
            we = ws + timedelta(days=6)
            n = conn.execute(
                "SELECT COUNT(*) FROM bookings WHERE status='Confirmed' AND booking_date BETWEEN ? AND ?",
                (ws.isoformat(), we.isoformat())).fetchone()[0]
            weekly.append({"label": f"{ws.isoformat()} to {we.isoformat()}", "count": n})

        top = conn.execute(
            """
            SELECT r.room_name, COUNT(*) AS n FROM bookings b JOIN rooms r ON r.room_id = b.room_id
            WHERE b.status = 'Confirmed' GROUP BY b.room_id ORDER BY n DESC, r.room_name LIMIT 1
            """).fetchone()

        window_start = (today - timedelta(days=UTILISATION_WINDOW_DAYS - 1)).isoformat()
        booked = {r["room_id"]: r["minutes"] for r in conn.execute(
            """
            SELECT room_id, SUM((CAST(substr(end_time,1,2) AS INTEGER)*60 + CAST(substr(end_time,4,2) AS INTEGER))
                              - (CAST(substr(start_time,1,2) AS INTEGER)*60 + CAST(substr(start_time,4,2) AS INTEGER))) AS minutes
            FROM bookings WHERE status='Confirmed' AND booking_date >= ? GROUP BY room_id
            """, (window_start,))}
        rooms = conn.execute("SELECT room_id, room_name, status FROM rooms ORDER BY room_name COLLATE NOCASE").fetchall()

        employees = [dict(r) for r in conn.execute(
            """
            SELECT e.employee_name, e.department,
                   SUM(CASE WHEN b.status='Confirmed' THEN 1 ELSE 0 END) AS confirmed,
                   SUM(CASE WHEN b.status='Cancelled' THEN 1 ELSE 0 END) AS cancelled,
                   COALESCE(SUM(CASE WHEN b.status='Confirmed' THEN
                       (CAST(substr(b.end_time,1,2) AS INTEGER)*60 + CAST(substr(b.end_time,4,2) AS INTEGER))
                     - (CAST(substr(b.start_time,1,2) AS INTEGER)*60 + CAST(substr(b.start_time,4,2) AS INTEGER))
                     ELSE 0 END), 0) AS minutes
            FROM employees e JOIN bookings b ON b.employee_id = e.employee_id
            GROUP BY e.employee_id ORDER BY confirmed DESC, e.employee_name LIMIT 20
            """)]

    capacity_minutes = _working_minutes() * UTILISATION_WINDOW_DAYS
    utilisation = [{
        "room_name": r["room_name"],
        "status": r["status"],
        "booked_hours": round(booked.get(r["room_id"], 0) / 60, 1),
        "utilisation_pct": round(100 * booked.get(r["room_id"], 0) / capacity_minutes, 1),
    } for r in rooms]

    return {
        "daily": daily,
        "weekly": weekly,
        "most_booked_room": ({"room_name": top["room_name"], "count": top["n"]} if top else None),
        "utilisation": utilisation,
        "utilisation_window_days": UTILISATION_WINDOW_DAYS,
        "employees": [{**e, "hours": round(e["minutes"] / 60, 1)} for e in employees],
    }
