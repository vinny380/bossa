"""Filesystem commands: ls, read, write, grep, glob, edit, delete."""

import json
import os
import sys
from pathlib import Path

import httpx
import typer
from rich.console import Console

from cli.config import BOSSA_API_BASE, BOSSA_TIMEOUT
from cli.workspace_context import get_active_key, get_workspace_key

console = Console()
files_app = typer.Typer(
    help="Filesystem operations: ls, read, write, grep, glob, edit, delete. Use --json for agent-friendly output. Exit codes: 0=success, 1=error, 2=auth failure."
)


def _get_api_key(key: str | None, base_url: str) -> str:
    """Resolve API key: --key > BOSSA_API_KEY > BOSSA_WORKSPACE (from config) > config.active_key > error."""
    if key:
        return key
    if "localhost" in base_url:
        return "sk-default"
    env_key = os.environ.get("BOSSA_API_KEY", "").strip()
    if env_key:
        return env_key
    # BOSSA_WORKSPACE=name overrides active workspace
    workspace_name = os.environ.get("BOSSA_WORKSPACE", "").strip()
    if workspace_name:
        stored_key = get_workspace_key(workspace_name)
        if stored_key:
            return stored_key
    # Fall back to active_key from config
    active_key = get_active_key()
    if active_key:
        return active_key
    console.print(
        "[red]No API key. Set BOSSA_API_KEY, use --key, or run: bossa workspace use <name> --key <key>[/red]"
    )
    raise typer.Exit(1)


def _api_headers(key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {key}", "X-API-Key": key}


def _json_mode(json_flag: bool) -> bool:
    """True if output should be JSON (--json or BOSSA_CLI_JSON=1)."""
    if json_flag:
        return True
    return os.environ.get("BOSSA_CLI_JSON", "").strip() in ("1", "true", "yes")


def _handle_response(
    resp: httpx.Response, exit_401: int = 2, exit_error: int = 1
) -> None:
    """Print error and exit on failure. 401 -> exit_401, else -> exit_error."""
    if resp.status_code == 401:
        console.print("[red]Unauthorized. Check BOSSA_API_KEY or --key.[/red]")
        raise typer.Exit(exit_401)
    if resp.status_code >= 400:
        console.print(f"[red]Error {resp.status_code}: {resp.text}[/red]")
        raise typer.Exit(exit_error)


@files_app.command("ls")
def ls_cmd(
    path: str = typer.Argument("/", help="Directory path to list"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    safe: bool = typer.Option(
        False, "--safe", help="Read-only; signals auto-approval for agent harnesses"
    ),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
) -> None:
    """List files and directories at a path. Exit codes: 0=success, 1=error, 2=auth failure."""
    api_key = _get_api_key(key, BOSSA_API_BASE)
    url = f"{BOSSA_API_BASE}/api/v1/files/list"
    params: dict = {"path": path}
    if _json_mode(json_output):
        params["metadata"] = "true"
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.get(url, headers=_api_headers(api_key), params=params)
    _handle_response(resp)
    data = resp.json()
    items = data.get("items", [])
    if _json_mode(json_output):
        console.print(json.dumps({"items": items}))
    else:
        for item in items:
            console.print(item)


@files_app.command("read")
def read_cmd(
    path: str = typer.Argument(..., help="File path to read"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    safe: bool = typer.Option(
        False, "--safe", help="Read-only; signals auto-approval for agent harnesses"
    ),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
) -> None:
    """Read file content. Outputs raw content to stdout for piping. Exit codes: 0=success, 1=error, 2=auth failure."""
    api_key = _get_api_key(key, BOSSA_API_BASE)
    url = f"{BOSSA_API_BASE}/api/v1/files"
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.get(url, headers=_api_headers(api_key), params={"path": path})
    _handle_response(resp)
    data = resp.json()
    content = data.get("content", "")
    if _json_mode(json_output):
        console.print(json.dumps({"path": path, "content": content}))
    else:
        sys.stdout.write(content)
        if content and not content.endswith("\n"):
            sys.stdout.write("\n")


@files_app.command("stat")
def stat_cmd(
    path: str = typer.Argument(..., help="File path"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    safe: bool = typer.Option(
        False, "--safe", help="Read-only; signals auto-approval for agent harnesses"
    ),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
) -> None:
    """Show file metadata: size, modified, created. Exit codes: 0=success, 1=error, 2=auth failure."""
    api_key = _get_api_key(key, BOSSA_API_BASE)
    url = f"{BOSSA_API_BASE}/api/v1/files/stat"
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.get(url, headers=_api_headers(api_key), params={"path": path})
    _handle_response(resp)
    data = resp.json()
    if _json_mode(json_output):
        console.print(json.dumps(data))
    else:
        console.print(f"Path: {data.get('path', path)}")
        console.print(f"Size: {data.get('size', 0)} bytes")
        console.print(f"Modified: {data.get('modified', '—')}")
        console.print(f"Created: {data.get('created', '—')}")


@files_app.command("tree")
def tree_cmd(
    path: str = typer.Argument("/", help="Directory path"),
    depth: int = typer.Option(
        None, "--depth", "-d", help="Max depth (default: unlimited)"
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    safe: bool = typer.Option(
        False, "--safe", help="Read-only; signals auto-approval for agent harnesses"
    ),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
) -> None:
    """Show directory tree. Exit codes: 0=success, 1=error, 2=auth failure."""
    api_key = _get_api_key(key, BOSSA_API_BASE)
    url = f"{BOSSA_API_BASE}/api/v1/files/tree"
    params: dict = {"path": path}
    if depth is not None:
        params["depth"] = depth
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.get(url, headers=_api_headers(api_key), params=params)
    _handle_response(resp)
    data = resp.json()
    tree_text = data.get("tree", "")
    if _json_mode(json_output):
        console.print(json.dumps({"tree": tree_text}))
    else:
        console.print(tree_text)


@files_app.command("du")
def du_cmd(
    path: str = typer.Argument("/", help="Directory path"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    safe: bool = typer.Option(
        False, "--safe", help="Read-only; signals auto-approval for agent harnesses"
    ),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
) -> None:
    """Show disk usage per directory. Exit codes: 0=success, 1=error, 2=auth failure."""
    api_key = _get_api_key(key, BOSSA_API_BASE)
    url = f"{BOSSA_API_BASE}/api/v1/files/du"
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.get(url, headers=_api_headers(api_key), params={"path": path})
    _handle_response(resp)
    data = resp.json()
    usage = data.get("usage", [])
    if _json_mode(json_output):
        console.print(json.dumps({"usage": usage}))
    else:
        for item in usage:
            console.print(f"{item['size']:>10}  {item['path']}")


@files_app.command("delete")
def delete_cmd(
    path: str = typer.Argument(..., help="File path to delete"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
) -> None:
    """Delete a file. Exit codes: 0=success, 1=error, 2=auth failure."""
    api_key = _get_api_key(key, BOSSA_API_BASE)
    url = f"{BOSSA_API_BASE}/api/v1/files"
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.delete(url, headers=_api_headers(api_key), params={"path": path})
    _handle_response(resp)
    data = resp.json()
    if _json_mode(json_output):
        console.print(json.dumps({"path": path, "deleted": True}))
    else:
        console.print(f"[green]Deleted {path}[/green]")


@files_app.command("write")
def write_cmd(
    path: str = typer.Argument(..., help="File path to write"),
    content: str = typer.Option(
        None, "--content", "-c", help="Content (or read from stdin)"
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
) -> None:
    """Write file content. Reads from stdin if --content not provided. Exit codes: 0=success, 1=error, 2=auth failure."""
    if content is None:
        content = sys.stdin.read()
    api_key = _get_api_key(key, BOSSA_API_BASE)
    url = f"{BOSSA_API_BASE}/api/v1/files"
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.post(
            url,
            headers=_api_headers(api_key),
            json={"path": path, "content": content},
        )
    _handle_response(resp)
    if _json_mode(json_output):
        console.print(json.dumps({"path": path, "wrote": True}))
    else:
        console.print(f"[green]Wrote {path}[/green]")


@files_app.command("grep")
def grep_cmd(
    pattern: str = typer.Argument(
        None, help="Pattern to search for (optional if using --all-of/--any-of)"
    ),
    path: str = typer.Option("/", "--path", "-p", help="Directory to scope search"),
    regex: bool = typer.Option(False, "--regex", help="Treat pattern as regex"),
    case_sensitive: bool = typer.Option(
        False, "--case-sensitive", help="Case-sensitive match"
    ),
    whole_word: bool = typer.Option(
        False, "--whole-word", help="Match whole words only"
    ),
    output_mode: str = typer.Option(
        "matches",
        "--output-mode",
        "-o",
        help="matches | files_with_matches | count",
    ),
    max_matches: int = typer.Option(100, "--max-matches", help="Max results"),
    offset: int = typer.Option(0, "--offset", help="Pagination offset"),
    all_of: list[str] = typer.Option([], "--all-of", help="All terms must match (AND)"),
    any_of: list[str] = typer.Option(
        [], "--any-of", help="At least one term must match (OR)"
    ),
    none_of: list[str] = typer.Option(
        [], "--none-of", help="Exclude lines matching any"
    ),
    context_before: int = typer.Option(
        0, "--context-before", help="Lines before each match"
    ),
    context_after: int = typer.Option(
        0, "--context-after", help="Lines after each match"
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    safe: bool = typer.Option(
        False, "--safe", help="Read-only; signals auto-approval for agent harnesses"
    ),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
) -> None:
    """Search file contents. Exit codes: 0=success, 1=error, 2=auth failure."""
    if not pattern and not all_of and not any_of and not none_of:
        console.print("[red]Provide pattern or --all-of/--any-of/--none-of[/red]")
        raise typer.Exit(1)
    api_key = _get_api_key(key, BOSSA_API_BASE)
    url = f"{BOSSA_API_BASE}/api/v1/files/search"
    payload = {
        "path": path,
        "regex": regex,
        "case_sensitive": case_sensitive,
        "whole_word": whole_word,
        "output_mode": output_mode,
        "max_matches": max_matches,
        "offset": offset,
        "all_of": all_of,
        "any_of": any_of,
        "none_of": none_of,
        "context_before": context_before,
        "context_after": context_after,
    }
    if pattern is not None:
        payload["pattern"] = pattern
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.post(url, headers=_api_headers(api_key), json=payload)
    _handle_response(resp)
    data = resp.json()
    if _json_mode(json_output):
        console.print(json.dumps(data))
    else:
        if data.get("output_mode") == "matches":
            for m in data.get("matches", []):
                console.print(f"{m['path']}:{m['line_number']}:{m['line']}")
        elif data.get("output_mode") == "files_with_matches":
            for f in data.get("files", []):
                console.print(f)
        elif data.get("output_mode") == "count":
            console.print(f"Count: {data.get('count', 0)}")


@files_app.command("glob")
def glob_cmd(
    pattern: str = typer.Argument(..., help="Glob pattern (e.g. *.md)"),
    path: str = typer.Option("/", "--path", "-p", help="Directory to scope search"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    safe: bool = typer.Option(
        False, "--safe", help="Read-only; signals auto-approval for agent harnesses"
    ),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
) -> None:
    """Find files matching glob pattern. Exit codes: 0=success, 1=error, 2=auth failure."""
    api_key = _get_api_key(key, BOSSA_API_BASE)
    url = f"{BOSSA_API_BASE}/api/v1/files/glob"
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.get(
            url,
            headers=_api_headers(api_key),
            params={"pattern": pattern, "path": path},
        )
    _handle_response(resp)
    data = resp.json()
    paths = data.get("paths", [])
    if _json_mode(json_output):
        console.print(json.dumps({"paths": paths}))
    else:
        for p in paths:
            console.print(p)


@files_app.command("edit")
def edit_cmd(
    path: str = typer.Argument(..., help="File path to edit"),
    old_string: str = typer.Option(..., "--old", "-o", help="String to replace"),
    new_string: str = typer.Option(..., "--new", "-n", help="Replacement string"),
    replace_all: bool = typer.Option(
        False, "--all", "-a", help="Replace all occurrences"
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
) -> None:
    """Replace old_string with new_string in file. Use --all for replace-all. Exit codes: 0=success, 1=error, 2=auth failure."""
    api_key = _get_api_key(key, BOSSA_API_BASE)
    url = f"{BOSSA_API_BASE}/api/v1/files"
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.patch(
            url,
            headers=_api_headers(api_key),
            json={
                "path": path,
                "old_string": old_string,
                "new_string": new_string,
                "replace_all": replace_all,
            },
        )
    _handle_response(resp)
    if _json_mode(json_output):
        console.print(json.dumps({"path": path, "edited": True}))
    else:
        console.print(f"[green]Edited {path}[/green]")


@files_app.command("put")
def put_file(
    local_file: Path = typer.Argument(..., help="Local file to upload"),
    target: str = typer.Option(
        "/", "--target", "-t", help="Remote path (default: / + basename)"
    ),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
) -> None:
    """Upload a single file. Exit codes: 0=success, 1=error, 2=auth failure."""
    if not local_file.exists():
        console.print(f"[red]File not found: {local_file}[/red]")
        raise typer.Exit(1)
    if not local_file.is_file():
        console.print(f"[red]Not a file: {local_file}[/red]")
        raise typer.Exit(1)

    api_key = _get_api_key(key, BOSSA_API_BASE)
    remote_path = target.rstrip("/") if target != "/" else "/"
    if remote_path == "/" or remote_path.endswith("/"):
        remote_path = (remote_path + local_file.name).replace("//", "/")

    content = local_file.read_text(encoding="utf-8", errors="replace")
    url = f"{BOSSA_API_BASE}/api/v1/files"
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.post(
            url,
            headers=_api_headers(api_key),
            json={"path": remote_path, "content": content},
        )
    if resp.status_code != 200:
        console.print(f"[red]Error {resp.status_code}: {resp.text}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Uploaded {local_file} -> {remote_path}[/green]")


def _collect_files(local_path: Path, include_hidden: bool) -> list[Path]:
    """Recursively collect regular files, optionally including hidden."""
    files: list[Path] = []
    if local_path.is_file():
        return [local_path]
    for p in local_path.rglob("*"):
        if not p.is_file():
            continue
        if not include_hidden and any(part.startswith(".") for part in p.parts):
            continue
        files.append(p)
    return sorted(files)


@files_app.command("batch")
def batch_cmd(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
) -> None:
    """Execute batch ops from stdin (one JSON object per line). Ops: read, write, delete. Exit codes: 0=success, 1=error, 2=auth failure."""
    api_key = _get_api_key(key, BOSSA_API_BASE)
    lines = sys.stdin.read().strip().split("\n")
    ops: list[dict] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            op = json.loads(line)
            if "op" not in op or "path" not in op:
                console.print(f"[red]Invalid op: {line}[/red]")
                raise typer.Exit(1)
            ops.append(op)
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON: {e}[/red]")
            raise typer.Exit(1)
    if not ops:
        console.print("[red]No ops provided[/red]")
        raise typer.Exit(1)
    if len(ops) > 100:
        console.print("[red]Max 100 ops per batch[/red]")
        raise typer.Exit(1)
    url = f"{BOSSA_API_BASE}/api/v1/files/batch"
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.post(url, headers=_api_headers(api_key), json={"ops": ops})
    _handle_response(resp)
    data = resp.json()
    results = data.get("results", [])
    if _json_mode(json_output):
        console.print(json.dumps({"results": results}))
    else:
        for r in results:
            if "error" in r:
                console.print(f"[red]{r['op']} {r['path']}: {r['error']}[/red]")
            elif r.get("op") == "read":
                content = r.get("content", "")
                preview = content[:80] + "..." if len(content) > 80 else content
                console.print(f"[green]read {r['path']}:[/green] {preview}")
            else:
                console.print(f"[green]{r['op']} {r['path']}: ok[/green]")


@files_app.command("upload")
def upload_files(
    local_path: Path = typer.Argument(..., help="Directory or file to upload"),
    target: str = typer.Option("/", "--target", "-t", help="Remote path prefix"),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
    include_hidden: bool = typer.Option(
        False, "--include-hidden", help="Include hidden files"
    ),
) -> None:
    """Upload a directory or file (bulk). Exit codes: 0=success, 1=error, 2=auth failure."""
    if not local_path.exists():
        console.print(f"[red]Path not found: {local_path}[/red]")
        raise typer.Exit(1)

    api_key = _get_api_key(key, BOSSA_API_BASE)
    files_list = _collect_files(local_path, include_hidden)
    if not files_list:
        console.print("[yellow]No files to upload[/yellow]")
        return

    target_prefix = target.rstrip("/") or "/"
    if target_prefix != "/" and not target_prefix.startswith("/"):
        target_prefix = "/" + target_prefix

    base = local_path if local_path.is_dir() else local_path.parent
    batch_size = 50
    total_created = 0
    total_updated = 0
    total_failed = 0

    for i in range(0, len(files_list), batch_size):
        batch = files_list[i : i + batch_size]
        payload_files: list[dict] = []
        for fp in batch:
            try:
                content = fp.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                console.print(f"[red]Skip {fp}: {e}[/red]")
                total_failed += 1
                continue
            rel = fp.relative_to(base)
            parts = list(rel.parts)
            remote_path = (
                target_prefix + "/" + "/".join(parts)
                if target_prefix != "/"
                else "/" + "/".join(parts)
            )
            remote_path = remote_path.replace("//", "/")
            payload_files.append({"path": remote_path, "content": content})

        if not payload_files:
            continue

        url = f"{BOSSA_API_BASE}/api/v1/files/bulk"
        with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
            resp = client.post(
                url,
                headers=_api_headers(api_key),
                json={"files": payload_files},
            )
        if resp.status_code != 200:
            console.print(f"[red]Error {resp.status_code}: {resp.text}[/red]")
            total_failed += len(payload_files)
            continue

        data = resp.json()
        total_created += data.get("created", 0)
        total_updated += data.get("updated", 0)
        total_failed += len(data.get("failed", []))

    console.print(f"[green]Uploaded {total_created + total_updated} files[/green]")
    if total_failed:
        console.print(f"[yellow]{total_failed} failed[/yellow]")
