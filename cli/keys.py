"""API key commands."""

import httpx
import typer
from rich.console import Console
from rich.table import Table

from cli.auth import get_access_token
from cli.config import BOSSA_API_URL, BOSSA_TIMEOUT
from cli.workspace_context import set_active_workspace

console = Console()
keys_app = typer.Typer(help="Manage API keys")


def _require_auth() -> str:
    token = get_access_token()
    if not token:
        console.print("[red]Not logged in. Run 'bossa login' first.[/red]")
        raise typer.Exit(1)
    return token


def _resolve_workspace_id(token: str, workspace: str) -> str:
    """Resolve workspace name to ID, or return as-is if already UUID."""
    if len(workspace) == 36 and workspace.count("-") == 4:
        return workspace
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.get(
            f"{BOSSA_API_URL.rstrip('/')}/api/v1/workspaces",
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


@keys_app.command("create")
def create_key(
    workspace: str = typer.Argument(..., help="Workspace name or ID"),
    name: str = typer.Option("default", "--name", "-n", help="Key name"),
    save: bool = typer.Option(
        False, "--save", "-s", help="Save key to config as active workspace"
    ),
) -> None:
    """Create an API key. Copy it now; it won't be shown again."""
    token = _require_auth()
    workspace_id = _resolve_workspace_id(token, workspace)
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.post(
            f"{BOSSA_API_URL.rstrip('/')}/api/v1/workspaces/{workspace_id}/keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": name},
        )
    if resp.status_code != 200:
        console.print(f"[red]Error: {resp.status_code} {resp.text}[/red]")
        raise typer.Exit(1)
    data = resp.json()
    if save:
        set_active_workspace(workspace, workspace_id, data["key"])
        console.print(
            f"[green]Key created and saved. Active workspace: {workspace}[/green]"
        )
    else:
        console.print(
            "[yellow]API key created. Copy it now; it won't be shown again:[/yellow]"
        )
    console.print(f"[bold]{data['key']}[/bold]")


@keys_app.command("list")
def list_keys(
    workspace: str = typer.Argument(..., help="Workspace name or ID"),
) -> None:
    """List API keys for a workspace."""
    token = _require_auth()
    workspace_id = _resolve_workspace_id(token, workspace)
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.get(
            f"{BOSSA_API_URL.rstrip('/')}/api/v1/workspaces/{workspace_id}/keys",
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code != 200:
        console.print(f"[red]Error: {resp.status_code} {resp.text}[/red]")
        raise typer.Exit(1)
    data = resp.json()
    if not data:
        console.print("[dim]No API keys[/dim]")
        return
    table = Table(title="API Keys")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Created")
    for k in data:
        table.add_row(k["id"], k["name"], k.get("created_at", ""))
    console.print(table)


@keys_app.command("revoke")
def revoke_key(
    workspace: str = typer.Argument(..., help="Workspace name or ID"),
    key_id: str = typer.Argument(..., help="Key ID to revoke"),
) -> None:
    """Revoke an API key."""
    token = _require_auth()
    workspace_id = _resolve_workspace_id(token, workspace)
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.delete(
            f"{BOSSA_API_URL.rstrip('/')}/api/v1/workspaces/{workspace_id}/keys/{key_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code != 200:
        console.print(f"[red]Error: {resp.status_code} {resp.text}[/red]")
        raise typer.Exit(1)
    console.print("[green]Key revoked[/green]")
