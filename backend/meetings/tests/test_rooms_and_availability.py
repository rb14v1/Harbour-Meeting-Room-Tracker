from django.core.management import call_command
from rest_framework.test import APITestCase

from meetings.models import Booking, Employee, Room
from meetings.tests.helpers import FUTURE, booking_payload, make_room

ROOM = {
    "room_name": "Test Room",
    "location": "Floor 9",
    "capacity": 6,
    "facilities": ["Projector", "Wi-Fi"],
    "status": "Active",
}


class RoomTests(APITestCase):
    def test_seed_creates_at_least_five_rooms_and_is_idempotent(self):
        call_command("seed", verbosity=0)
        first = Room.objects.count()
        self.assertGreaterEqual(first, 5)
        call_command("seed", verbosity=0)
        call_command("seed", verbosity=0)
        self.assertEqual(Room.objects.count(), first)
        self.assertEqual(Employee.objects.filter(email="priya.sharma@example.com").count(), 1)

    def test_create_and_update_room(self):
        r = self.client.post("/api/rooms", ROOM, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()["facilities"], ["Projector", "Wi-Fi"])
        rid = r.json()["room_id"]
        updated = self.client.put(f"/api/rooms/{rid}", {**ROOM, "capacity": 10}, format="json")
        self.assertEqual(updated.json()["capacity"], 10)

    def test_duplicate_room_name_is_conflict(self):
        make_room("Boardroom")
        r = self.client.post("/api/rooms", {**ROOM, "room_name": "boardroom"}, format="json")
        self.assertEqual(r.status_code, 409)

    def test_delete_room_without_history(self):
        rid = self.client.post("/api/rooms", ROOM, format="json").json()["room_id"]
        self.assertTrue(self.client.delete(f"/api/rooms/{rid}").json()["deleted"])

    def test_room_with_history_is_deactivated_not_deleted(self):
        room = make_room("Boardroom")
        self.client.post("/api/bookings", booking_payload(room, "09:00", "10:00", email="hist@example.com"),
                         format="json")
        body = self.client.delete(f"/api/rooms/{room.pk}").json()
        self.assertTrue(body["deactivated"])
        room.refresh_from_db()
        self.assertEqual(room.status, Room.Status.INACTIVE)

    def test_missing_room_returns_404(self):
        self.assertEqual(self.client.get("/api/rooms/999999").status_code, 404)


class AvailabilityTests(APITestCase):
    def setUp(self):
        self.a = make_room("Conference Room A", capacity=12, facilities="Projector, Wi-Fi")
        self.b = make_room("Conference Room B", capacity=8, facilities="TV Screen, Wi-Fi")
        self.huddle = make_room("Huddle Room 1", capacity=4, facilities="TV Screen")
        self.client.post("/api/bookings", booking_payload(self.a, "10:00", "11:00", email="slot@example.com"),
                         format="json")

    def check(self, **params):
        base = {"date": FUTURE.isoformat(), "start": "10:00", "end": "11:00"}
        base.update(params)
        r = self.client.get("/api/availability", base)
        self.assertEqual(r.status_code, 200, r.content)
        return r.json()

    def test_availability_reflects_requested_interval(self):
        rooms = {r["room_name"]: r for r in self.check()}
        self.assertEqual(rooms["Conference Room A"]["state"], "Occupied")
        self.assertTrue(rooms["Conference Room B"]["available"])
        later = {r["room_name"]: r for r in self.check(start="11:00", end="12:00")}
        self.assertTrue(later["Conference Room A"]["available"])

    def test_filters_by_capacity_name_and_facilities(self):
        self.assertTrue(all(r["capacity"] >= 10 for r in self.check(capacity=10)))
        self.assertTrue(all("huddle" in r["room_name"].lower() for r in self.check(search="huddle")))
        rows = self.check(facilities=["Projector"])
        self.assertTrue(rows and all("projector" in [f.lower() for f in r["facilities"]] for r in rows))

    def test_inactive_room_shows_inactive_state(self):
        self.huddle.status = Room.Status.INACTIVE
        self.huddle.save()
        rows = {r["room_name"]: r for r in self.check()}
        self.assertEqual(rows["Huddle Room 1"]["state"], "Inactive")

    def test_missing_parameters_return_422(self):
        r = self.client.get("/api/availability", {"date": FUTURE.isoformat()})
        self.assertEqual(r.status_code, 422)

    def test_dashboard_and_reports_respond(self):
        dash = self.client.get("/api/dashboard").json()
        self.assertGreaterEqual(dash["total_rooms"], 3)
        self.assertIn("room_overview", dash)
        rep = self.client.get("/api/reports/summary").json()
        self.assertEqual(len(rep["daily"]), 7)
        self.assertEqual(len(rep["weekly"]), 4)
        self.assertTrue(rep["utilisation"])
        self.assertIsNotNone(rep["most_booked_room"])

    def test_health_endpoint(self):
        self.assertEqual(self.client.get("/api/health").json(), {"status": "ok"})
