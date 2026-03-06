"""File upload commands."""

import os
from pathlib import Path

import httpx
import typer
from rich.console import Console

from cli.config import BOSSA_API_URL

console = Console()
files_app = typer.Typer(help="Upload files to Bossa")


def _get_api_key(key: str | None, base_url: str) -> str:
    """Resolve API key from arg, BOSSA_API_KEY env, or sk-default for localhost."""
    if key:
        return key
    if "localhost" in base_url:
        return "sk-default"
    env_key = os.environ.get("BOSSA_API_KEY", "").strip()
    if not env_key:
        console.print("[red]Set BOSSA_API_KEY in .env or use --key[/red]")
        raise typer.Exit(1)
    return env_key


def _api_headers(key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {key}", "X-API-Key": key}


@files_app.command("put")
def put_file(
    local_file: Path = typer.Argument(..., help="Local file to upload"),
    target: str = typer.Option(
        "/", "--target", "-t", help="Remote path (default: / + basename)"
    ),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
) -> None:
    """Upload a single file."""
    if not local_file.exists():
        console.print(f"[red]File not found: {local_file}[/red]")
        raise typer.Exit(1)
    if not local_file.is_file():
        console.print(f"[red]Not a file: {local_file}[/red]")
        raise typer.Exit(1)

    api_key = _get_api_key(key, BOSSA_API_URL)
    remote_path = target.rstrip("/") if target != "/" else "/"
    if remote_path == "/" or remote_path.endswith("/"):
        remote_path = (remote_path + local_file.name).replace("//", "/")

    content = local_file.read_text(encoding="utf-8", errors="replace")
    url = f"{BOSSA_API_URL.rstrip('/')}/api/v1/files"
    with httpx.Client() as client:
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


@files_app.command("upload")
def upload_files(
    local_path: Path = typer.Argument(..., help="Directory or file to upload"),
    target: str = typer.Option("/", "--target", "-t", help="Remote path prefix"),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
    include_hidden: bool = typer.Option(
        False, "--include-hidden", help="Include hidden files"
    ),
) -> None:
    """Upload a directory or file (bulk)."""
    if not local_path.exists():
        console.print(f"[red]Path not found: {local_path}[/red]")
        raise typer.Exit(1)

    api_key = _get_api_key(key, BOSSA_API_URL)
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

        url = f"{BOSSA_API_URL.rstrip('/')}/api/v1/files/bulk"
        with httpx.Client() as client:
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
