# tests/test_health.py
from fastapi.testclient import TestClient
import os
os.environ.setdefault("LITELLM_MASTER_KEY", "test")
from travis.api.main import app

def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}