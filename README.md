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

## Docker
Build:
```bash
docker build -t task-summarization .
```

Run:
```bash
docker run --rm -p 8000:8000 task-summarization
```

By default the Docker image runs with gunicorn workers. Override with:
```bash
docker run --rm -p 8000:8000 -e WEB_CONCURRENCY=4 task-summarization
```

## Production Controls
You can configure rate limiting and request size limits via environment variables:

- `RATE_LIMIT_ENABLED` (default: `true`)
- `RATE_LIMIT_MAX_REQUESTS` (default: `60`)
- `RATE_LIMIT_WINDOW_SECONDS` (default: `60`)
- `MAX_BODY_SIZE_BYTES` (default: `1000000`)
- `LOG_LEVEL` (default: `INFO`)
- `LOG_FORMAT` (default: `json`, use `text` for plain logs)
- `WEB_CONCURRENCY` (default: `2`, number of gunicorn workers in Docker)

For Docker Compose, you can copy `.env.example` to `.env` and override values there.

Example:
```bash
RATE_LIMIT_MAX_REQUESTS=120 RATE_LIMIT_WINDOW_SECONDS=60 MAX_BODY_SIZE_BYTES=2000000 LOG_LEVEL=INFO uvicorn app.main:app
```

The API will return an `X-Request-Id` header on every response. You can also pass
your own `X-Request-Id` or `X-Correlation-Id` header to preserve upstream IDs.

## Notes
- Description and comment content may be Lexical JSON strings; text is extracted automatically.
- Dates in summaries are formatted as DD/MM/YYYY.
- Actors and assignees are displayed as @username when available.
