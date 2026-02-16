from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from app.models.normalized_models import ActivityEvent, SummaryMeta, TaskSnapshot
from app.services.composition.formatting import mention
from app.utils.date_utils import parse_dt


def _fmt_date(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    # you can change formatting later (locale, etc.)
    return dt.strftime("%b %d, %Y")


def _join_clauses(clauses: Iterable[str]) -> str:
    items = [c for c in clauses if c and c.strip()]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _fmt_actor(actor: Optional[str]) -> Optional[str]:
    if not actor:
        return None
    return mention(actor) or actor


def _fmt_date_value(value: Optional[str]) -> Optional[str]:
    dt = parse_dt(value)
    return _fmt_date(dt) if dt else None


def build_snapshot_section(snapshot: TaskSnapshot) -> str:
    sentences: List[str] = []
    intro = f'This task "{snapshot.name}"'
    if snapshot.description:
        desc = snapshot.description.strip().rstrip(".")
        intro += f" has the following description: {desc}"
    sentences.append(intro + ".")

    details: List[str] = []
    if snapshot.status:
        details.append(f"is currently {snapshot.status.lower()}")
    if snapshot.assignees:
        assignees = ", ".join([mention(a) or a for a in snapshot.assignees])
        details.append(f"assigned to {assignees}")
    if snapshot.priority is not None:
        details.append(f"priority is {snapshot.priority}")
    if snapshot.tags:
        details.append(f"tags include {', '.join(snapshot.tags)}")
    if details:
        sentences.append(f"It {_join_clauses(details)}.")

    date_bits: List[str] = []
    if snapshot.start_date:
        date_bits.append(f"Work began on {_fmt_date(snapshot.start_date)}")
    if snapshot.due_date:
        date_bits.append(f"the due date is {_fmt_date(snapshot.due_date)}")
    if snapshot.estimation:
        date_bits.append(f"estimate is {snapshot.estimation}")
    if date_bits:
        sentences.append(f"{_join_clauses(date_bits)}.")

    return " ".join(sentences).strip()


def build_activity_section(events: List[ActivityEvent]) -> str:
    """
    Turn events into a compact narrative in chronological order.
    """
    if not events:
        return ""

    parts: List[str] = []
    for e in events:
        actor = _fmt_actor(e.actor)
        text: Optional[str] = None

        if e.type == "comment":
            if e.text:
                base = f'commented: "{e.text}"'
                text = f"{actor} {base}" if actor else f'Comment: "{e.text}"'
        elif e.type == "status_change":
            old = e.old or "—"
            new = e.new or "—"
            base = f"changed status from {old} to {new}"
            text = f"{actor} {base}" if actor else base
        elif e.type == "tag_added":
            tag = e.new or e.old
            if tag:
                base = f'added tag "{tag}"'
                text = f"{actor} {base}" if actor else base
        elif e.type == "tag_removed":
            tag = e.old or e.new
            if tag:
                base = f'removed tag "{tag}"'
                text = f"{actor} {base}" if actor else base
        elif e.type == "date_change":
            field = e.field or "date"
            old = _fmt_date_value(e.old)
            new = _fmt_date_value(e.new)
            if old and new:
                base = f"changed {field} from {old} to {new}"
            elif new:
                base = f"set {field} to {new}"
            elif old:
                base = f"cleared {field} (was {old})"
            else:
                base = e.text or ""
            text = f"{actor} {base}" if actor and base else base
        elif e.type == "assignee_change":
            if e.new:
                assignee = mention(str(e.new)) or str(e.new)
                base = f"added assignee {assignee}"
                text = f"{actor} {base}" if actor else base
            elif e.old:
                assignee = mention(str(e.old)) or str(e.old)
                base = f"removed assignee {assignee}"
                text = f"{actor} {base}" if actor else base
        else:
            text = e.text

        if not text:
            continue
        text = text.strip()
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        if not text.endswith("."):
            text += "."
        parts.append(text)

    return " ".join(parts).strip()


def build_comment_section(meta: SummaryMeta) -> str:
    if not meta:
        return ""
    n = meta.comments_count or 0
    if n == 0:
        return "No comments were added."
    return ""


def build_meta_section(meta: SummaryMeta) -> str:
    if not meta or not meta.last_activity_at:
        return ""
    return f"The last update was on {_fmt_date(meta.last_activity_at)}."
