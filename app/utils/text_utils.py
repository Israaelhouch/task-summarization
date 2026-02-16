from __future__ import annotations

def shorten_text(text: str, max_len: int = 180) -> str:
    t = " ".join(text.split())
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"
