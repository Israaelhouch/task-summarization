from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.normalized_models import TaskSnapshot
from app.utils.date_utils import parse_dt
from app.utils.text_utils import shorten_text


def _as_str(x: Any) -> Optional[str]:
    if x is None:
        return None
    s = str(x).strip()
    return s if s else None


def _extract_assignees(task: Dict[str, Any]) -> List[str]:
    raw = task.get("assignees") or task.get("assignee") or []
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return []

    out: List[str] = []
    for a in raw:
        if isinstance(a, str):
            v = _as_str(a)
            if v:
                out.append(v)
            continue
        if isinstance(a, dict):
            # common patterns
            for key in ("username", "handle", "displayName", "name", "email"):
                v = _as_str(a.get(key))
                if v:
                    out.append(v)
                    break
    # unique while preserving order
    seen = set()
    uniq = []
    for x in out:
        if x not in seen:
            uniq.append(x)
            seen.add(x)
    return uniq


def _extract_tags(task: Dict[str, Any]) -> List[str]:
    raw = task.get("tags") or []
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return []

    tags: List[str] = []
    for t in raw:
        if isinstance(t, str):
            v = _as_str(t)
            if v:
                tags.append(v)
        elif isinstance(t, dict):
            v = _as_str(t.get("name") or t.get("label") or t.get("title"))
            if v:
                tags.append(v)

    seen = set()
    uniq = []
    for x in tags:
        if x not in seen:
            uniq.append(x)
            seen.add(x)
    return uniq


def extract_task_snapshot(task: Dict[str, Any]) -> TaskSnapshot:
    name = _as_str(task.get("name") or task.get("title")) or "Untitled task"
    status = _as_str(task.get("status"))
    priority = task.get("priority")
    start_date = parse_dt(task.get("startDate") or task.get("start_date"))
    due_date = parse_dt(task.get("dueDate") or task.get("due_date"))

    description = _as_str(task.get("description") or task.get("shortDescription"))
    if description:
        description = shorten_text(description, max_len=180)

    estimation = task.get("estimation") or task.get("estimate") or task.get("timeEstimate")

    return TaskSnapshot(
        name=name,
        status=status,
        assignees=_extract_assignees(task),
        priority=priority,
        start_date=start_date,
        due_date=due_date,
        tags=_extract_tags(task),
        description=description,
        estimation=estimation,
    )
