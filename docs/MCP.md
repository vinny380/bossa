# MCP Integration

Bossa exposes a virtual filesystem via **MCP** (Model Context Protocol). Connect Claude Desktop, Cursor, LangChain, or any MCP-compatible client to use `ls`, `read_file`, `write_file`, `grep`, `glob_search`, `edit_file`, and `delete_file`.

**MCP endpoint:** `https://filesystem-fawn.vercel.app/mcp`

**Alternative:** If your agent harness runs tools as subprocesses (CLI-based), use the Bossa CLI instead: `bossa files ls`, `read`, `write`, `grep`, `glob`, `edit`, `delete` with `--json` or `BOSSA_CLI_JSON=1`. See [CLI Reference](./CLI.md).

---

## Authentication

Pass your workspace API key in HTTP headers when connecting:

| Header | Value |
|--------|-------|
| `Authorization` | `Bearer YOUR_API_KEY` |
| `X-API-Key` | `YOUR_API_KEY` |

Both headers are supported; use at least one.

---

## Available Tools

| Tool | Description | Read-only |
|------|-------------|-----------|
| `ls` | List files and directories at a path. Directories end with `/`. | ✓ |
| `read_file` | Return file contents with numbered lines (`1: line text`). | ✓ |
| `write_file` | Create or overwrite a file. | |
| `edit_file` | Replace the first occurrence of a substring in a file. | |
| `grep` | Search file contents (literal/regex, boolean filters, pagination). | ✓ |
| `glob_search` | Find files by glob pattern (e.g. `**/*.py`). | ✓ |
| `delete_file` | Permanently delete a file. | |

Tools include MCP annotations (`readOnlyHint`, `destructiveHint`, etc.) so clients can skip confirmation for safe operations.

---

## Client Setup

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "bossa": {
      "url": "https://filesystem-fawn.vercel.app/mcp",
      "transport": "streamable_http",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY",
        "X-API-Key": "YOUR_API_KEY"
      }
    }
  }
}
```

Replace `YOUR_API_KEY` with your workspace API key. Restart Claude Desktop.

### Cursor

Add Bossa as an MCP server in Cursor settings. Use:

- **URL:** `https://filesystem-fawn.vercel.app/mcp`
- **Transport:** Streamable HTTP
- **Headers:** `Authorization: Bearer YOUR_API_KEY` or `X-API-Key: YOUR_API_KEY`

### LangChain (Python)

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "bossa": {
        "url": "https://filesystem-fawn.vercel.app/mcp",
        "transport": "streamable_http",
        "headers": {
            "X-API-Key": "YOUR_API_KEY",
            "Authorization": "Bearer YOUR_API_KEY"
        }
    }
})

tools = await client.get_tools()
# Use tools with your agent
```

### Generic MCP Client (HTTP)

The MCP endpoint uses the [Streamable HTTP](https://modelcontextprotocol.io/specification/2025-06-18/server/transports#streamable-http) transport. Any client that supports streamable HTTP + custom headers can connect.

---

## Tool Details

### `ls`

List immediate children at a path.

- **path** (optional): Directory path. Default: `/`
- Returns: One entry per line; directories end with `/`

### `read_file`

Read a file's full contents.

- **path** (required): Absolute file path
- Returns: Numbered lines (`1: line text`) or error if not found

### `write_file`

Create or overwrite a file.

- **path** (required): Absolute path
- **content** (required): Full file content

### `edit_file`

Replace the first occurrence of a string in a file.

- **path** (required): File path
- **old_string** (required): Substring to replace
- **new_string** (required): Replacement

### `grep`

Search file contents with flexible options.

- **pattern**: Literal or regex pattern
- **path**: Scope to subtree (default: `/`)
- **regex**: Use regex for pattern (default: false)
- **case_sensitive**: Case-sensitive match (default: false)
- **output_mode**: `matches` | `files_with_matches` | `count`
- **all_of**, **any_of**, **none_of**: Boolean filters (same line)
- **max_matches**, **offset**: Pagination
- **context_before**, **context_after**: Context lines around matches

### `glob_search`

Find files by glob pattern.

- **pattern** (required): Glob (e.g. `**/*.md`, `/docs/*.txt`)
- **base_path** (optional): Scope to subtree

### `delete_file`

Permanently delete a file.

- **path** (required): File path

---

## Workspace Isolation

Each API key maps to one workspace. Files in workspace A are invisible to workspace B. Create multiple workspaces and keys for different apps or tenants.
