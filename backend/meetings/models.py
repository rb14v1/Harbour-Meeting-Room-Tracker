from django.contrib.postgres.constraints import ExclusionConstraint
from django.db import models
from django.db.models import Q
from django.db.models.expressions import RawSQL


class Employee(models.Model):
    employee_id = models.AutoField(primary_key=True)
    employee_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=80, default="General")

    class Meta:
        db_table = "employees"
        ordering = ["employee_name"]

    def __str__(self):
        return self.employee_name


class Room(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "Active", "Active"
        INACTIVE = "Inactive", "Inactive"

    room_id = models.AutoField(primary_key=True)
    room_name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=120)
    capacity = models.PositiveIntegerField()
    facilities = models.CharField(max_length=500, blank=True, default="")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        db_table = "rooms"
        ordering = ["room_name"]
        constraints = [
            models.CheckConstraint(check=Q(capacity__gt=0), name="room_capacity_positive"),
        ]

    def __str__(self):
        return self.room_name


class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "Confirmed", "Confirmed"
        CANCELLED = "Cancelled", "Cancelled"

    booking_id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="bookings", db_column="room_id")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="bookings",
                                 db_column="employee_id")
    meeting_title = models.CharField(max_length=150)
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.CONFIRMED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bookings"
        ordering = ["-booking_date", "-start_time"]
        indexes = [
            models.Index(fields=["room", "booking_date", "status"], name="idx_booking_room_date"),
            models.Index(fields=["booking_date", "status"], name="idx_booking_date"),
        ]
        constraints = [
            models.CheckConstraint(check=Q(end_time__gt=models.F("start_time")),
                                   name="booking_end_after_start"),
            # Database-level guarantee: two confirmed bookings in the same room cannot overlap.
            # Time range is [start, end), so back-to-back meetings are allowed.
            ExclusionConstraint(
                name="no_overlapping_confirmed_bookings",
                expressions=[
                    ("room", "="),
                    (RawSQL("tsrange(booking_date + start_time, booking_date + end_time)", []), "&&"),
                ],
                condition=Q(status="Confirmed"),
            ),
        ]

    def __str__(self):
        return f"{self.meeting_title} ({self.booking_date} {self.start_time}-{self.end_time})"
