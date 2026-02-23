from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.models.normalized_models import ActivityEvent, SummaryMeta


class TaskSummarizeResponse(BaseModel):
    summary: str
    meta: SummaryMeta
    events: Optional[List[ActivityEvent]] = None  # useful for debugging; can be disabled later
