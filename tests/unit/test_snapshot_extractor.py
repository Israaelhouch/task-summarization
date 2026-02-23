from app.services.extraction.snapshot_extractor import extract_task_snapshot

def test_extract_snapshot_minimal():
    task = {"name": "Build summarization", "status": "In Progress"}
    snap = extract_task_snapshot(task)
    assert snap.name == "Build summarization"
    assert snap.status == "In Progress"

def test_extract_snapshot_assignees_tags():
    task = {
        "name": "X",
        "assignees": [{"username": "softy"}, {"displayName": "Hachem"}],
        "tags": [{"name": "backend"}, "ai"],
    }
    snap = extract_task_snapshot(task)
    assert snap.assignees == ["softy", "Hachem"]
    assert snap.tags == ["backend", "ai"]


def test_extract_snapshot_lexical_description_dict():
    lexical = {
        "root": {
            "children": [
                {"children": [{"type": "text", "text": "Lexical description here."}], "type": "paragraph"}
            ],
            "type": "root",
        }
    }
    task = {"name": "X", "description": lexical}
    snap = extract_task_snapshot(task)
    assert snap.description == "Lexical description here."
