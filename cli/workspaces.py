"""Workspace commands."""

import httpx
import typer
from rich.console import Console
from rich.table import Table

from cli.auth import get_access_token
from cli.config import BOSSA_API_URL

console = Console()
workspaces_app = typer.Typer(help="Manage workspaces")


def _require_auth() -> str:
    token = get_access_token()
    if not token:
        console.print("[red]Not logged in. Run 'bossa login' first.[/red]")
        raise typer.Exit(1)
    return token


@workspaces_app.command("list")
def list_workspaces() -> None:
    """List your workspaces."""
    token = _require_auth()
    with httpx.Client() as client:
        resp = client.get(
            f"{BOSSA_API_URL.rstrip('/')}/api/v1/workspaces",
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code != 200:
        console.print(f"[red]Error: {resp.status_code} {resp.text}[/red]")
        raise typer.Exit(1)
    data = resp.json()
    if not data:
        console.print(
            "[dim]No workspaces. Create one with 'bossa workspaces create <name>'[/dim]"
        )
        return
    table = Table(title="Workspaces")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    for w in data:
        table.add_row(w["id"], w["name"])
    console.print(table)


@workspaces_app.command("create")
def create_workspace(name: str = typer.Argument(..., help="Workspace name")) -> None:
    """Create a workspace."""
    token = _require_auth()
    with httpx.Client() as client:
        resp = client.post(
            f"{BOSSA_API_URL.rstrip('/')}/api/v1/workspaces",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": name},
        )
    if resp.status_code != 200:
        console.print(f"[red]Error: {resp.status_code} {resp.text}[/red]")
        raise typer.Exit(1)
    data = resp.json()
    console.print(
        f"[green]Created workspace '{data['name']}' (id: {data['id']})[/green]"
    )
