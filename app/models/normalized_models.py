from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal, Union
from pydantic import BaseModel, Field


class TaskSnapshot(BaseModel):
    """
    Strict, internal normalized task snapshot.
    Only keep fields that are allowed to appear in summaries.
    """
    name: str
    status: Optional[str] = None
    assignees: List[str] = Field(default_factory=list)
    priority: Optional[Union[str, int]] = None

    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None

    tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    estimation: Optional[Union[str, int, float]] = None


EventType = Literal[
    "status_change",
    "tag_added",
    "tag_removed",
    "date_change",
    "assignee_change",
    "comment",
    "other",
]


class ActivityEvent(BaseModel):
    """
    Strict, internal normalized event.
    `text` must already be human-readable and safe (no IDs, no URLs).
    """
    type: EventType
    actor: Optional[str] = None
    at: Optional[datetime] = None
    text: str

    # Optional structured fields for smarter grouping later
    field: Optional[str] = None
    old: Optional[str] = None
    new: Optional[str] = None


class SummaryMeta(BaseModel):
    events_count: int = 0
    comments_count: int = 0
    last_activity_at: Optional[datetime] = None


class SummaryResponse(BaseModel):
    summary: str
    meta: SummaryMeta = Field(default_factory=SummaryMeta)
