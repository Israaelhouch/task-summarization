from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.models.normalized_models import TaskSnapshot
from app.utils.date_utils import parse_dt
from app.utils.text_utils import shorten_text


def _as_str(x: Any) -> Optional[str]:
    if x is None:
        return None
    s = str(x).strip()
    return s if s else None


def _extract_status(task: Dict[str, Any]) -> Optional[str]:
    """
    Accepts:
      - "To Do"
      - {"id": "...", "name": "To Do", ...}
    Returns:
      - "To Do" or None
    """
    raw = task.get("status") or task.get("state")
    if raw is None:
        return None
    if isinstance(raw, str):
        return _as_str(raw)
    if isinstance(raw, dict):
        return _as_str(raw.get("name") or raw.get("label") or raw.get("title"))
    return _as_str(raw)


def _extract_priority(task: Dict[str, Any]) -> Optional[str]:
    """
    Accepts:
      - "High"
      - {"id": "...", "name": "High", ...}
    Returns:
      - "High" or None
    """
    raw = task.get("priority")
    if raw is None:
        return None
    if isinstance(raw, str):
        return _as_str(raw)
    if isinstance(raw, dict):
        return _as_str(raw.get("name") or raw.get("label") or raw.get("title"))
    return _as_str(raw)


def _extract_assignees(task: Dict[str, Any]) -> List[str]:
    """
    Your payload uses `users` as the assigned users list.
    We also support some other common keys as fallback.
    Accepts:
      - ["john", "sara"]
      - [{"fullName": "John Doe"}, {"email": "x@y.com"}]
      - {"fullName": "John Doe"} (single dict)
      - None
    Returns:
      - list[str] unique, stable order
    """
    raw = (
        task.get("users")
        or task.get("assignees")
        or task.get("assignedTo")
        or task.get("assigned_to")
        or task.get("assignee")
        or []
    )

    # handle comma-separated string IDs: "id1,id2"
    if isinstance(raw, str) and "," in raw:
        raw = [p.strip() for p in raw.split(",") if p.strip()]

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
            for key in ("username", "handle", "fullName", "displayName", "name", "email", "id"):
                v = _as_str(a.get(key))
                if v:
                    out.append(v)
                    break

    seen = set()
    uniq: List[str] = []
    for x in out:
        if x not in seen:
            uniq.append(x)
            seen.add(x)
    return uniq


def _lexical_to_text(s: str) -> str:
    """
    Lexical editor JSON is stored as a string.
    Extract all text nodes and join them.
    """
    try:
        obj = json.loads(s)
    except Exception:
        return s

    texts: List[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "text" and isinstance(node.get("text"), str):
                t = node["text"].strip()
                if t:
                    texts.append(t)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for it in node:
                walk(it)

    walk(obj)
    return " ".join(texts).strip() or s


def _extract_description(task: Dict[str, Any]) -> Optional[str]:
    raw = task.get("shortDescription") or task.get("description") or task.get("markdownDescription")
    txt = _as_str(raw)
    if not txt:
        return None

    # detect lexical JSON string
    if txt.startswith("{") and '"root"' in txt:
        txt = _lexical_to_text(txt)

    return shorten_text(txt, max_len=180)


def _extract_tags(task: Dict[str, Any]) -> List[str]:
    """
    Accepts:
      - ["ai", "backend"]
      - [{"name":"backend"}, {"label":"ai"}]
      - {"name":"backend"} (single dict)
      - None
    Returns:
      - list[str] unique, stable order
    """
    raw = task.get("tags") or []
    if raw is None:
        return []
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
    uniq: List[str] = []
    for x in tags:
        if x not in seen:
            uniq.append(x)
            seen.add(x)
    return uniq


def _format_estimation(est: Any) -> Optional[str]:
    """
    Your payload has estimation like "72000".
    We'll treat numbers as seconds (best-effort) and format to min/h.
    If it's not a number -> return as string.
    """
    if est is None:
        return None

    if isinstance(est, str):
        s = est.strip()
        if s.isdigit():
            est = int(s)
        else:
            return _as_str(est)

    if isinstance(est, (int, float)):
        seconds = int(est)
        if seconds <= 0:
            return None
        if seconds < 3600:
            return f"{round(seconds / 60)} min"
        hours = seconds / 3600
        v = f"{hours:.1f}".rstrip("0").rstrip(".")
        return f"{v} h"

    return _as_str(est)


def extract_task_snapshot(task: Dict[str, Any]) -> TaskSnapshot:
    name = _as_str(task.get("name") or task.get("title")) or "Untitled task"
    status = _extract_status(task)
    priority = _extract_priority(task)
    start_date = parse_dt(task.get("startDate") or task.get("start_date"))
    due_date = parse_dt(task.get("dueDate") or task.get("due_date"))

    return TaskSnapshot(
        name=name,
        status=status,
        assignees=_extract_assignees(task),
        priority=priority,
        start_date=start_date,
        due_date=due_date,
        tags=_extract_tags(task),
        description=_extract_description(task),
        estimation=_format_estimation(task.get("estimation") or task.get("estimate") or task.get("timeEstimate")),
    )
