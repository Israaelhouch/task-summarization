from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_post_summarize_route():
    payload = {
        "task": {
            "name": "Task Summarization",
            "status": "In Progress",
            "assignees": [{"username": "softy"}],
            "startDate": "2026-02-10T00:00:00Z",
            "dueDate": "2026-02-20T00:00:00Z",
            "tags": [{"name": "backend"}],
            "description": "Implement summarization endpoint."
        },
        "activity": [
            {"field": "status", "old": "To Do", "new": "In Progress", "actor": "softy", "timestamp": "2026-02-16T10:00:00Z"},
            {"comment": "Handle tag removals too.", "actor": "alice", "timestamp": "2026-02-16T12:00:00Z"},
        ],
    }

    r = client.post("/api/v1/summarize", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data
    assert "meta" in data
    assert "Task Summarization" in data["summary"]
