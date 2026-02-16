from app.services.extraction.activity_extractor import extract_activity_events


def test_extract_activity_status_change():
    activity = [
        {"field": "status", "old": "To Do", "new": "In Progress", "actor": {"username": "softy"}, "timestamp": "2026-02-16T10:00:00Z"}
    ]
    events, meta = extract_activity_events(activity)
    assert len(events) == 1
    assert events[0].type == "status_change"
    assert "Status changed" in events[0].text
    assert meta.events_count == 1


def test_extract_activity_tags_change():
    activity = [
        {
            "changes": {
                "tags": {"from": ["backend"], "to": ["backend", "ai"]}
            },
            "actor": "alice",
            "timestamp": "2026-02-16T09:00:00Z"
        }
    ]
    events, meta = extract_activity_events(activity)
    assert any(e.type == "tag_added" for e in events)
    assert meta.events_count == len(events)


def test_extract_activity_comment():
    activity = [
        {"comment": "Please fix the edge cases in status parsing.", "actor": "bob", "timestamp": "2026-02-16T11:00:00Z"}
    ]
    events, meta = extract_activity_events(activity)
    assert len(events) == 1
    assert events[0].type == "comment"
    assert meta.comments_count == 1
