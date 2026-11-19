from datetime import date, timedelta

from meetings.models import Room

FUTURE = date.today() + timedelta(days=7)


def make_room(name="Conference Room A", capacity=8, facilities="Wi-Fi", status=Room.Status.ACTIVE):
    return Room.objects.create(room_name=name, location="Floor 1", capacity=capacity,
                               facilities=facilities, status=status)


def booking_payload(room, start, end, email="tester@example.com", title="Test meeting",
                    day=None, name="Test User", department="QA"):
    return {
        "room_id": room.pk,
        "employee_name": name,
        "employee_email": email,
        "department": department,
        "meeting_title": title,
        "booking_date": (day or FUTURE).isoformat(),
        "start_time": start,
        "end_time": end,
    }
