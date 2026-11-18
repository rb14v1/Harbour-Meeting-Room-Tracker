import sqlite3
from datetime import date, datetime

from fastapi import HTTPException

from app.database import read_connection, write_transaction
from app.schemas import RoomIn
from app.utils import now_local, parse_date, parse_time_minutes, minutes_to_hhmm


def split_facilities(raw: str) -> list[str]:
    return [f.strip() for f in (raw or "").split(",") if f.strip()]


def _room_dict(row: sqlite3.Row) -> dict:
    return {
        "room_id": row["room_id"],
        "room_name": row["room_name"],
        "location": row["location"],
        "capacity": row["capacity"],
        "facilities": split_facilities(row["facilities"]),
        "status": row["status"],
    }


def list_rooms(include_inactive: bool = True) -> list[dict]:
    sql = "SELECT * FROM rooms"
    if not include_inactive:
        sql += " WHERE status = 'Active'"
    sql += " ORDER BY room_name COLLATE NOCASE"
    with read_connection() as conn:
        return [_room_dict(r) for r in conn.execute(sql)]


def get_room(room_id: int) -> dict:
    with read_connection() as conn:
        row = conn.execute("SELECT * FROM rooms WHERE room_id = ?", (room_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Room not found")
    return _room_dict(row)


def create_room(data: RoomIn) -> dict:
    try:
        with write_transaction() as conn:
            cur = conn.execute(
                "INSERT INTO rooms (room_name, location, capacity, facilities, status) VALUES (?, ?, ?, ?, ?)",
                (data.room_name, data.location, data.capacity, ", ".join(data.facilities), data.status),
            )
            room_id = cur.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(409, f"A room named '{data.room_name}' already exists")
    return get_room(room_id)


def update_room(room_id: int, data: RoomIn) -> dict:
    get_room(room_id)
    try:
        with write_transaction() as conn:
            conn.execute(
                "UPDATE rooms SET room_name = ?, location = ?, capacity = ?, facilities = ?, status = ? WHERE room_id = ?",
                (data.room_name, data.location, data.capacity, ", ".join(data.facilities), data.status, room_id),
            )
    except sqlite3.IntegrityError:
        raise HTTPException(409, f"A room named '{data.room_name}' already exists")
    return get_room(room_id)


def delete_room(room_id: int) -> dict:
    """Hard-delete only rooms with no bookings. Rooms with history are deactivated instead."""
    get_room(room_id)
    with write_transaction() as conn:
        count = conn.execute("SELECT COUNT(*) FROM bookings WHERE room_id = ?", (room_id,)).fetchone()[0]
        if count:
            conn.execute("UPDATE rooms SET status = 'Inactive' WHERE room_id = ?", (room_id,))
            return {"deleted": False, "deactivated": True,
                    "message": f"Room has {count} booking record(s), so it was deactivated instead of deleted."}
        conn.execute("DELETE FROM rooms WHERE room_id = ?", (room_id,))
    return {"deleted": True, "deactivated": False, "message": "Room deleted."}


def room_availability(date_str: str, start: str, end: str, capacity: int | None = None,
                      search: str | None = None, facilities: list[str] | None = None) -> list[dict]:
    day = parse_date(date_str)
    start_m = parse_time_minutes(start, "start")
    end_m = parse_time_minutes(end, "end")
    if end_m <= start_m:
        raise HTTPException(422, "end must be later than start")

    wanted = [f.lower() for f in (facilities or []) if f.strip()]
    term = (search or "").strip().lower()

    with read_connection() as conn:
        rooms = [_room_dict(r) for r in conn.execute("SELECT * FROM rooms ORDER BY room_name COLLATE NOCASE")]
        clashes = conn.execute(
            """
            SELECT b.room_id, b.meeting_title, b.start_time, b.end_time
            FROM bookings b
            WHERE b.booking_date = ? AND b.status = 'Confirmed'
              AND b.start_time < ? AND b.end_time > ?
            ORDER BY b.start_time
            """,
            (day.isoformat(), end, start),
        ).fetchall()

    by_room: dict[int, list[dict]] = {}
    for c in clashes:
        by_room.setdefault(c["room_id"], []).append({
            "meeting_title": c["meeting_title"], "start_time": c["start_time"], "end_time": c["end_time"]})

    results = []
    for room in rooms:
        if term and term not in room["room_name"].lower():
            continue
        if capacity and room["capacity"] < capacity:
            continue
        if wanted:
            have = {f.lower() for f in room["facilities"]}
            if not all(w in have for w in wanted):
                continue
        conflicts = by_room.get(room["room_id"], [])
        if room["status"] != "Active":
            state = "Inactive"
        elif conflicts:
            state = "Occupied"
        else:
            state = "Available"
        results.append({**room, "available": state == "Available", "state": state, "conflicts": conflicts})
    return results


def room_status_at(day: date, now: datetime, rooms_active: list[dict]) -> list[dict]:
    """Current occupancy for each active room at the given instant (used by dashboard)."""
    now_hm = now.strftime("%H:%M")
    with read_connection() as conn:
        rows = conn.execute(
            """
            SELECT b.room_id, b.meeting_title, b.start_time, b.end_time
            FROM bookings b
            WHERE b.booking_date = ? AND b.status = 'Confirmed' AND b.end_time > ?
            ORDER BY b.start_time
            """,
            (day.isoformat(), now_hm),
        ).fetchall()
    nxt: dict[int, sqlite3.Row] = {}
    current: dict[int, sqlite3.Row] = {}
    for r in rows:
        if r["start_time"] <= now_hm < r["end_time"]:
            current.setdefault(r["room_id"], r)
        else:
            nxt.setdefault(r["room_id"], r)
    out = []
    for room in rooms_active:
        cur = current.get(room["room_id"])
        up = nxt.get(room["room_id"])
        out.append({
            **room,
            "occupied_now": cur is not None,
            "current_meeting": {"meeting_title": cur["meeting_title"], "end_time": cur["end_time"]} if cur else None,
            "next_meeting": {"meeting_title": up["meeting_title"], "start_time": up["start_time"],
                             "end_time": up["end_time"]} if up else None,
        })
    return out
