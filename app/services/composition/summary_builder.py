from __future__ import annotations

from typing import List

from app.models.normalized_models import ActivityEvent, SummaryMeta, TaskSnapshot
from app.services.composition.section_generators import (
    build_activity_section,
    build_comment_section,
    build_meta_section,
    build_snapshot_section,
)


def build_summary(
    snapshot: TaskSnapshot,
    events: List[ActivityEvent],
    meta: SummaryMeta,
) -> str:
    sections = [
        build_snapshot_section(snapshot),
        build_activity_section(events),
        build_comment_section(meta),
        build_meta_section(meta),
    ]

    sections = [s.strip() for s in sections if s and s.strip()]
    return " ".join(sections)
