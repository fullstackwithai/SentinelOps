import os
from pathlib import Path
os.environ["DATABASE_URL"] = "sqlite:///./test_sentinelops.db"
os.environ["OPENAI_API_KEY"] = ""
from fastapi.testclient import TestClient
from app.main import app, seed


def pytest_sessionstart(session):
    path = Path("test_sentinelops.db")
    if path.exists(): path.unlink()
    seed()


def pytest_sessionfinish(session, exitstatus):
    path = Path("test_sentinelops.db")
    if path.exists(): path.unlink()


client = TestClient(app)
