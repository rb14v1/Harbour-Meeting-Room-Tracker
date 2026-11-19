from datetime import date, time, timedelta

from django.db import IntegrityError, transaction
from rest_framework.test import APITestCase

from meetings.models import Booking, Employee
from meetings.tests.helpers import FUTURE, booking_payload, make_room


class BookingRuleTests(APITestCase):
    def setUp(self):
        self.room = make_room("Conference Room A", capacity=12)
        self.huddle = make_room("Huddle Room 2", capacity=4, facilities="Wi-Fi, Whiteboard")

    def post(self, payload):
        return self.client.post("/api/bookings", payload, format="json")

    def create(self, room, start, end, **kwargs):
        r = self.post(booking_payload(room, start, end, **kwargs))
        self.assertEqual(r.status_code, 201, r.content)
        return r.json()

    def test_overlapping_booking_is_rejected(self):
        self.create(self.room, "10:00", "11:00")
        r = self.post(booking_payload(self.room, "10:30", "11:30", email="other@example.com"))
        self.assertEqual(r.status_code, 409)
        self.assertIn("10:00-11:00", r.json()["detail"])

    def test_back_to_back_booking_is_allowed(self):
        self.create(self.room, "10:00", "11:00")
        self.create(self.room, "11:00", "12:00", email="b@example.com")

    def test_end_time_must_be_after_start(self):
        r = self.post(booking_payload(self.room, "12:00", "12:00"))
        self.assertEqual(r.status_code, 422)
        self.assertTrue(any(e["field"] == "end_time" for e in r.json()["detail"]))

    def test_past_date_is_rejected(self):
        yesterday = date.today() - timedelta(days=1)
        r = self.post(booking_payload(self.room, "09:00", "10:00", day=yesterday))
        self.assertEqual(r.status_code, 422)

    def test_invalid_date_is_rejected(self):
        payload = booking_payload(self.room, "09:00", "10:00")
        payload["booking_date"] = "2026-02-30"
        self.assertEqual(self.post(payload).status_code, 422)

    def test_inactive_room_cannot_be_booked(self):
        self.huddle.status = self.huddle.Status.INACTIVE
        self.huddle.save()
        self.assertEqual(self.post(booking_payload(self.huddle, "09:00", "10:00")).status_code, 409)

    def test_cancelled_booking_does_not_block(self):
        b = self.create(self.room, "13:00", "14:00")
        self.assertEqual(self.client.post(f"/api/bookings/{b['booking_id']}/cancel").status_code, 200)
        self.create(self.room, "13:00", "14:00", email="next@example.com")

    def test_cancel_twice_is_rejected(self):
        b = self.create(self.room, "15:00", "16:00")
        self.client.post(f"/api/bookings/{b['booking_id']}/cancel")
        self.assertEqual(self.client.post(f"/api/bookings/{b['booking_id']}/cancel").status_code, 409)

    def test_database_constraint_blocks_overlap_even_without_service_check(self):
        room = self.room
        employee = Employee.objects.create(employee_name="Direct Insert", email="direct@example.com")
        Booking.objects.create(room=room, employee=employee, meeting_title="First",
                               booking_date=FUTURE, start_time=time(9), end_time=time(10))
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Booking.objects.create(room=room, employee=employee, meeting_title="Clash",
                                       booking_date=FUTURE, start_time=time(9, 30), end_time=time(10, 30))

    def test_names_with_digits_symbols_or_accents_are_rejected(self):
        bad_names = ["John3", "Priya_S", "Mary-Anne", "O'Brien", "J.Smith", "Ravi@Kumar",
                     "Sophie!", "<script>", "Amy  #1", "José Müller", "Zoë Ångström", "Łukasz Nowak"]
        for bad in bad_names:
            with self.subTest(name=bad):
                r = self.post(booking_payload(self.huddle, "09:00", "10:00", name=bad))
                self.assertEqual(r.status_code, 422)
                self.assertTrue(any(e["field"] == "employee_name" for e in r.json()["detail"]))

    def test_valid_name_is_accepted_and_normalised(self):
        r = self.post(booking_payload(self.huddle, "09:00", "10:00", name="  Priya   Sharma  "))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["employee_name"], "Priya Sharma")

    def test_list_views_and_search(self):
        self.create(self.huddle, "09:00", "09:30", name="Priya Sharma")
        upcoming = self.client.get("/api/bookings", {"view": "upcoming", "search": "Priya"}).json()
        self.assertTrue(upcoming)
        self.assertTrue(all("Priya" in b["employee_name"] for b in upcoming))
        by_date = self.client.get("/api/bookings", {"date": FUTURE.isoformat(), "room_id": self.huddle.pk}).json()
        self.assertTrue(by_date)
        self.assertTrue(all(b["booking_date"] == FUTURE.isoformat() for b in by_date))

    def test_flags_show_what_can_be_edited(self):
        b = self.create(self.room, "09:00", "10:00")
        self.assertTrue(b["can_edit"] and b["can_cancel"])
        self.assertFalse(b["is_past"])
        self.client.post(f"/api/bookings/{b['booking_id']}/cancel")
        cancelled = self.client.get(f"/api/bookings/{b['booking_id']}").json()
        self.assertFalse(cancelled["can_edit"])
        self.assertEqual(cancelled["status"], "Cancelled")


class BookingEditTests(APITestCase):
    def setUp(self):
        self.boardroom = make_room("Boardroom", capacity=16)
        self.huddle = make_room("Huddle Room 1", capacity=4)
        self.booking = self.client.post(
            "/api/bookings", booking_payload(self.boardroom, "09:00", "10:00", email="edit@example.com"),
            format="json").json()
        self.url = f"/api/bookings/{self.booking['booking_id']}"

    def put(self, payload):
        return self.client.put(self.url, payload, format="json")

    def test_edit_changes_fields(self):
        r = self.put(booking_payload(self.huddle, "14:00", "15:00", email="edit@example.com",
                                     title="Moved meeting"))
        self.assertEqual(r.status_code, 200, r.content)
        body = r.json()
        self.assertEqual(body["room_name"], "Huddle Room 1")
        self.assertEqual((body["start_time"], body["end_time"], body["meeting_title"]),
                         ("14:00", "15:00", "Moved meeting"))
        self.assertEqual(body["booking_id"], self.booking["booking_id"])

    def test_edit_can_keep_same_slot_without_clashing_with_itself(self):
        r = self.put(booking_payload(self.boardroom, "09:00", "10:00", email="edit@example.com",
                                     title="Renamed only"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["meeting_title"], "Renamed only")

    def test_edit_into_another_booking_slot_is_rejected(self):
        self.client.post("/api/bookings", booking_payload(self.boardroom, "10:00", "11:00",
                                                          email="one@example.com"), format="json")
        other = self.client.post("/api/bookings", booking_payload(self.boardroom, "13:00", "14:00",
                                                                  email="two@example.com"), format="json").json()
        r = self.client.put(f"/api/bookings/{other['booking_id']}",
                            booking_payload(self.boardroom, "10:30", "11:30", email="two@example.com"),
                            format="json")
        self.assertEqual(r.status_code, 409)

    def test_edit_rejects_invalid_times_and_past_dates(self):
        self.assertEqual(self.put(booking_payload(self.boardroom, "12:00", "11:00",
                                                  email="edit@example.com")).status_code, 422)
        yesterday = date.today() - timedelta(days=1)
        self.assertEqual(self.put(booking_payload(self.boardroom, "09:00", "10:00",
                                                  email="edit@example.com", day=yesterday)).status_code, 422)

    def test_edit_rejects_invalid_name(self):
        payload = booking_payload(self.boardroom, "09:00", "10:00", email="edit@example.com", name="Priya_S")
        self.assertEqual(self.put(payload).status_code, 422)

    def test_edit_cancelled_booking_is_rejected(self):
        self.client.post(f"{self.url}/cancel")
        self.assertEqual(self.put(booking_payload(self.boardroom, "11:00", "12:00",
                                                  email="edit@example.com")).status_code, 409)

    def test_edit_missing_booking_returns_404(self):
        r = self.client.put("/api/bookings/999999", booking_payload(self.boardroom, "09:00", "10:00"),
                            format="json")
        self.assertEqual(r.status_code, 404)

    def test_edit_into_inactive_room_is_rejected(self):
        self.huddle.status = self.huddle.Status.INACTIVE
        self.huddle.save()
        self.assertEqual(self.put(booking_payload(self.huddle, "09:00", "10:00",
                                                  email="edit@example.com")).status_code, 409)
