# Task Summarization API

## Summary
This service exposes a single HTTP endpoint that summarizes a task and its activity history. It
extracts the current task state and generates a concise, human-readable narrative of meaningful
changes (status, tag, date updates, and comments), including the actor and the last update date.

## API Overview
- Endpoint: `POST /summarize`
- Query: `include_events=false` (optional) - include normalized events in the response

## Request Contract
Top-level keys:
- `task`: current task snapshot
- `activity`: chronological history of changes

From `task`, the service extracts:
- name, status, assignees (usernames), priority
- startDate, dueDate
- tags, description (short), estimation

From `activity`, the service extracts:
- status/tag/date/assignee changes
- comments (summarized)
- actor and timestamp

## Response Contract
- `summary`: string
- `meta.events_count`: number
- `meta.comments_count`: number
- `meta.last_activity_at`: ISO timestamp or null
- `events`: normalized events (optional, only if `include_events=true`)

## Example
Request:
```json
{
  "task": {
    "name": "Task Summarization",
    "description": "{...Lexical JSON...}",
    "status": {"name": "In Progress"},
    "priority": 1,
    "startDate": "2026-02-10T00:00:00Z",
    "dueDate": "2026-02-20T00:00:00Z",
    "users": [{"username": "softy"}],
    "tags": [{"name": "backend"}],
    "estimation": "72000"
  },
  "activity": [
    {
      "targetField": "status",
      "oldValue": {"status": {"name": "To Do"}},
      "newValue": {"status": {"name": "In Progress"}},
      "owner": {"username": "softy"},
      "createdAt": "2026-02-16T10:00:00Z"
    },
    {
      "type": "comment",
      "content": "{...Lexical JSON...}",
      "owner": {"username": "alice"},
      "createdAt": "2026-02-16T12:00:00Z"
    }
  ]
}
```

Response:
```json
{
  "summary": "This task \"Task Summarization\" involves: ...",
  "meta": {
    "events_count": 2,
    "comments_count": 1,
    "last_activity_at": "2026-02-16T12:00:00Z"
  },
  "events": null
}
```

## Local Development
Install:
```bash
python -m pip install -e .
python -m pip install -e .[dev]
```

Run:
```bash
uvicorn app.main:app --reload
```

Test:
```bash
pytest
```

## Notes
- Description and comment content may be Lexical JSON strings; text is extracted automatically.
- Dates in summaries are formatted as DD/MM/YYYY.
- Actors and assignees are displayed as @username when available.
