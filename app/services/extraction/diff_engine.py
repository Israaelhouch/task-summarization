from __future__ import annotations

from typing import Any, Iterable, List, Tuple


def _norm_str(x: Any) -> str:
    if x is None:
        return ""
    return str(x).strip()


def normalize_tags(raw: Any) -> List[str]:
    """
    Accepts: ["ai", {"name": "backend"}], or {"name": "backend"}, or None.
    Returns unique tag names in stable order.
    """
    if raw is None:
        return []
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return []

    out: List[str] = []
    for t in raw:
        if isinstance(t, str):
            v = _norm_str(t)
            if v:
                out.append(v)
        elif isinstance(t, dict):
            v = _norm_str(t.get("name") or t.get("label") or t.get("title"))
            if v:
                out.append(v)

    seen = set()
    uniq: List[str] = []
    for x in out:
        if x not in seen:
            uniq.append(x)
            seen.add(x)
    return uniq


def diff_list(old: Iterable[Any], new: Iterable[Any]) -> Tuple[List[str], List[str]]:
    """
    Returns (added, removed) based on normalized string values.
    """
    old_set = {_norm_str(x) for x in old if _norm_str(x)}
    new_set = {_norm_str(x) for x in new if _norm_str(x)}

    added = sorted(list(new_set - old_set))
    removed = sorted(list(old_set - new_set))
    return added, removed
