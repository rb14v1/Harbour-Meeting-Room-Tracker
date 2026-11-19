from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from meetings.models import Booking, Employee, Room

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

DEMO_BOOKINGS = [
    # room name, employee email, title, day offset, start, end
    ("Conference Room A", "priya.sharma@example.com", "Sprint planning", 0, "09:00", "10:00"),
    ("Huddle Room 1", "james.carter@example.com", "Client call prep", 0, "14:00", "14:30"),
    ("Conference Room B", "amelia.brooks@example.com", "Interview panel", 1, "10:00", "11:00"),
    ("Boardroom", "ravi.kumar@example.com", "Quarterly review", 2, "13:00", "15:00"),
    ("Innovation Lab", "sophie.turner@example.com", "Campaign brainstorm", 3, "11:00", "12:30"),
]


class Command(BaseCommand):
    help = "Insert sample rooms and employees. Safe to run repeatedly."

    @transaction.atomic
    def handle(self, *args, **options):
        for name, location, capacity, facilities in SAMPLE_ROOMS:
            Room.objects.get_or_create(
                room_name=name,
                defaults={"location": location, "capacity": capacity, "facilities": facilities},
            )
        for name, email, department in SAMPLE_EMPLOYEES:
            Employee.objects.get_or_create(
                email=email, defaults={"employee_name": name, "department": department},
            )
        if not Booking.objects.exists():
            today = date.today()
            for room_name, email, title, offset, start, end in DEMO_BOOKINGS:
                Booking.objects.create(
                    room=Room.objects.get(room_name=room_name),
                    employee=Employee.objects.get(email=email),
                    meeting_title=title,
                    booking_date=today + timedelta(days=offset),
                    start_time=start,
                    end_time=end,
                )
        self.stdout.write(self.style.SUCCESS("Sample data is in place."))
