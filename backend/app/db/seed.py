from datetime import date, timedelta

from app.database import write_transaction

SAMPLE_ROOMS = [
    ("Conference Room A", "Floor 1, East Wing", 12, "Projector, Wi-Fi, Whiteboard, Video Conferencing"),
    ("Conference Room B", "Floor 1, West Wing", 8, "TV Screen, Wi-Fi, Whiteboard"),
    ("Boardroom", "Floor 3, Executive Suite", 16, "Projector, Wi-Fi, Video Conferencing, Speakerphone"),
    ("Huddle Room 1", "Floor 2, Open Plan", 4, "TV Screen, Wi-Fi"),
    ("Huddle Room 2", "Floor 2, Open Plan", 4, "Wi-Fi, Whiteboard"),
    ("Innovation Lab", "Floor 4, North Wing", 10, "Projector, Wi-Fi, Whiteboard, TV Screen"),
]

SAMPLE_EMPLOYEES = [
    ("Priya Sharma", "priya.sharma@example.com", "Engineering"),
    ("James Carter", "james.carter@example.com", "Sales"),
    ("Amelia Brooks", "amelia.brooks@example.com", "HR"),
    ("Ravi Kumar", "ravi.kumar@example.com", "IT Operations"),
    ("Sophie Turner", "sophie.turner@example.com", "Marketing"),
]


def seed_database() -> None:
    """Insert sample data once. Uses INSERT OR IGNORE so restarts never duplicate rows."""
    with write_transaction() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO rooms (room_name, location, capacity, facilities, status) VALUES (?, ?, ?, ?, 'Active')",
            SAMPLE_ROOMS,
        )
        conn.executemany(
            "INSERT OR IGNORE INTO employees (employee_name, email, department) VALUES (?, ?, ?)",
            SAMPLE_EMPLOYEES,
        )
        has_bookings = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0] > 0
        if not has_bookings:
            _insert_demo_bookings(conn)


def _insert_demo_bookings(conn) -> None:
    today = date.today()
    room_ids = {r["room_name"]: r["room_id"] for r in conn.execute("SELECT room_id, room_name FROM rooms")}
    emp_ids = {r["email"]: r["employee_id"] for r in conn.execute("SELECT employee_id, email FROM employees")}
    demo = [
        (0, "Conference Room A", "priya.sharma@example.com", "Sprint planning", 0, "09:00", "10:00"),
        (0, "Huddle Room 1", "james.carter@example.com", "Client call prep", 0, "14:00", "14:30"),
        (1, "Conference Room B", "amelia.brooks@example.com", "Interview panel", 1, "10:00", "11:00"),
        (2, "Boardroom", "ravi.kumar@example.com", "Quarterly review", 2, "13:00", "15:00"),
        (3, "Innovation Lab", "sophie.turner@example.com", "Campaign brainstorm", 3, "11:00", "12:30"),
    ]
    for _, room, email, title, offset, start, end in demo:
        d = (today + timedelta(days=offset)).isoformat()
        conn.execute(
            "INSERT INTO bookings (room_id, employee_id, meeting_title, booking_date, start_time, end_time, status) "
            "VALUES (?, ?, ?, ?, ?, ?, 'Confirmed')",
            (room_ids[room], emp_ids[email], title, d, start, end),
        )
