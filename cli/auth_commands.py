"""Auth commands: login, logout, whoami."""

import typer
from rich.console import Console

from cli.auth import clear_credentials, get_access_token, save_credentials
from cli.config import SUPABASE_ANON_KEY, SUPABASE_URL

console = Console()


def _require_supabase_config() -> None:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        console.print(
            "[red]Set SUPABASE_URL and SUPABASE_ANON_KEY in your environment.[/red]"
        )
        raise typer.Exit(1)


def signup(
    email: str = typer.Option(..., prompt=True, help="Email address"),
    password: str = typer.Option(..., prompt=True, hide_input=True, help="Password (min 6 chars)"),
) -> None:
    """Create an account with Supabase Auth (email + password)."""
    _require_supabase_config()
    from supabase import create_client

    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    try:
        response = client.auth.sign_up({"email": email, "password": password})
    except Exception as e:
        console.print(f"[red]Signup failed: {e}[/red]")
        raise typer.Exit(1)
    if response.user:
        console.print(f"[green]Account created for {response.user.email}[/green]")
        if response.session:
            save_credentials(
                access_token=response.session.access_token,
                refresh_token=response.session.refresh_token or "",
                expires_at=response.session.expires_at,
            )
            console.print("[green]Logged in. You can now use workspaces and keys commands.[/green]")
        else:
            console.print(
                "[yellow]Check your email to confirm. Then run 'bossa login'.[/yellow]"
            )
    else:
        console.print("[red]Signup failed: no user returned[/red]")
        raise typer.Exit(1)


def login(
    email: str = typer.Option(..., prompt=True, help="Email address"),
    password: str = typer.Option(..., prompt=True, hide_input=True, help="Password"),
) -> None:
    """Log in with Supabase Auth (email + password)."""
    _require_supabase_config()
    from supabase import create_client

    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    try:
        response = client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        console.print(f"[red]Login failed: {e}[/red]")
        raise typer.Exit(1)
    session = response.session
    if not session:
        console.print("[red]Login failed: no session returned[/red]")
        raise typer.Exit(1)
    save_credentials(
        access_token=session.access_token,
        refresh_token=session.refresh_token or "",
        expires_at=session.expires_at,
    )
    user = response.user
    email = user.email if user else "unknown"
    console.print(f"[green]Logged in as {email}[/green]")


def logout() -> None:
    """Clear stored credentials."""
    clear_credentials()
    console.print("[green]Logged out[/green]")


def whoami() -> None:
    """Show current user (from stored token)."""
    token = get_access_token()
    if not token:
        console.print("[yellow]Not logged in. Run 'bossa login' first.[/yellow]")
        raise typer.Exit(1)
    # Decode JWT to get email (no verification needed for display)
    import base64
    import json
    parts = token.split(".")
    if len(parts) < 2:
        console.print("[red]Invalid token[/red]")
        raise typer.Exit(1)
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
    email = payload.get("email", "unknown")
    sub = payload.get("sub", "unknown")
    console.print(f"User: {email} (id: {sub})")
