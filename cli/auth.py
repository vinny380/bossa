"""CLI auth: credential storage."""

import json
from pathlib import Path

import typer
from rich.console import Console

from cli.config import CREDENTIALS_PATH


def load_credentials() -> dict | None:
    """Load stored credentials. Returns None if not logged in."""
    if not CREDENTIALS_PATH.exists():
        return None
    try:
        data = json.loads(CREDENTIALS_PATH.read_text())
        if not data.get("access_token"):
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None


def save_credentials(
    access_token: str, refresh_token: str, expires_at: int | None = None
) -> None:
    """Save credentials to disk."""
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at,
    }
    CREDENTIALS_PATH.write_text(json.dumps(data, indent=2))


def clear_credentials() -> None:
    """Remove stored credentials."""
    if CREDENTIALS_PATH.exists():
        CREDENTIALS_PATH.unlink()


def get_access_token() -> str | None:
    """Get current access token, or None if not logged in."""
    creds = load_credentials()
    return creds.get("access_token") if creds else None


def require_auth() -> str:
    """Get access token or exit with error if not logged in."""
    token = get_access_token()
    if not token:
        Console().print("[red]Not logged in. Run 'bossa login' first.[/red]")
        raise typer.Exit(1)
    return token
