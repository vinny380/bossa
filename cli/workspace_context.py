"""Workspace context: config load/save, active workspace, active key."""

import json
import os
from pathlib import Path

import httpx
import typer
from rich.console import Console

from cli.auth import get_access_token
from cli.config import BOSSA_API_BASE, BOSSA_TIMEOUT

console = Console()
workspace_app = typer.Typer(
    help="Set active workspace for files commands. Use 'bossa workspace use <name> --key sk-xxx' to avoid --key on every command."
)


def _config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))


def get_config_path() -> Path:
    """Path to config.json (same dir as credentials)."""
    return _config_home() / "bossa" / "config.json"


def load_config() -> dict:
    """Load config from ~/.config/bossa/config.json. Returns empty dict if missing."""
    path = get_config_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict) -> None:
    """Save config to ~/.config/bossa/config.json. Ensures dir exists, chmod 600."""
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2))
    try:
        path.chmod(0o600)
    except OSError:
        pass


def get_active_key() -> str | None:
    """Return active API key from config, or None if not set."""
    config = load_config()
    return config.get("active_key") or None


def get_active_workspace() -> str | None:
    """Return active workspace name from config, or None if not set."""
    config = load_config()
    return config.get("active_workspace") or None


def set_active_workspace(name: str, workspace_id: str, key: str) -> None:
    """Set active workspace and key in config. Updates workspaces map."""
    config = load_config()
    workspaces = config.get("workspaces") or {}
    workspaces[name] = {"id": workspace_id, "key": key}
    config["workspaces"] = workspaces
    config["active_workspace"] = name
    config["active_key"] = key
    save_config(config)


def get_workspace_key(name: str) -> str | None:
    """Return stored key for workspace name, or None."""
    config = load_config()
    workspaces = config.get("workspaces") or {}
    entry = workspaces.get(name)
    if entry and isinstance(entry, dict):
        return entry.get("key")
    return None


def get_workspace_id_from_config(name: str) -> str | None:
    """Return stored workspace id for name, or None."""
    config = load_config()
    workspaces = config.get("workspaces") or {}
    entry = workspaces.get(name)
    if entry and isinstance(entry, dict):
        return entry.get("id")
    return None


def _resolve_workspace_id(token: str, workspace: str) -> str:
    """Resolve workspace name to ID via API, or return as-is if UUID."""
    if len(workspace) == 36 and workspace.count("-") == 4:
        return workspace
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.get(
            f"{BOSSA_API_BASE}/api/v1/workspaces",
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code != 200:
        console.print(f"[red]Error: {resp.status_code} {resp.text}[/red]")
        raise typer.Exit(1)
    for w in resp.json():
        if w["name"] == workspace:
            return w["id"]
    console.print(f"[red]Workspace '{workspace}' not found[/red]")
    raise typer.Exit(1)


@workspace_app.command("use")
def workspace_use(
    name: str = typer.Argument(..., help="Workspace name to activate"),
    key: str = typer.Option(None, "--key", "-k", help="API key for this workspace"),
) -> None:
    """Set active workspace. Provide --key to store it, or use a previously stored key."""
    if key:
        # User provided key - store it
        workspace_id = ""
        token = get_access_token()
        if token:
            try:
                workspace_id = _resolve_workspace_id(token, name)
            except typer.Exit:
                raise
        set_active_workspace(name, workspace_id, key)
        console.print(f"[green]Active workspace: {name}[/green]")
    else:
        # No key - use stored key for this workspace
        stored_key = get_workspace_key(name)
        if not stored_key:
            console.print(
                f"[red]No key for workspace '{name}'. Run: bossa workspace use {name} --key <your-key>[/red]"
            )
            raise typer.Exit(1)
        config = load_config()
        config["active_workspace"] = name
        config["active_key"] = stored_key
        save_config(config)
        console.print(f"[green]Active workspace: {name}[/green]")


@workspace_app.command("current")
def workspace_current() -> None:
    """Show active workspace name."""
    active = get_active_workspace()
    if active:
        console.print(active)
    else:
        console.print(
            "[dim]No active workspace. Run: bossa workspace use <name> --key <key>[/dim]"
        )
