from __future__ import annotations

from app.models.request_models import TaskSummarizeRequest
from app.models.response_models import TaskSummarizeResponse

from app.services.extraction.snapshot_extractor import extract_task_snapshot
from app.services.extraction.activity_extractor import extract_activity_events
from app.services.composition.summary_builder import build_summary


class SummarizationService:
    def summarize(self, req: TaskSummarizeRequest, include_events: bool = False) -> TaskSummarizeResponse:
        snapshot = extract_task_snapshot(req.task)
        events, meta = extract_activity_events(req.activity)

        summary = build_summary(snapshot=snapshot, events=events, meta=meta)

        return TaskSummarizeResponse(
            summary=summary,
            meta=meta,
            events=events if include_events else None,
        )
