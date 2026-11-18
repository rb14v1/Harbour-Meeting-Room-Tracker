# Booking Rules

## Overlap

A booking conflicts with an existing **confirmed** booking in the same room on the same date when:

```
existing.start_time < new.end_time  AND  existing.end_time > new.start_time
```

| Existing | New | Result |
|---|---|---|
| 10:00–11:00 | 10:30–11:30 | Rejected (409) |
| 10:00–11:00 | 11:00–12:00 | Allowed (back-to-back) |
| 10:00–11:00 | 09:00–10:00 | Allowed |

## Validation

- `end_time` must be later than `start_time` (422).
- `booking_date` must be a real date in `YYYY-MM-DD` form (422).
- Past dates are rejected. For today, a start time already passed is rejected (422).
- Inactive rooms cannot be booked (409).
- Email must be valid. The employee is created on first booking and updated on later ones, keyed by email (case-insensitive).

## Cancellation

- Cancelling sets `status = 'Cancelled'`. The row stays for history.
- Cancelled bookings do not block new reservations.
- Already cancelled bookings return 409.
- Past bookings cannot be cancelled (409).

## Room deletion

- Rooms with no bookings are deleted.
- Rooms with any booking history are deactivated instead, so history stays intact.

## Availability states

| State | Meaning |
|---|---|
| Available | Active room, no confirmed booking overlaps the requested window |
| Occupied | At least one confirmed booking overlaps the window |
| Inactive | Room status is Inactive |

Availability is calculated per request for the selected date and time window. There is no stored room status.
