CREATE TABLE IF NOT EXISTS employees (
    employee_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name TEXT    NOT NULL CHECK (length(trim(employee_name)) > 0),
    email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    department    TEXT    NOT NULL DEFAULT 'General'
);

CREATE TABLE IF NOT EXISTS rooms (
    room_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    room_name  TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    location   TEXT    NOT NULL,
    capacity   INTEGER NOT NULL CHECK (capacity > 0),
    facilities TEXT    NOT NULL DEFAULT '',
    status     TEXT    NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive'))
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id       INTEGER NOT NULL REFERENCES rooms(room_id) ON DELETE RESTRICT,
    employee_id   INTEGER NOT NULL REFERENCES employees(employee_id) ON DELETE RESTRICT,
    meeting_title TEXT    NOT NULL CHECK (length(trim(meeting_title)) > 0),
    booking_date  TEXT    NOT NULL CHECK (booking_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    start_time    TEXT    NOT NULL CHECK (start_time GLOB '[0-2][0-9]:[0-5][0-9]'),
    end_time      TEXT    NOT NULL CHECK (end_time GLOB '[0-2][0-9]:[0-5][0-9]'),
    status        TEXT    NOT NULL DEFAULT 'Confirmed' CHECK (status IN ('Confirmed', 'Cancelled')),
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
    CHECK (end_time > start_time)
);

CREATE INDEX IF NOT EXISTS idx_bookings_room_date ON bookings (room_id, booking_date, status);
CREATE INDEX IF NOT EXISTS idx_bookings_date ON bookings (booking_date, status);
CREATE INDEX IF NOT EXISTS idx_bookings_employee ON bookings (employee_id);
CREATE INDEX IF NOT EXISTS idx_bookings_created ON bookings (created_at);
