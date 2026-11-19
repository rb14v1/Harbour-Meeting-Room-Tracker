import threading
from datetime import time

from django.db import close_old_connections, connection
from django.test import TransactionTestCase

from meetings import services
from meetings.exceptions import Conflict
from meetings.tests.helpers import FUTURE, make_room


class ConcurrentBookingTests(TransactionTestCase):
    """Real threads on the real Postgres database: only one booking for a slot may succeed."""

    def test_concurrent_bookings_for_same_slot_only_one_succeeds(self):
        room = make_room("Innovation Lab", capacity=10)
        barrier = threading.Barrier(8)
        results = []
        lock = threading.Lock()

        def attempt(i):
            try:
                barrier.wait()
                services.create_booking({
                    "room_id": room.pk,
                    "employee_name": f"Racer {'ABCDEFGH'[i]}",
                    "employee_email": f"racer{i}@example.com",
                    "department": "QA",
                    "meeting_title": "Race condition test",
                    "booking_date": FUTURE,
                    "start_time": time(9, 0),
                    "end_time": time(10, 0),
                })
                outcome = "ok"
            except Conflict:
                outcome = 409
            except Exception as exc:  # surfaced in the assertion below
                outcome = repr(exc)
            finally:
                connection.close()
            with lock:
                results.append(outcome)

        threads = [threading.Thread(target=attempt, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        close_old_connections()

        self.assertEqual(results.count("ok"), 1, results)
        self.assertEqual(results.count(409), 7, results)
