from datetime import date, timedelta

FUTURE = (date.today() + timedelta(days=7)).isoformat()

ROOM = {
    "room_name": "Test Room",
    "location": "Floor 9",
    "capacity": 6,
    "facilities": ["Projector", "Wi-Fi"],
    "status": "Active",
}


def test_seed_creates_at_least_five_rooms(client):
    assert len(client.get("/api/rooms").json()) >= 5


def test_seed_is_idempotent(client):
    from app.db.seed import seed_database
    before = len(client.get("/api/rooms").json())
    seed_database()
    seed_database()
    assert len(client.get("/api/rooms").json()) == before


def test_create_and_update_room(client):
    created = client.post("/api/rooms", json=ROOM)
    assert created.status_code == 201
    rid = created.json()["room_id"]
    assert created.json()["facilities"] == ["Projector", "Wi-Fi"]
    updated = {**ROOM, "capacity": 10}
    assert client.put(f"/api/rooms/{rid}", json=updated).json()["capacity"] == 10


def test_duplicate_room_name_rejected(client):
    assert client.post("/api/rooms", json={**ROOM, "room_name": "Boardroom"}).status_code == 409


def test_delete_room_without_history(client):
    rid = client.post("/api/rooms", json=ROOM).json()["room_id"]
    body = client.delete(f"/api/rooms/{rid}").json()
    assert body["deleted"] is True


def test_room_with_history_is_deactivated_not_deleted(client):
    rid = next(r["room_id"] for r in client.get("/api/rooms").json() if r["room_name"] == "Boardroom")
    client.post("/api/bookings", json={
        "room_id": rid, "employee_name": "Hist Owner", "employee_email": "hist@example.com",
        "meeting_title": "History", "booking_date": FUTURE, "start_time": "09:00", "end_time": "10:00"})
    body = client.delete(f"/api/rooms/{rid}").json()
    assert body["deactivated"] is True
    assert client.get(f"/api/rooms/{rid}").json()["status"] == "Inactive"


def test_availability_reflects_requested_interval(client):
    params = {"date": FUTURE, "start": "10:00", "end": "11:00"}
    rid = next(r["room_id"] for r in client.get("/api/rooms").json() if r["room_name"] == "Conference Room A")
    client.post("/api/bookings", json={
        "room_id": rid, "employee_name": "Slot Holder", "employee_email": "slot@example.com",
        "meeting_title": "Slot", "booking_date": FUTURE, "start_time": "10:00", "end_time": "11:00"})

    rooms = {r["room_name"]: r for r in client.get("/api/availability", params=params).json()}
    assert rooms["Conference Room A"]["state"] == "Occupied"
    assert rooms["Conference Room B"]["available"] is True

    later = client.get("/api/availability", params={"date": FUTURE, "start": "11:00", "end": "12:00"}).json()
    assert {r["room_name"]: r for r in later}["Conference Room A"]["available"] is True


def test_availability_filters(client):
    rooms = client.get("/api/availability", params={
        "date": FUTURE, "start": "09:00", "end": "10:00", "capacity": 10}).json()
    assert rooms and all(r["capacity"] >= 10 for r in rooms)

    by_name = client.get("/api/availability", params={
        "date": FUTURE, "start": "09:00", "end": "10:00", "search": "huddle"}).json()
    assert by_name and all("huddle" in r["room_name"].lower() for r in by_name)

    by_facility = client.get("/api/availability", params=[
        ("date", FUTURE), ("start", "09:00"), ("end", "10:00"), ("facilities", "Projector")]).json()
    assert by_facility and all("projector" in [f.lower() for f in r["facilities"]] for r in by_facility)


def test_inactive_room_shows_inactive_state(client):
    rid = client.post("/api/rooms", json={**ROOM, "status": "Inactive"}).json()["room_id"]
    rows = client.get("/api/availability", params={"date": FUTURE, "start": "09:00", "end": "10:00"}).json()
    assert next(r for r in rows if r["room_id"] == rid)["state"] == "Inactive"


def test_reports_and_dashboard_respond(client):
    dash = client.get("/api/dashboard").json()
    assert dash["total_rooms"] >= 5 and "room_overview" in dash
    rep = client.get("/api/reports/summary").json()
    assert len(rep["daily"]) == 7 and len(rep["weekly"]) == 4
    assert rep["utilisation"] and rep["employees"] is not None
