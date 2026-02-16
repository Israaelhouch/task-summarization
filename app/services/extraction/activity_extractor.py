from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.models.normalized_models import ActivityEvent, SummaryMeta
from app.services.extraction.event_classifier import classify_activity_item


def extract_activity_events(activity: List[Dict[str, Any]]) -> Tuple[List[ActivityEvent], SummaryMeta]:
    """
    Turns raw activity[] into a normalized list of ActivityEvent + meta.
    """
    if not isinstance(activity, list):
        activity = []

    # classify and collect
    events: List[ActivityEvent] = []
    for item in activity:
        if isinstance(item, dict):
            events.extend(classify_activity_item(item))

    # sort by timestamp (None last)
    events.sort(key=lambda e: (e.at is None, e.at))

    meta = SummaryMeta(
        events_count=len(events),
        comments_count=sum(1 for e in events if e.type == "comment"),
        last_activity_at=events[-1].at if events else None,
    )
    return events, meta
