import os
import sys

# Ensure backend source is importable when running tests from repo root
CURRENT_DIR = os.path.dirname(__file__)
SRC_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from fastapi.testclient import TestClient  # type: ignore
from clarity_api.app import app


client = TestClient(app)


def test_health_ok() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "healthy"


def test_root_message() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "message" in data


def test_clear_endpoint_ok() -> None:
    resp = client.post("/clear", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True
    # Paths included for visibility
    assert "cleared_db_path" in data
    assert "cleared_tree_path" in data


def test_tree_available_or_missing() -> None:
    # The tree file may or may not exist depending on local setup.
    # Either 200 with a valid payload, or 404 when missing.
    resp = client.get("/tree")
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        data = resp.json()
        assert "nodes" in data
        assert "root_ids" in data

