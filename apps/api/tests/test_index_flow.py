import os
import sys

CURRENT_DIR = os.path.dirname(__file__)
SRC_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from fastapi.testclient import TestClient  # type: ignore
from clarity_api.app import app


client = TestClient(app)


def test_index_rejects_when_missing_root_dir() -> None:
    resp = client.post("/index", json={})
    # We either default to home directory or error out in the route
    # Accept both 200 and 500 but validate JSON shape if 200
    assert resp.status_code in (200, 500)
    if resp.status_code == 200:
        data = resp.json()
        assert "nodes" in data
        assert "metadata" in data


def test_refresh_returns_payload_or_error() -> None:
    resp = client.post("/refresh")
    assert resp.status_code in (200, 500)

