from django.contrib import admin

from meetings.models import Booking, Employee, Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_name", "location", "capacity", "status")
    list_filter = ("status",)
    search_fields = ("room_name", "location")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_name", "email", "department")
    search_fields = ("employee_name", "email")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("booking_id", "meeting_title", "room", "employee", "booking_date", "start_time", "end_time", "status")
    list_filter = ("status", "booking_date")
    search_fields = ("meeting_title", "employee__employee_name")
