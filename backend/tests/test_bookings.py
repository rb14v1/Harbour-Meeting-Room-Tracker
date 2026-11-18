import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.schemas import BookingIn
from app.services.bookings import create_booking

FUTURE = (date.today() + timedelta(days=7)).isoformat()


def _room_id(client, name):
    return next(r["room_id"] for r in client.get("/api/rooms").json() if r["room_name"] == name)


def _payload(room_id, start, end, email="tester@example.com", title="Test meeting", day=FUTURE):
    return {
        "room_id": room_id,
        "employee_name": "Test User",
        "employee_email": email,
        "department": "QA",
        "meeting_title": title,
        "booking_date": day,
        "start_time": start,
        "end_time": end,
    }


def test_overlapping_booking_is_rejected(client):
    rid = _room_id(client, "Conference Room A")
    assert client.post("/api/bookings", json=_payload(rid, "10:00", "11:00")).status_code == 201
    r = client.post("/api/bookings", json=_payload(rid, "10:30", "11:30", email="other@example.com"))
    assert r.status_code == 409
    assert "10:00-11:00" in r.json()["detail"]


def test_back_to_back_booking_is_allowed(client):
    rid = _room_id(client, "Conference Room A")
    assert client.post("/api/bookings", json=_payload(rid, "10:00", "11:00")).status_code == 201
    assert client.post("/api/bookings", json=_payload(rid, "11:00", "12:00", email="b@example.com")).status_code == 201


def test_end_time_must_be_after_start(client):
    rid = _room_id(client, "Huddle Room 1")
    r = client.post("/api/bookings", json=_payload(rid, "12:00", "12:00"))
    assert r.status_code == 422


def test_past_date_is_rejected(client):
    rid = _room_id(client, "Huddle Room 1")
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    r = client.post("/api/bookings", json=_payload(rid, "09:00", "10:00", day=yesterday))
    assert r.status_code == 422


def test_invalid_date_is_rejected(client):
    rid = _room_id(client, "Huddle Room 1")
    r = client.post("/api/bookings", json=_payload(rid, "09:00", "10:00", day="2026-02-30"))
    assert r.status_code == 422


def test_inactive_room_cannot_be_booked(client):
    rid = _room_id(client, "Huddle Room 2")
    room = client.get(f"/api/rooms/{rid}").json()
    room["status"] = "Inactive"
    room["facilities"] = room["facilities"]
    client.put(f"/api/rooms/{rid}", json=room)
    r = client.post("/api/bookings", json=_payload(rid, "09:00", "10:00"))
    assert r.status_code == 409


def test_cancelled_booking_does_not_block(client):
    rid = _room_id(client, "Boardroom")
    bid = client.post("/api/bookings", json=_payload(rid, "13:00", "14:00")).json()["booking_id"]
    assert client.post(f"/api/bookings/{bid}/cancel").status_code == 200
    r = client.post("/api/bookings", json=_payload(rid, "13:00", "14:00", email="next@example.com"))
    assert r.status_code == 201


def test_cancel_twice_is_rejected(client):
    rid = _room_id(client, "Boardroom")
    bid = client.post("/api/bookings", json=_payload(rid, "15:00", "16:00")).json()["booking_id"]
    client.post(f"/api/bookings/{bid}/cancel")
    assert client.post(f"/api/bookings/{bid}/cancel").status_code == 409


def test_concurrent_bookings_for_same_slot_only_one_succeeds():
    from app.services import rooms as room_service
    rid = next(r["room_id"] for r in room_service.list_rooms() if r["room_name"] == "Innovation Lab")
    barrier = threading.Barrier(8)

    def attempt(i):
        barrier.wait()
        try:
            create_booking(BookingIn(
                room_id=rid, employee_name=f"Racer {'ABCDEFGH'[i]}", employee_email=f"racer{i}@example.com",
                meeting_title="Race condition test", booking_date=FUTURE,
                start_time="09:00", end_time="10:00"))
            return "ok"
        except HTTPException as exc:
            return exc.status_code

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(attempt, range(8)))
    assert results.count("ok") == 1
    assert results.count(409) == 7


@pytest.mark.parametrize("bad_name", [
    "John3", "Priya_S", "Mary-Anne", "O'Brien", "J.Smith", "Ravi@Kumar", "Sophie!", "<script>", "Amy  #1",
])
def test_name_with_special_characters_or_digits_is_rejected(client, bad_name):
    rid = _room_id(client, "Huddle Room 2")
    payload = _payload(rid, "09:00", "10:00")
    payload["employee_name"] = bad_name
    r = client.post("/api/bookings", json=payload)
    assert r.status_code == 422
    assert any(e["field"] == "employee_name" for e in r.json()["detail"])


@pytest.mark.parametrize("bad_name", ["José Müller", "Zoë Ångström", "Łukasz Nowak"])
def test_accented_names_are_rejected(client, bad_name):
    rid = _room_id(client, "Huddle Room 2")
    payload = _payload(rid, "09:00", "10:00")
    payload["employee_name"] = bad_name
    assert client.post("/api/bookings", json=payload).status_code == 422


def test_name_with_letters_and_spaces_is_accepted_and_normalised(client):
    rid = _room_id(client, "Huddle Room 2")
    payload = _payload(rid, "09:00", "10:00")
    payload["employee_name"] = "  Priya   Sharma  "
    r = client.post("/api/bookings", json=payload)
    assert r.status_code == 201
    assert r.json()["employee_name"] == "Priya Sharma"


def _create(client, room_name, start, end, email="edit@example.com", title="Original"):
    rid = _room_id(client, room_name)
    r = client.post("/api/bookings", json=_payload(rid, start, end, email=email, title=title))
    assert r.status_code == 201, r.text
    return r.json()


def test_edit_booking_changes_fields(client):
    b = _create(client, "Boardroom", "09:00", "10:00")
    payload = _payload(_room_id(client, "Huddle Room 1"), "14:00", "15:00", email="edit@example.com",
                       title="Moved meeting")
    r = client.put(f"/api/bookings/{b['booking_id']}", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["room_name"] == "Huddle Room 1"
    assert (body["start_time"], body["end_time"], body["meeting_title"]) == ("14:00", "15:00", "Moved meeting")
    assert body["booking_id"] == b["booking_id"]


def test_edit_can_keep_same_slot_without_clashing_with_itself(client):
    b = _create(client, "Boardroom", "09:00", "10:00")
    payload = _payload(_room_id(client, "Boardroom"), "09:00", "10:00", email="edit@example.com",
                       title="Renamed only")
    r = client.put(f"/api/bookings/{b['booking_id']}", json=payload)
    assert r.status_code == 200 and r.json()["meeting_title"] == "Renamed only"


def test_edit_into_another_booking_slot_is_rejected(client):
    _create(client, "Boardroom", "10:00", "11:00", email="one@example.com")
    b = _create(client, "Boardroom", "13:00", "14:00", email="two@example.com")
    payload = _payload(_room_id(client, "Boardroom"), "10:30", "11:30", email="two@example.com")
    r = client.put(f"/api/bookings/{b['booking_id']}", json=payload)
    assert r.status_code == 409


def test_edit_rejects_invalid_times_and_past_dates(client):
    b = _create(client, "Boardroom", "09:00", "10:00")
    bid = b["booking_id"]
    bad_times = _payload(_room_id(client, "Boardroom"), "12:00", "11:00", email="edit@example.com")
    assert client.put(f"/api/bookings/{bid}", json=bad_times).status_code == 422
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    past = _payload(_room_id(client, "Boardroom"), "09:00", "10:00", email="edit@example.com", day=yesterday)
    assert client.put(f"/api/bookings/{bid}", json=past).status_code == 422


def test_edit_rejects_invalid_name(client):
    b = _create(client, "Boardroom", "09:00", "10:00")
    payload = _payload(_room_id(client, "Boardroom"), "09:00", "10:00", email="edit@example.com")
    payload["employee_name"] = "Priya_S"
    assert client.put(f"/api/bookings/{b['booking_id']}", json=payload).status_code == 422


def test_edit_cancelled_booking_is_rejected(client):
    b = _create(client, "Boardroom", "09:00", "10:00")
    client.post(f"/api/bookings/{b['booking_id']}/cancel")
    payload = _payload(_room_id(client, "Boardroom"), "11:00", "12:00", email="edit@example.com")
    assert client.put(f"/api/bookings/{b['booking_id']}", json=payload).status_code == 409


def test_edit_missing_booking_returns_404(client):
    payload = _payload(_room_id(client, "Boardroom"), "09:00", "10:00")
    assert client.put("/api/bookings/999999", json=payload).status_code == 404


def test_edit_into_inactive_room_is_rejected(client):
    b = _create(client, "Boardroom", "09:00", "10:00")
    rid = _room_id(client, "Huddle Room 2")
    room = client.get(f"/api/rooms/{rid}").json()
    client.put(f"/api/rooms/{rid}", json={**room, "status": "Inactive"})
    payload = _payload(rid, "09:00", "10:00", email="edit@example.com")
    assert client.put(f"/api/bookings/{b['booking_id']}", json=payload).status_code == 409


def test_flags_show_what_can_be_edited(client):
    b = _create(client, "Boardroom", "09:00", "10:00")
    assert b["can_edit"] is True and b["can_cancel"] is True and b["is_past"] is False
    client.post(f"/api/bookings/{b['booking_id']}/cancel")
    cancelled = client.get(f"/api/bookings/{b['booking_id']}").json()
    assert cancelled["can_edit"] is False and cancelled["status"] == "Cancelled"


def test_list_views_and_search(client):
    rid = _room_id(client, "Huddle Room 1")
    client.post("/api/bookings", json=_payload(rid, "09:00", "09:30"))
    upcoming = client.get("/api/bookings", params={"view": "upcoming", "search": "Priya"}).json()
    assert all("Priya" in b["employee_name"] for b in upcoming)
    by_date = client.get("/api/bookings", params={"date": FUTURE, "room_id": rid}).json()
    assert by_date and all(b["booking_date"] == FUTURE and b["room_id"] == rid for b in by_date)
