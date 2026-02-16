from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable, List, Optional

from app.models.normalized_models import ActivityEvent, SummaryMeta, TaskSnapshot


def _fmt_date(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    # you can change formatting later (locale, etc.)
    return dt.strftime("%b %d, %Y")


def _plural(n: int, singular: str, plural: Optional[str] = None) -> str:
    if n == 1:
        return f"{n} {singular}"
    return f"{n} {plural or (singular + 's')}"


def build_snapshot_section(snapshot: TaskSnapshot) -> str:
    parts: List[str] = []
    parts.append(f'This task "{snapshot.name}"')

    if snapshot.status:
        parts.append(f"is currently {snapshot.status.lower()}")

    if snapshot.assignees:
        # make @Name style, consistent with your output
        ass = ", ".join([f"@{a}" for a in snapshot.assignees])
        parts.append(f"and assigned to {ass}")

    s = " ".join(parts).strip()
    if not s.endswith("."):
        s += "."
    if snapshot.start_date:
        s += f" Work began on {_fmt_date(snapshot.start_date)}."
    return s


def build_activity_section(events: List[ActivityEvent]) -> str:
    """
    Turn events into a compact narrative.
    - Group tag_added / tag_removed
    - Group assignee changes
    - Keep date/status changes as individual sentences in chronological order
    """
    if not events:
        return ""

    tag_added: List[str] = []
    tag_removed: List[str] = []
    assignees_added: List[str] = []
    assignees_removed: List[str] = []

    # keep non-grouped events in chronological order
    passthrough: List[str] = []

    for e in events:
        if e.type == "tag_added" and e.new:
            tag_added.append(str(e.new))
            continue
        if e.type == "tag_removed" and e.old:
            tag_removed.append(str(e.old))
            continue

        if e.type == "assignee_change":
            # your classifier uses old/new to encode add/remove
            if e.new:
                assignees_added.append(str(e.new))
            elif e.old:
                assignees_removed.append(str(e.old))
            continue

        # keep the already-built readable text
        if e.text:
            passthrough.append(e.text)

    parts: List[str] = []

    # grouped additions/removals first (usually cleaner)
    if tag_added:
        uniq = list(dict.fromkeys(tag_added))
        parts.append(f'Tags added: {", ".join(uniq)}.')
    if tag_removed:
        uniq = list(dict.fromkeys(tag_removed))
        parts.append(f'Tags removed: {", ".join(uniq)}.')

    if assignees_added:
        uniq = list(dict.fromkeys(assignees_added))
        parts.append(f'Assignees added: {", ".join(uniq)}.')
    if assignees_removed:
        uniq = list(dict.fromkeys(assignees_removed))
        parts.append(f'Assignees removed: {", ".join(uniq)}.')

    # then the rest in order
    for t in passthrough:
        t = t.strip()
        if not t:
            continue
        if not t.endswith("."):
            t += "."
        parts.append(t)

    return " ".join(parts).strip()


def build_comment_section(meta: SummaryMeta) -> str:
    if not meta:
        return ""
    n = meta.comments_count or 0
    if n <= 0:
        return ""
    # FIX grammar here ✅
    if n == 1:
        return "1 comment was added."
    return f"{n} comments were added."


def build_meta_section(meta: SummaryMeta) -> str:
    if not meta or not meta.last_activity_at:
        return ""
    return f"The last update was on {_fmt_date(meta.last_activity_at)}."
