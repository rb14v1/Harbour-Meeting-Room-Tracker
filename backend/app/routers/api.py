from fastapi import APIRouter, Query

from app.schemas import BookingIn, RoomIn
from app.services import bookings as booking_service
from app.services import reports as report_service
from app.services import rooms as room_service

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/dashboard")
def dashboard(date: str | None = None):
    return report_service.dashboard_summary(date)


@router.get("/rooms")
def list_rooms(include_inactive: bool = True):
    return room_service.list_rooms(include_inactive)


@router.post("/rooms", status_code=201)
def create_room(data: RoomIn):
    return room_service.create_room(data)


@router.get("/rooms/{room_id}")
def get_room(room_id: int):
    return room_service.get_room(room_id)


@router.put("/rooms/{room_id}")
def update_room(room_id: int, data: RoomIn):
    return room_service.update_room(room_id, data)


@router.delete("/rooms/{room_id}")
def delete_room(room_id: int):
    return room_service.delete_room(room_id)


@router.get("/availability")
def availability(
    date: str,
    start: str,
    end: str,
    capacity: int | None = Query(default=None, ge=1),
    search: str | None = None,
    facilities: list[str] = Query(default_factory=list),
):
    return room_service.room_availability(date, start, end, capacity, search, facilities)


@router.get("/bookings")
def list_bookings(
    view: str = Query(default="all", pattern="^(all|upcoming|past|cancelled)$"),
    search: str | None = None,
    room_id: int | None = None,
    date: str | None = None,
):
    return booking_service.list_bookings(view, search, room_id, date)


@router.post("/bookings", status_code=201)
def create_booking(data: BookingIn):
    return booking_service.create_booking(data)


@router.get("/bookings/{booking_id}")
def get_booking(booking_id: int):
    return booking_service.get_booking(booking_id)


@router.put("/bookings/{booking_id}")
def update_booking(booking_id: int, data: BookingIn):
    return booking_service.update_booking(booking_id, data)


@router.post("/bookings/{booking_id}/cancel")
def cancel_booking(booking_id: int):
    return booking_service.cancel_booking(booking_id)


@router.get("/reports/summary")
def reports_summary():
    return report_service.reports_summary()
