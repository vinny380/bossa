"""bossa init - Add Bossa usage instructions to AGENTS.md / CLAUDE.md / GEMINI.md."""

import os
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Literal

import questionary
import typer
from questionary import Style

from cli.config import BOSSA_API_URL

# One Dark palette — polished, professional (InquirerPy-style)
_INIT_CHECKBOX_STYLE = Style(
    [
        ("qmark", "fg:#e5c07b"),  # amber
        ("question", "fg:#abb2bf"),  # gray
        ("answer", "fg:#61afef"),  # blue
        ("pointer", "fg:#61afef"),  # blue
        ("highlighted", "fg:#61afef bold"),
        ("selected", "fg:#98c379"),  # green
        ("separator", "fg:#5c6370"),  # dim gray
        ("instruction", "fg:#5c6370"),
        ("text", "fg:#abb2bf"),
        ("disabled", "fg:#5c6370"),
    ]
)

# Project-level paths to check (relative to project root)
_PROJECT_FILES = ["AGENTS.md", "CLAUDE.md", ".claude/CLAUDE.md", "GEMINI.md"]

# Global paths (relative to home or XDG_CONFIG_HOME)
_GLOBAL_PATHS = [
    ".claude/CLAUDE.md",
    ".codex/AGENTS.md",
    ".cursor/AGENTS.md",
    ".gemini/GEMINI.md",
]


def _find_project_root(cwd: Path) -> Path:
    """Find project root (directory with .git) by walking up from cwd."""
    current = Path(cwd).resolve()
    while True:
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            return Path(cwd).resolve()
        current = parent


def discover_project_paths(cwd: Path) -> list[Path]:
    """Discover AGENTS.md, CLAUDE.md, .claude/CLAUDE.md, GEMINI.md at project root."""
    root = _find_project_root(cwd)
    found: list[Path] = []
    for rel in _PROJECT_FILES:
        p = root / rel
        if p.exists():
            found.append(p)
    return found


def discover_global_paths() -> list[Path]:
    """Discover global agent config files (~/.claude, ~/.codex, ~/.gemini, etc.)."""
    home = Path.home()
    xdg = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    found: list[Path] = []
    for rel in _GLOBAL_PATHS:
        p = home / rel
        if p.exists() or p.parent.exists():
            found.append(p)
    # Proposed standard: ~/.config/agents/AGENTS.md
    agents_config = xdg / "agents" / "AGENTS.md"
    if agents_config.exists() or agents_config.parent.exists():
        found.append(agents_config)
    return found


def _format_path_for_display(p: Path) -> str:
    """Short path for checkbox display (relative or ~ for home)."""
    try:
        rel = p.relative_to(Path.cwd())
        return f"./{rel}" if rel != Path(".") else str(p)
    except ValueError:
        pass
    try:
        home = Path.home()
        if p == home or str(p).startswith(str(home) + os.sep):
            return "~" + str(p)[len(str(home)) :]
    except (ValueError, OSError):
        pass
    return str(p)


def _get_bossa_version() -> str:
    """Return the installed bossa-memory version."""
    try:
        return version("bossa-memory")
    except Exception:
        return "0.0.0"


def _get_intro() -> str:
    """Shared intro for all templates."""
    return """## Bossa — Long-term memory for AI agents

Bossa gives your agent a persistent filesystem. Use `pip install bossa-memory` and connect via CLI or MCP.

**When to use:** User preferences, context persistence, session memory, dynamic context discovery.

**When NOT to use:** Temporary data, files already in git, large binaries.

### Auth

- `BOSSA_API_KEY` — Set in env, or use `bossa workspace use <name> --key sk-xxx` to store it."""


def _get_cli_section() -> str:
    """CLI-specific template content."""
    return """
### Commands (CLI)

| Command | Description |
|---------|-------------|
| `bossa files ls [path]` | List directory |
| `bossa files read <path>` | Read file |
| `bossa files write <path>` | Write (stdin or `--content`) |
| `bossa files grep <pattern>` | Search contents |
| `bossa files glob <pattern>` | Find by glob |
| `bossa files edit <path> --old X --new Y` | Replace substring |
| `bossa files delete <path>` | Delete file |

### Agent flags (CLI)

- `--json` or `BOSSA_CLI_JSON=1` — Machine-readable output
- `--safe` — On read-only commands, signals auto-approval for harnesses

### Exit codes

- `0` — Success
- `1` — Error (not found, validation)
- `2` — Auth failure (invalid API key)"""


def _get_mcp_section() -> str:
    """MCP-specific template content."""
    mcp_url = f"{BOSSA_API_URL.rstrip('/')}/mcp"
    return f"""
### MCP

**Endpoint:** `{mcp_url}`

**Auth:** Pass `Authorization: Bearer YOUR_API_KEY` or `X-API-Key: YOUR_API_KEY` in headers.

| Tool | Description |
|------|-------------|
| `ls` | List files and directories at path |
| `read_file` | Return file contents with numbered lines |
| `write_file` | Create or overwrite a file |
| `edit_file` | Replace substring in a file |
| `grep` | Search file contents |
| `glob_search` | Find files by glob pattern |
| `delete_file` | Permanently delete a file |
| `stat` | Return file metadata |
"""


def _get_bossa_template(mode: Literal["cli", "mcp", "both"]) -> str:
    """Return the Bossa section markdown template for the given mode."""
    ver = _get_bossa_version()
    intro = _get_intro()

    if mode == "cli":
        body = _get_cli_section()
    elif mode == "mcp":
        body = _get_mcp_section()
    else:
        body = _get_cli_section() + "\n\n" + _get_mcp_section()

    footer = (
        f"\n\n*Generated by bossa-memory v{ver}. To update: `bossa init --overwrite`*"
    )
    return f"<!-- Bossa: start -->\n{intro}{body}{footer}\n<!-- Bossa: end -->"


def _write_bossa_section(target: Path, overwrite: bool, template: str) -> None:
    """Write Bossa section to file: replace existing section or append if none."""
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = target.read_text() if target.exists() else ""

    start_marker = "<!-- Bossa: start -->"
    end_marker = "<!-- Bossa: end -->"
    start_idx = existing.find(start_marker)
    # Find last end_marker so we collapse any duplicate sections into one
    end_idx = existing.rfind(end_marker)

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        # Section exists: always replace (never append, prevents duplication)
        before = existing[:start_idx].rstrip()
        after = existing[end_idx + len(end_marker) :].lstrip("\n")
        new_content = (
            f"{before}\n\n{template}\n\n{after}" if after else f"{before}\n\n{template}"
        )
        target.write_text(new_content)
        return

    # No section found: append
    suffix = "\n\n" if existing.strip() else ""
    target.write_text(existing.rstrip() + suffix + template)


def init(
    project: bool = typer.Option(False, "--project", help="Only project files"),
    global_: bool = typer.Option(False, "--global", help="Only global files"),
    path: list[str] = typer.Option([], "--path", "-p", help="Explicit path(s)"),
    mode: str = typer.Option(
        "both",
        "--mode",
        "-m",
        help="CLI, MCP, or both",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing Bossa section (use when upgrading to a new bossa version)",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
) -> None:
    """Add Bossa usage instructions to AGENTS.md / CLAUDE.md / GEMINI.md."""
    if mode not in ("cli", "mcp", "both"):
        raise typer.BadParameter("--mode must be cli, mcp, or both")

    from rich.console import Console
    from rich.tree import Tree

    console = Console()
    cwd = Path.cwd()

    # Resolve target paths
    if path:
        targets = [Path(p).expanduser().resolve() for p in path]
    elif project:
        targets = discover_project_paths(cwd)
    elif global_:
        targets = discover_global_paths()
    else:
        # Interactive: discover both, present choice
        project_paths = discover_project_paths(cwd)
        global_paths = discover_global_paths()
        if not project_paths and not global_paths:
            console.print()
            console.print("[dim]No agent config files found.[/dim]")
            console.print("[dim]Create one with: bossa init --path ./AGENTS.md[/dim]")
            console.print()
            raise typer.Exit(1)
        if project_paths or global_paths:
            tree = Tree("[dim]Found agent config files[/dim]", guide_style="dim")
            if project_paths:
                proj = tree.add("[dim]Project[/dim]")
                for p in project_paths:
                    proj.add(_format_path_for_display(p))
            if global_paths:
                glob = tree.add("[dim]Global[/dim]")
                for p in global_paths:
                    glob.add(_format_path_for_display(p))
            console.print()
            console.print(tree)
            console.print()
        targets = list(dict.fromkeys(project_paths + global_paths))

    if not targets:
        console.print(
            "[dim]No agent config files found. Use --path to specify a file.[/dim]"
        )
        raise typer.Exit(1)

    # Interactive selection or confirmation (unless --yes)
    if not yes:
        if path:
            # --path: simple confirm (user explicitly chose paths)
            if not typer.confirm(f"Add Bossa section to {len(targets)} file(s)?"):
                raise typer.Exit(0)
        elif sys.stdout.isatty() or os.environ.get("BOSSA_INIT_FORCE_CHECKBOX") == "1":
            # Discovery: checkbox multi-select
            choices = [
                questionary.Choice(_format_path_for_display(p), value=p, checked=True)
                for p in targets
            ]
            try:
                selected = questionary.checkbox(
                    "Select files to update",
                    choices=choices,
                    style=_INIT_CHECKBOX_STYLE,
                    instruction="space: toggle  enter: confirm",
                ).ask()
            except (KeyboardInterrupt, EOFError):
                raise typer.Exit(0)
            if selected is None or len(selected) == 0:
                raise typer.Exit(0)
            targets = selected
        # No TTY and no --path: use all targets (e.g. in pipes/CI)

    # Mode selection (interactive only)
    if not yes and (
        sys.stdout.isatty() or os.environ.get("BOSSA_INIT_FORCE_CHECKBOX") == "1"
    ):
        try:
            selected = questionary.select(
                "How will your agent use Bossa?",
                choices=[
                    questionary.Choice(
                        "CLI — agent runs subprocesses (bossa files ls, read, write...)",
                        value="cli",
                    ),
                    questionary.Choice(
                        "MCP — harness has native MCP (Cursor, Claude, LangChain)",
                        value="mcp",
                    ),
                    questionary.Choice(
                        "Both — include CLI and MCP instructions",
                        value="both",
                    ),
                ],
                style=_INIT_CHECKBOX_STYLE,
            ).ask()
        except (KeyboardInterrupt, EOFError):
            raise typer.Exit(0)
        if selected is None:
            raise typer.Exit(0)
        mode = selected

    template = _get_bossa_template(mode)
    for target in targets:
        _write_bossa_section(target, overwrite, template)
    console.print()
    for target in targets:
        console.print(
            f"  [green]✓[/green] [dim]{_format_path_for_display(target)}[/dim]"
        )
    console.print()
