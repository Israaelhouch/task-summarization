from __future__ import annotations
from datetime import datetime
from typing import Optional


def format_date(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    return dt.strftime("%b %d, %Y")


def mention(user: Optional[str]) -> Optional[str]:
    if not user:
        return None
    if user.startswith("@"):
        return user
    return f"@{user}"


def pluralize(word: str, count: int) -> str:
    return word if count == 1 else word + "s"
