import re

from rest_framework import serializers

from meetings.exceptions import Conflict
from meetings.models import Booking, Room
from meetings.services import booking_flags, now_local, split_facilities

NAME_RE = re.compile(r"[A-Za-z]+(?: [A-Za-z]+)*")


class FacilitiesField(serializers.Field):
    """Accepts a list or comma-separated string; stores comma-separated text."""

    def to_internal_value(self, data):
        if data is None:
            return ""
        if isinstance(data, str):
            items = data.split(",")
        elif isinstance(data, list):
            items = data
        else:
            raise serializers.ValidationError("Facilities must be a list.")
        cleaned, seen = [], set()
        for item in items:
            name = str(item).strip()
            if name and name.lower() not in seen:
                seen.add(name.lower())
                cleaned.append(name)
        return ", ".join(cleaned)

    def to_representation(self, value):
        return split_facilities(value)


class RoomSerializer(serializers.ModelSerializer):
    room_id = serializers.IntegerField(source="pk", read_only=True)
    room_name = serializers.CharField(min_length=2, max_length=100)
    location = serializers.CharField(min_length=2, max_length=120)
    capacity = serializers.IntegerField(min_value=1, max_value=500)
    facilities = FacilitiesField(required=False)

    class Meta:
        model = Room
        fields = ["room_id", "room_name", "location", "capacity", "facilities", "status"]

    def validate_room_name(self, value):
        value = value.strip()
        clash = Room.objects.filter(room_name__iexact=value)
        if self.instance is not None:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise Conflict(f"A room named '{value}' already exists")
        return value


class BookingWriteSerializer(serializers.Serializer):
    room_id = serializers.IntegerField(min_value=1)
    employee_name = serializers.CharField(max_length=100)
    employee_email = serializers.EmailField(max_length=254)
    department = serializers.CharField(max_length=80, required=False, allow_blank=True, default="")
    meeting_title = serializers.CharField(min_length=3, max_length=150)
    booking_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    start_time = serializers.TimeField(input_formats=["%H:%M"])
    end_time = serializers.TimeField(input_formats=["%H:%M"])

    def validate_employee_name(self, value):
        name = " ".join(value.split())
        if len(name) < 2:
            raise serializers.ValidationError("Enter your name.")
        if not NAME_RE.fullmatch(name):
            raise serializers.ValidationError("Use English letters and single spaces only.")
        return name

    def validate(self, attrs):
        if attrs["end_time"] <= attrs["start_time"]:
            raise serializers.ValidationError({"end_time": "end_time must be later than start_time"})
        attrs["department"] = attrs.get("department", "").strip() or "General"
        return attrs


class BookingReadSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source="pk", read_only=True)
    room_id = serializers.IntegerField(read_only=True)
    room_name = serializers.CharField(source="room.room_name", read_only=True)
    location = serializers.CharField(source="room.location", read_only=True)
    capacity = serializers.IntegerField(source="room.capacity", read_only=True)
    employee_id = serializers.IntegerField(read_only=True)
    employee_name = serializers.CharField(source="employee.employee_name", read_only=True)
    email = serializers.EmailField(source="employee.email", read_only=True)
    department = serializers.CharField(source="employee.department", read_only=True)
    start_time = serializers.TimeField(format="%H:%M", read_only=True)
    end_time = serializers.TimeField(format="%H:%M", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "booking_id", "room_id", "room_name", "location", "capacity", "employee_id", "employee_name",
            "email", "department", "meeting_title", "booking_date", "start_time", "end_time", "status",
            "created_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["booking_date"] = instance.booking_date.isoformat()
        data.update(booking_flags(instance, now_local()))
        return data
