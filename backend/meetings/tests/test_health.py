from unittest.mock import patch

from django.db import OperationalError
from django.test import SimpleTestCase


class ProbeTests(SimpleTestCase):
    def test_healthz_ignores_allowed_hosts(self):
        resp = self.client.get("/healthz", HTTP_HOST="10.0.0.5:8080")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"ok")

    def test_readyz_ok_when_database_reachable(self):
        with patch("config.health.connection"):
            resp = self.client.get("/readyz", HTTP_HOST="10.0.0.5")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})

    def test_readyz_503_when_database_down(self):
        with patch("config.health.connection") as conn:
            conn.cursor.side_effect = OperationalError("down")
            resp = self.client.get("/readyz", HTTP_HOST="10.0.0.5")
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.json(), {"status": "unavailable"})
