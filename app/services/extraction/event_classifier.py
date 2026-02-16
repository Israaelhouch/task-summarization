from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from app.models.normalized_models import ActivityEvent
from app.services.extraction.diff_engine import diff_list, normalize_tags
from app.utils.date_utils import parse_dt
from app.utils.text_utils import shorten_text


def _as_str(x: Any) -> Optional[str]:
    if x is None:
        return None
    s = str(x).strip()
    return s if s else None


def _actor(activity_item: Dict[str, Any]) -> Optional[str]:
    # Your payload uses "owner" (not "actor")
    a = activity_item.get("actor") or activity_item.get("owner") or activity_item.get("user") or activity_item.get("by")
    if isinstance(a, str):
        return _as_str(a)
    if isinstance(a, dict):
        return _as_str(
            a.get("username")
            or a.get("handle")
            or a.get("fullName")
            or a.get("displayName")
            or a.get("name")
            or a.get("email")
        )
    return None


def _timestamp(activity_item: Dict[str, Any]):
    return parse_dt(
        activity_item.get("timestamp")
        or activity_item.get("createdAt")
        or activity_item.get("at")
        or activity_item.get("date")
    )


def _lexical_to_text(s: str) -> str:
    """
    Lexical editor JSON can be stored as a string:
      {"root": {"children": [...{"type":"text","text":"hello"}...]}}
    We extract all "text" nodes and join them.
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
    out = " ".join(texts).strip()
    return out or s


def _comment_text(activity_item: Dict[str, Any]) -> Optional[str]:
    # Common keys (your payload uses "content")
    for k in ("comment", "message", "text", "body", "content"):
        v = activity_item.get(k)

        if isinstance(v, str) and v.strip():
            txt = v.strip()
            if txt.startswith("{") and '"root"' in txt:
                txt = _lexical_to_text(txt)
            return shorten_text(txt, max_len=200)

        if isinstance(v, dict):
            inner = v.get("text") or v.get("body") or v.get("content")
            if isinstance(inner, str) and inner.strip():
                txt = inner.strip()
                if txt.startswith("{") and '"root"' in txt:
                    txt = _lexical_to_text(txt)
                return shorten_text(txt, max_len=200)

    return None


def _field_update_shape(activity_item: Dict[str, Any]) -> Optional[Tuple[str, Any, Any]]:
    """
    Detect:
      {"field": "status", "old": "To Do", "new": "In Progress"}
    """
    field = activity_item.get("field") or activity_item.get("key")
    if not field:
        return None
    old = activity_item.get("old") if "old" in activity_item else activity_item.get("from")
    new = activity_item.get("new") if "new" in activity_item else activity_item.get("to")
    if old is None and new is None:
        return None
    return str(field), old, new


def _changes_shape(activity_item: Dict[str, Any]) -> List[Tuple[str, Any, Any]]:
    """
    Detect:
      {"changes": {"status": {"from": "...", "to": "..."}}}
    """
    changes = activity_item.get("changes")
    if not isinstance(changes, dict):
        return []
    out: List[Tuple[str, Any, Any]] = []
    for field, payload in changes.items():
        if isinstance(payload, dict):
            old = payload.get("from") if "from" in payload else payload.get("old")
            new = payload.get("to") if "to" in payload else payload.get("new")
            out.append((str(field), old, new))
        else:
            out.append((str(field), None, payload))
    return out


def _targetfield_shape(activity_item: Dict[str, Any]) -> Optional[Tuple[str, Any, Any]]:
    """
    Your real payload:
      {"targetField": "tags", "oldValue": {...}, "newValue": {...}}
    Normalize to (field, old, new).

    - oldValue/newValue might be full snapshots, OR already the field value.
    - If dict and contains that field, we take dict[field].
    """
    field = activity_item.get("targetField")
    if not field:
        return None

    old_v = activity_item.get("oldValue")
    new_v = activity_item.get("newValue")

    if isinstance(old_v, dict) and str(field) in old_v:
        old_v = old_v.get(str(field))
    if isinstance(new_v, dict) and str(field) in new_v:
        new_v = new_v.get(str(field))

    return str(field), old_v, new_v


def _norm_status_value(x: Any) -> Optional[str]:
    """
    Status can be:
      - "To Do"
      - {"id": "...", "name": "To Do", ...}
    We want a human string, not the dict printed.
    """
    if x is None:
        return None
    if isinstance(x, str):
        return _as_str(x)
    if isinstance(x, dict):
        return _as_str(x.get("name") or x.get("label") or x.get("title"))
    return _as_str(x)


def classify_activity_item(activity_item: Dict[str, Any]) -> List[ActivityEvent]:
    """
    Convert one raw activity item into 0..N normalized ActivityEvent(s).
    """
    actor = _actor(activity_item)
    at = _timestamp(activity_item)
    events: List[ActivityEvent] = []

    # 1) Comment (usually "comment" type entries)
    c = _comment_text(activity_item)
    if c:
        events.append(
            ActivityEvent(
                type="comment",
                actor=actor,
                at=at,
                text=f'Comment added: "{c}"',
                field="comment",
                old=None,
                new=None,
            )
        )
        return events

    candidates: List[Tuple[str, Any, Any]] = []

    # 2) Your payload shape
    tf = _targetfield_shape(activity_item)
    if tf:
        candidates.append(tf)

    # 3) Other supported shapes
    fu = _field_update_shape(activity_item)
    if fu:
        candidates.append(fu)

    candidates.extend(_changes_shape(activity_item))

    # 4) before/after best effort
    before = activity_item.get("before")
    after = activity_item.get("after")
    if isinstance(before, dict) and isinstance(after, dict):
        for field in ("status", "priority", "startDate", "dueDate", "tags", "assignees"):
            if field in before or field in after:
                candidates.append((field, before.get(field), after.get(field)))

    for field, old, new in candidates:
        f = field.lower()

        # status
        if f in ("status", "state"):
            o, n = _norm_status_value(old), _norm_status_value(new)
            if o != n and (o or n):
                events.append(
                    ActivityEvent(
                        type="status_change",
                        actor=actor,
                        at=at,
                        text=f"Status changed from {o or '—'} to {n or '—'}",
                        field="status",
                        old=o,
                        new=n,
                    )
                )
            continue

        # tags
        if f in ("tags", "tag"):
            old_tags = normalize_tags(old)
            new_tags = normalize_tags(new)
            added, removed = diff_list(old_tags, new_tags)

            for t in added:
                events.append(
                    ActivityEvent(
                        type="tag_added",
                        actor=actor,
                        at=at,
                        text=f'Tag "{t}" added',
                        field="tags",
                        old=None,
                        new=t,
                    )
                )
            for t in removed:
                events.append(
                    ActivityEvent(
                        type="tag_removed",
                        actor=actor,
                        at=at,
                        text=f'Tag "{t}" removed',
                        field="tags",
                        old=t,
                        new=None,
                    )
                )
            continue

        # dates
        if f in ("startdate", "start_date", "start", "duedate", "due_date", "due"):
            o_dt = parse_dt(old)
            n_dt = parse_dt(new)
            if o_dt != n_dt and (o_dt or n_dt):
                pretty_field = "start date" if "start" in f else "due date"
                events.append(
                    ActivityEvent(
                        type="date_change",
                        actor=actor,
                        at=at,
                        text=(
                            f"{pretty_field.title()} changed from "
                            f"{o_dt.date().isoformat() if o_dt else '—'} to "
                            f"{n_dt.date().isoformat() if n_dt else '—'}"
                        ),
                        field=pretty_field,
                        old=o_dt.isoformat() if o_dt else None,
                        new=n_dt.isoformat() if n_dt else None,
                    )
                )
            continue

        # assignees
        if f in ("assignees", "assignee", "users"):
            def norm_people(x: Any) -> List[str]:
                if x is None:
                    return []
                if isinstance(x, dict):
                    x = [x]
                if not isinstance(x, list):
                    return []
                out: List[str] = []
                for p in x:
                    if isinstance(p, str):
                        s = _as_str(p)
                        if s:
                            out.append(s)
                    elif isinstance(p, dict):
                        s = _as_str(
                            p.get("username")
                            or p.get("handle")
                            or p.get("fullName")
                            or p.get("displayName")
                            or p.get("name")
                            or p.get("email")
                        )
                        if s:
                            out.append(s)

                seen = set()
                uniq: List[str] = []
                for s in out:
                    if s not in seen:
                        uniq.append(s)
                        seen.add(s)
                return uniq

            old_p = norm_people(old)
            new_p = norm_people(new)
            added, removed = diff_list(old_p, new_p)

            for u in added:
                events.append(
                    ActivityEvent(
                        type="assignee_change",
                        actor=actor,
                        at=at,
                        text=f'Assignee "{u}" added',
                        field="assignees",
                        old=None,
                        new=u,
                    )
                )
            for u in removed:
                events.append(
                    ActivityEvent(
                        type="assignee_change",
                        actor=actor,
                        at=at,
                        text=f'Assignee "{u}" removed',
                        field="assignees",
                        old=u,
                        new=None,
                    )
                )
            continue

        # ignore unknown/noise fields by default

    return events
