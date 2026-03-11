---
title: "REST API Reference"
description: "Full endpoint documentation for all filesystem operations."
---

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
GET /api/v1/files/list?path=/&metadata=false
```

**Query:**

| Param | Default | Description |
|-------|---------|-------------|
| path | `/` | Directory path |
| metadata | `false` | If `true`, return `{name, type, size?, modified?}` per item |

**Response:** `200` — Without metadata: `{"items": ["customers/", "docs/", "readme.txt"]}`. With `metadata=true`: `{"items": [{"name": "docs/", "type": "directory"}, {"name": "readme.txt", "type": "file", "size": 1024, "modified": "2026-03-06T10:00:00Z"}]}`. Directories end with `/`.

---

### Stat (File Metadata)

```
GET /api/v1/files/stat?path=/docs/readme.md
```

**Response:** `200` — `{"path": "/docs/readme.md", "size": 1024, "modified": "2026-03-06T10:00:00Z", "created": "2026-03-01T08:00:00Z"}`. `404` if not found.

---

### Tree

```
GET /api/v1/files/tree?path=/&depth=2
```

**Query:** `path` (default `/`), `depth` (optional, limits recursion).

**Response:** `200` — `{"tree": "  a/\n    b/\n      file.txt"}`

---

### Disk Usage

```
GET /api/v1/files/du?path=/
```

**Response:** `200` — `{"usage": [{"path": "/", "size": 4096}, {"path": "/docs", "size": 2048}]}`

---

### Batch Operations

```
POST /api/v1/files/batch
Content-Type: application/json
```

**Body:**

```json
{
  "ops": [
    {"op": "read", "path": "/docs/api.md"},
    {"op": "write", "path": "/output/summary.md", "content": "..."},
    {"op": "delete", "path": "/temp.txt"}
  ]
}
```

Max 100 ops per request. **Response:** `200` — `{"results": [{"op": "read", "path": "...", "content": "..."}, ...]}`

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
  "new_string": "\"debug\": true",
  "replace_all": false
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| path | string | — | File path |
| old_string | string | — | Substring to replace |
| new_string | string | — | Replacement |
| replace_all | bool | false | If true, replace all occurrences; else first only |

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

## Usage

```
GET /api/v1/usage
```

Returns current usage and limits for the account associated with the API key.

**Response:** `200` — `{"storage_mb": 12.5, "files_count": 42, "requests_today": 156, "tier": "free", "limits": {"storage_mb": 100, "files": 500, "requests_per_day": 1000}}`

See [Pricing & Limits](PRICING) for tier details.

---

## Billing

### Create Checkout Session

```
POST /api/v1/billing/checkout?interval=month
Authorization: Bearer <JWT>
```

Creates a Stripe Checkout session for Pro subscription. Requires JWT (from `bossa login`), not API key.

**Query:** `interval` — `month` (default) or `year`

**Response:** `200` — `{"checkout_url": "https://checkout.stripe.com/..."}`

Redirect the user to `checkout_url` to complete payment. See [Pricing & Limits](PRICING).

### Create Portal Session

```
POST /api/v1/billing/portal
Authorization: Bearer <JWT>
```

Creates a Stripe Customer Portal session for managing subscription (update payment, view invoices, cancel). Requires JWT (from `bossa login`), not API key.

**Response:** `200` — `{"url": "https://billing.stripe.com/..."}`

Redirect the user to `url` to manage their subscription. Returns `400` with `"No billing account. Run 'bossa billing upgrade' first."` if the user has no Stripe customer. Returns `503` if billing is not configured.

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
| 402 | Usage limit exceeded (storage, files, requests, or workspaces). [Upgrade](https://bossa.mintlify.app/pricing) for higher limits. |
| 404 | File or path not found |
| 400 | Invalid request (e.g. empty body, validation error) |
| 413 | Batch size exceeds 100 files |
