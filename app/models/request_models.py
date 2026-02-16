from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TaskSummarizeRequest(BaseModel):
    """
    Incoming API payload.
    Keep it permissive: upstream systems may send extra fields we must ignore.
    """
    task: Dict[str, Any] = Field(..., description="Task snapshot (current state).")
    activity: List[Dict[str, Any]] = Field(default_factory=list, description="Chronological task activity log.")

    model_config = ConfigDict(extra="allow")

