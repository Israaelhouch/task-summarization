from datetime import datetime
from app.models.request_models import TaskSummarizeRequest
from app.models.normalized_models import TaskSnapshot, ActivityEvent, SummaryResponse


def test_request_model_accepts_task_and_activity():
    payload = {
        "task": {"name": "My Task", "status": "To Do", "random_field": 123},
        "activity": [{"type": "update", "timestamp": "2026-02-16T10:00:00Z"}],
        "extra_top_level": True,
    }

    req = TaskSummarizeRequest(**payload)
    assert req.task["name"] == "My Task"
    assert isinstance(req.activity, list)
    assert req.task["random_field"] == 123  # allowed


def test_task_snapshot_defaults():
    snap = TaskSnapshot(name="X")
    assert snap.assignees == []
    assert snap.tags == []
    assert snap.status is None


def test_activity_event_requires_text():
    ev = ActivityEvent(type="comment", text="Hello", actor="Alice")
    assert ev.type == "comment"
    assert ev.text == "Hello"


def test_summary_response_defaults_meta():
    res = SummaryResponse(summary="ok")
    assert res.meta.events_count == 0
    assert res.meta.comments_count == 0
