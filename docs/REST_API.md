# REST API Reference

Bossa exposes a REST API for all filesystem operations. Use it when MCP isn't available or when building custom integrations.

**Base URL:** `https://filesystem-fawn.vercel.app/api/v1`

**Authentication:** `Authorization: Bearer YOUR_API_KEY` or `X-API-Key: YOUR_API_KEY`

---

## Endpoints

### Create or Overwrite a File

```
POST /api/v1/files
Content-Type: application/json
```

**Body:**

```json
{
  "path": "/docs/readme.md",
  "content": "# Hello\n\nThis is the content."
}
```

**Response:** `200` — `{"path": "/docs/readme.md", "content": "..."}`

---

### Bulk Create/Overwrite Files

```
POST /api/v1/files/bulk
Content-Type: application/json
```

**Body:**

```json
{
  "files": [
    {"path": "/a.txt", "content": "content a"},
    {"path": "/b.txt", "content": "content b"}
  ]
}
```

- Max 100 files per request.
- Parent folders are created automatically.

**Response:** `200` — `{"created": 2, "updated": 0, "failed": []}`

---

### Read a File

```
GET /api/v1/files?path=/docs/readme.md
```

**Response:** `200` — `{"path": "/docs/readme.md", "content": "..."}`

**Errors:** `404` if file not found

---

### List Directory

```
GET /api/v1/files/list?path=/
```

**Query:**

| Param | Default | Description |
|-------|---------|-------------|
| path | `/` | Directory path |

**Response:** `200` — `{"items": ["customers/", "docs/", "readme.txt"]}`

Directories end with `/`.

---

### Search (Grep)

```
POST /api/v1/files/search
Content-Type: application/json
```

**Body:**

```json
{
  "pattern": "Enterprise",
  "path": "/customers",
  "regex": false,
  "case_sensitive": false,
  "whole_word": false,
  "max_matches": 100,
  "offset": 0,
  "output_mode": "matches",
  "all_of": [],
  "any_of": [],
  "none_of": [],
  "context_before": 0,
  "context_after": 0
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| pattern | string | — | Literal or regex pattern |
| path | string | `/` | Scope to subtree |
| regex | bool | false | Treat pattern as regex |
| case_sensitive | bool | false | Case-sensitive match |
| whole_word | bool | false | Match whole words only |
| max_matches | int | 100 | Max results to return |
| offset | int | 0 | Pagination offset |
| output_mode | string | `matches` | `matches` \| `files_with_matches` \| `count` |
| all_of | string[] | [] | All must appear on same line (AND) |
| any_of | string[] | [] | Any must appear (OR) |
| none_of | string[] | [] | None may appear (exclude) |
| context_before | int | 0 | Lines before each match |
| context_after | int | 0 | Lines after each match |

At least one of `pattern`, `all_of`, `any_of`, or `none_of` is required.

**Response:** `200` — Depends on `output_mode`:

- `matches`: `{matches: [{path, line_number, line, context_before, context_after}], has_more, next_offset}`
- `files_with_matches`: `{files: ["/path/a.md", "/path/b.md"]}`
- `count`: `{count: 42, total_matches: 42}`

---

### Glob Search

```
GET /api/v1/files/glob?pattern=*.md&path=/
```

**Query:**

| Param | Default | Description |
|-------|---------|--------------|
| pattern | — | Glob pattern (e.g. `*.md`, `**/*.py`) |
| path | `/` | Directory to scope search |

**Response:** `200` — `{"paths": ["/docs/a.md", "/docs/b.md"]}`

---

### Edit a File

```
PATCH /api/v1/files
Content-Type: application/json
```

**Body:**

```json
{
  "path": "/config.json",
  "old_string": "\"debug\": false",
  "new_string": "\"debug\": true"
}
```

Replaces the first occurrence of `old_string` with `new_string`.

**Response:** `200` — `{"path": "/config.json", "edited": true}`

**Errors:** `404` if file not found or old_string not in file

---

### Delete a File

```
DELETE /api/v1/files?path=/docs/old.txt
```

**Response:** `200` — `{"path": "/docs/old.txt", "deleted": true}`

**Errors:** `404` if file not found

---

## Public Endpoint

### Health Check

```
GET /health
```

No authentication required. Returns `200` with `{"status": "ok"}`.

---

## Error Responses

| Code | Meaning |
|------|---------|
| 401 | Missing or invalid API key |
| 404 | File or path not found |
| 400 | Invalid request (e.g. empty body, validation error) |
| 413 | Batch size exceeds 100 files |
