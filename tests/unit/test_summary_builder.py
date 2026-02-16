from datetime import datetime
from app.models.normalized_models import TaskSnapshot, ActivityEvent, SummaryMeta
from app.services.composition.summary_builder import build_summary


def test_summary_builder_basic():
    snapshot = TaskSnapshot(
        name="Build summarization",
        status="In Progress",
        assignees=["softy"],
        priority=None,
        start_date=datetime(2026, 2, 10),
        due_date=datetime(2026, 2, 20),
        tags=[],
        description=None,
        estimation=None,
    )

    events = [
        ActivityEvent(
            type="status_change",
            actor="softy",
            at=datetime(2026, 2, 16),
            text="Status changed from To Do to In Progress",
            field="status",
            old="To Do",
            new="In Progress",
        )
    ]

    meta = SummaryMeta(events_count=1, comments_count=0, last_activity_at=datetime(2026, 2, 16))

    summary = build_summary(snapshot, events, meta)

    assert "Build summarization" in summary
    assert "Status changed" in summary
    assert "No comments were added." in summary
