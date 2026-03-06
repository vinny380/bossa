"""Bossa CLI entry point."""

from pathlib import Path

# Load .env before any module reads config (works for both 'bossa' and 'python -m cli')
try:
    from dotenv import load_dotenv
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")
except ImportError:
    pass

import typer

from cli.auth_commands import login, logout, signup, whoami
from cli.keys import keys_app
from cli.workspaces import workspaces_app

app = typer.Typer(name="bossa", help="Bossa filesystem CLI")

app.command("login")(login)
app.command("signup")(signup)
app.command("logout")(logout)
app.command("whoami")(whoami)
app.add_typer(workspaces_app, name="workspaces")
app.add_typer(keys_app, name="keys")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
