import os
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="mrt_test_")) / "test.db"
os.environ["MRT_DB_PATH"] = str(_tmp)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import get_connection, init_database  # noqa: E402
from app.db.seed import seed_database  # noqa: E402
from app.main import app  # noqa: E402

init_database()


@pytest.fixture(autouse=True)
def fresh_db():
    conn = get_connection(_tmp)
    conn.executescript("DELETE FROM bookings; DELETE FROM employees; DELETE FROM rooms;")
    conn.close()
    seed_database()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
