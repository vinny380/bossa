---
title: "Docs MCP Server"
description: "Connect the Bossa documentation to Cursor, VS Code, Claude, or Claude Code so your AI assistant can search our docs."
---

# Add These Docs As MCP to Your IDE

Give your AI assistant (Cursor, VS Code, Claude, Claude Code) direct access to the Bossa documentation. When you ask questions about Bossa, the AI can search our docs in real time instead of relying on web search.

**MCP server URL:** `https://docs.bossamemory.com/mcp`

---

## Quick Connect (One-Click)

Use the contextual menu at the top of any page on this site:

- **Connect to Cursor** — Installs the Bossa docs MCP server in Cursor
- **Connect to VS Code** — Installs the Bossa docs MCP server in VS Code

Select the menu and choose your IDE for a one-click setup.

---

## Cursor

1. Open the command palette: **Command + Shift + P** (Mac) or **Ctrl + Shift + P** (Windows/Linux)
2. Search for **"Open MCP settings"** and select it
3. Select **Add custom MCP** — this opens your `mcp.json` file
4. Add the Bossa docs server:

```json
{
  "mcpServers": {
    "Bossa Docs": {
      "url": "https://docs.bossamemory.com/mcp"
    }
  }
}
```

5. Save the file. Cursor will connect automatically.

**Test it:** In Cursor's chat, ask "What tools do you have available?" You should see the Bossa Docs MCP server listed.

---

## VS Code

1. Create or edit `.vscode/mcp.json` in your project
2. Add the Bossa docs server:

```json
{
  "servers": {
    "Bossa Docs": {
      "type": "http",
      "url": "https://docs.bossamemory.com/mcp"
    }
  }
}
```

3. Save the file.

See the [VS Code MCP documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers) for more details.

---

## Claude (claude.ai)

1. Go to [Claude Settings → Connectors](https://claude.ai/settings/connectors)
2. Select **Add custom connector**
3. Add:
   - **Name:** `Bossa Docs`
   - **URL:** `https://docs.bossamemory.com/mcp`
4. Select **Add**

When you chat with Claude, use the attachments button (plus icon) and select the Bossa Docs connector to give Claude access to our documentation.

---

## Claude Code

Run this command to add the Bossa docs MCP server:

```bash
claude mcp add --transport http "Bossa Docs" https://docs.bossamemory.com/mcp
```

Verify the connection:

```bash
claude mcp list
```

---

## Why This Helps

- **No search noise** — The AI goes straight to our documentation instead of generic web results
- **Up-to-date** — MCP searches our current indexed docs, not stale cached pages
- **Integrated** — The AI searches during response generation, not as a separate step

---

## Next Steps

- [Getting Started](GETTING_STARTED) — Sign up and make your first request
- [MCP Integration](MCP) — Connect Claude, Cursor, LangChain to the Bossa API (not the docs)
