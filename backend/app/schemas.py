import re
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.utils import parse_date, parse_time_minutes

# English letters only (A-Z, a-z), with single spaces between words.
NAME_RE = re.compile(r"[A-Za-z]+(?: [A-Za-z]+)*")


def _normalise_facilities(value) -> list[str]:
    if value is None:
        return []
    items = value.split(",") if isinstance(value, str) else value
    cleaned = []
    seen = set()
    for item in items:
        name = str(item).strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            cleaned.append(name)
    return cleaned


class RoomIn(BaseModel):
    room_name: str = Field(min_length=2, max_length=100)
    location: str = Field(min_length=2, max_length=120)
    capacity: int = Field(ge=1, le=500)
    facilities: list[str] = Field(default_factory=list)
    status: Literal["Active", "Inactive"] = "Active"

    @field_validator("room_name", "location")
    @classmethod
    def strip_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v

    @field_validator("facilities", mode="before")
    @classmethod
    def normalise(cls, v):
        return _normalise_facilities(v)


class BookingIn(BaseModel):
    room_id: int = Field(gt=0)
    employee_name: str = Field(min_length=2, max_length=100)
    employee_email: EmailStr
    department: str = Field(default="General", max_length=80)
    meeting_title: str = Field(min_length=3, max_length=150)
    booking_date: str
    start_time: str
    end_time: str

    @field_validator("employee_name")
    @classmethod
    def name_letters_only(cls, v: str) -> str:
        name = " ".join(v.split())
        if not NAME_RE.fullmatch(name):
            raise ValueError("name may contain only letters and single spaces")
        return name

    @field_validator("meeting_title", "department")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()

    @model_validator(mode="after")
    def check_times(self):
        parse_date(self.booking_date, "booking_date")
        start = parse_time_minutes(self.start_time, "start_time")
        end = parse_time_minutes(self.end_time, "end_time")
        if end <= start:
            raise ValueError("end_time must be later than start_time")
        return self
