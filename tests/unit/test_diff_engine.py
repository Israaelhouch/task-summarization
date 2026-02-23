from app.services.extraction.diff_engine import normalize_tags, diff_list


def test_normalize_tags():
    raw = [{"name": "backend"}, "ai", {"label": "urgent"}, {"title": "prod"}, ""]
    assert normalize_tags(raw) == ["backend", "ai", "urgent", "prod"]


def test_diff_list():
    added, removed = diff_list(["a", "b"], ["b", "c"])
    assert added == ["c"]
    assert removed == ["a"]
