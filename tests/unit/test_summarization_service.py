from app.services.summarization_service import SummarizationService
from app.models.request_models import TaskSummarizeRequest


def test_summarization_service_end_to_end():
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
            {"changes": {"tags": {"from": ["backend"], "to": ["backend", "ai"]}}, "actor": "softy", "timestamp": "2026-02-16T11:00:00Z"},
            {"comment": "Please handle tag removals too.", "actor": "alice", "timestamp": "2026-02-16T12:00:00Z"},
        ],
    }

    req = TaskSummarizeRequest(**payload)
    svc = SummarizationService()
    res = svc.summarize(req)

    assert isinstance(res.summary, str)
    assert "Task Summarization" in res.summary
    assert res.meta.events_count >= 1
