# API Reference

Base path: `/api`. Requests use JSON. Trailing slashes are not used, for example `/api/rooms`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/dashboard?date=YYYY-MM-DD` | Summary cards, room overview, upcoming meetings, recent activity |
| GET | `/rooms?include_inactive=true` | List rooms |
| POST | `/rooms` | Create room |
| GET | `/rooms/{id}` | Get room |
| PUT | `/rooms/{id}` | Update room |
| DELETE | `/rooms/{id}` | Delete room, or deactivate if it has bookings |
| GET | `/availability?date&start&end[&capacity][&search][&facilities=...]` | Availability for a time window |
| GET | `/bookings?view=all\|upcoming\|past\|cancelled[&search][&room_id][&date]` | List bookings |
| POST | `/bookings` | Create booking |
| GET | `/bookings/{id}` | Booking details |
| PUT | `/bookings/{id}` | Edit a confirmed, upcoming booking (same body as create) |
| POST | `/bookings/{id}/cancel` | Cancel a confirmed, upcoming booking |
| GET | `/reports/summary` | Daily/weekly counts, most booked room, utilisation, employee stats |
| GET | `/health` | Liveness check, returns `{"status": "ok"}` |

## Example: create booking

```http
POST /api/bookings
Content-Type: application/json

{
  "room_id": 1,
  "employee_name": "Priya Sharma",
  "employee_email": "priya.sharma@example.com",
  "department": "Engineering",
  "meeting_title": "Sprint planning",
  "booking_date": "2026-11-20",
  "start_time": "10:00",
  "end_time": "11:00"
}
```

Responses: `201` with the booking, `409` on overlap or inactive room, `422` on validation failure.

## Errors

- `409` and `404` return `{"detail": "message"}`.
- `422` from field validation returns `{"detail": [{"field": "...", "message": "..."}]}`.
