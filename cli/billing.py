"""Billing commands: upgrade to Pro, manage subscription."""

import webbrowser

import httpx
import typer
from rich.console import Console

from cli.auth import require_auth
from cli.config import BOSSA_API_BASE, BOSSA_TIMEOUT

console = Console()
billing_app = typer.Typer(help="Billing and subscription")


def _billing_post(path: str, token: str, **kwargs) -> httpx.Response:
    """POST to billing API. Caller handles response."""
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        return client.post(
            f"{BOSSA_API_BASE}/api/v1/billing/{path}",
            headers={"Authorization": f"Bearer {token}"},
            **kwargs,
        )


@billing_app.command("upgrade")
def upgrade(
    interval: str = typer.Option("month", "--interval", "-i", help="month or year"),
) -> None:
    """Open Stripe Checkout to upgrade to Pro."""
    token = require_auth()
    resp = _billing_post("checkout", token, params={"interval": interval})
    if resp.status_code == 503:
        console.print("[red]Billing not available.[/red]")
        raise typer.Exit(1)
    if resp.status_code != 200:
        console.print(f"[red]Error: {resp.status_code} {resp.text}[/red]")
        raise typer.Exit(1)
    data = resp.json()
    checkout_url = data.get("checkout_url")
    if not checkout_url:
        console.print("[red]No checkout URL returned.[/red]")
        raise typer.Exit(1)
    webbrowser.open(checkout_url)
    console.print(
        "[green]Opened checkout in browser. Complete payment to upgrade to Pro.[/green]"
    )


@billing_app.command("manage")
def manage() -> None:
    """Open Stripe Customer Portal to manage subscription (payment, invoices, cancel)."""
    token = require_auth()
    resp = _billing_post("portal", token)
    if resp.status_code == 200:
        data = resp.json()
        url = data.get("url")
        if url:
            webbrowser.open(url)
            console.print("[green]Opened billing portal in browser.[/green]")
        else:
            console.print("[red]No portal URL returned.[/red]")
            raise typer.Exit(1)
    elif resp.status_code == 400:
        detail = resp.json().get(
            "detail", "No billing account. Run 'bossa billing upgrade' first."
        )
        console.print(f"[red]{detail}[/red]")
        raise typer.Exit(1)
    elif resp.status_code == 503:
        console.print("[red]Billing not available.[/red]")
        raise typer.Exit(1)
    else:
        console.print(f"[red]Error: {resp.status_code} {resp.text}[/red]")
        raise typer.Exit(1)
