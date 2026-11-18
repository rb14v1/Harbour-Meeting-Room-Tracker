import sqlite3
from datetime import datetime

from fastapi import HTTPException

from app.database import read_connection, write_transaction
from app.schemas import BookingIn
from app.utils import now_local, parse_date

BOOKING_SELECT = """
SELECT b.booking_id, b.room_id, r.room_name, r.location, r.capacity, b.employee_id,
       e.employee_name, e.email, e.department, b.meeting_title, b.booking_date,
       b.start_time, b.end_time, b.status, b.created_at
FROM bookings b
JOIN rooms r ON r.room_id = b.room_id
JOIN employees e ON e.employee_id = b.employee_id
"""


def _has_ended(booking_date: str, end_time: str, now: datetime) -> bool:
    today = now.date().isoformat()
    return booking_date < today or (booking_date == today and end_time <= now.strftime("%H:%M"))


def _with_flags(row: sqlite3.Row, now: datetime) -> dict:
    booking = dict(row)
    ended = _has_ended(booking["booking_date"], booking["end_time"], now)
    booking["is_past"] = ended
    booking["can_edit"] = booking["status"] == "Confirmed" and not ended
    booking["can_cancel"] = booking["can_edit"]
    return booking


def _ensure_not_past(day, start_time: str) -> None:
    now = now_local()
    if day < now.date():
        raise HTTPException(422, "Booking date cannot be in the past")
    if day == now.date() and start_time <= now.strftime("%H:%M"):
        raise HTTPException(422, "Start time has already passed for today")


def _validate_and_upsert(conn, data: BookingIn, day, exclude_booking_id: int | None = None) -> int:
    """Shared checks for create and edit. Returns the employee_id to store on the booking."""
    _ensure_not_past(day, data.start_time)

    room = conn.execute("SELECT room_name, status FROM rooms WHERE room_id = ?", (data.room_id,)).fetchone()
    if not room:
        raise HTTPException(404, "Room not found")
    if room["status"] != "Active":
        raise HTTPException(409, f"{room['room_name']} is inactive and cannot be booked")

    employee = conn.execute(
        """
        INSERT INTO employees (employee_name, email, department) VALUES (?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET employee_name = excluded.employee_name,
                                         department = excluded.department
        RETURNING employee_id
        """,
        (data.employee_name, data.employee_email.lower(), data.department),
    ).fetchone()

    # Overlap rule: existing.start < new.end AND existing.end > new.start.
    # Back-to-back meetings (10-11 then 11-12) do not overlap.
    # exclude_booking_id stops an edited booking from clashing with itself.
    clash = conn.execute(
        """
        SELECT b.meeting_title, b.start_time, b.end_time
        FROM bookings b
        WHERE b.room_id = ? AND b.booking_date = ? AND b.status = 'Confirmed'
          AND b.start_time < ? AND b.end_time > ?
          AND b.booking_id IS NOT ?
        LIMIT 1
        """,
        (data.room_id, day.isoformat(), data.end_time, data.start_time, exclude_booking_id),
    ).fetchone()
    if clash:
        raise HTTPException(
            409,
            f"Room already booked {clash['start_time']}-{clash['end_time']} ({clash['meeting_title']})",
        )
    return employee["employee_id"]


def create_booking(data: BookingIn) -> dict:
    day = parse_date(data.booking_date, "booking_date")
    with write_transaction() as conn:
        employee_id = _validate_and_upsert(conn, data, day)
        cur = conn.execute(
            """
            INSERT INTO bookings (room_id, employee_id, meeting_title, booking_date, start_time, end_time, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Confirmed')
            """,
            (data.room_id, employee_id, data.meeting_title, day.isoformat(), data.start_time, data.end_time),
        )
        booking_id = cur.lastrowid
    return get_booking(booking_id)


def update_booking(booking_id: int, data: BookingIn) -> dict:
    day = parse_date(data.booking_date, "booking_date")
    with write_transaction() as conn:
        current = conn.execute(
            "SELECT booking_date, end_time, status FROM bookings WHERE booking_id = ?", (booking_id,)
        ).fetchone()
        if not current:
            raise HTTPException(404, "Booking not found")
        if current["status"] != "Confirmed":
            raise HTTPException(409, "Cancelled bookings cannot be edited")
        if _has_ended(current["booking_date"], current["end_time"], now_local()):
            raise HTTPException(409, "Past bookings cannot be edited")

        employee_id = _validate_and_upsert(conn, data, day, exclude_booking_id=booking_id)
        conn.execute(
            """
            UPDATE bookings
            SET room_id = ?, employee_id = ?, meeting_title = ?, booking_date = ?, start_time = ?, end_time = ?
            WHERE booking_id = ?
            """,
            (data.room_id, employee_id, data.meeting_title, day.isoformat(),
             data.start_time, data.end_time, booking_id),
        )
    return get_booking(booking_id)


def get_booking(booking_id: int) -> dict:
    with read_connection() as conn:
        row = conn.execute(BOOKING_SELECT + " WHERE b.booking_id = ?", (booking_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Booking not found")
    return _with_flags(row, now_local())


def list_bookings(view: str = "all", search: str | None = None, room_id: int | None = None,
                  booking_date: str | None = None) -> list[dict]:
    clauses, params = [], []
    now = now_local()
    today = now.date().isoformat()
    now_hm = now.strftime("%H:%M")

    if view == "upcoming":
        clauses.append("b.status = 'Confirmed' AND (b.booking_date > ? OR (b.booking_date = ? AND b.end_time > ?))")
        params += [today, today, now_hm]
    elif view == "past":
        clauses.append("b.status = 'Confirmed' AND (b.booking_date < ? OR (b.booking_date = ? AND b.end_time <= ?))")
        params += [today, today, now_hm]
    elif view == "cancelled":
        clauses.append("b.status = 'Cancelled'")

    if search and search.strip():
        clauses.append("e.employee_name LIKE ? ESCAPE '\\'")
        escaped = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        params.append(f"%{escaped}%")
    if room_id:
        clauses.append("b.room_id = ?")
        params.append(room_id)
    if booking_date:
        clauses.append("b.booking_date = ?")
        params.append(parse_date(booking_date, "date").isoformat())

    sql = BOOKING_SELECT
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY b.booking_date DESC, b.start_time DESC LIMIT 500"
    with read_connection() as conn:
        return [_with_flags(r, now) for r in conn.execute(sql, params)]


def cancel_booking(booking_id: int) -> dict:
    with write_transaction() as conn:
        row = conn.execute("SELECT booking_date, end_time, status FROM bookings WHERE booking_id = ?",
                           (booking_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Booking not found")
        if row["status"] == "Cancelled":
            raise HTTPException(409, "Booking is already cancelled")
        if _has_ended(row["booking_date"], row["end_time"], now_local()):
            raise HTTPException(409, "Past bookings cannot be cancelled")
        conn.execute("UPDATE bookings SET status = 'Cancelled' WHERE booking_id = ?", (booking_id,))
    return get_booking(booking_id)
