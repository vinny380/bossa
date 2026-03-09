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
from rich.console import Console
from rich.rule import Rule
from rich.text import Text

from cli.auth_commands import login, logout, signup, whoami
from cli.files import files_app
from cli.keys import keys_app
from cli.workspace_context import workspace_app
from cli.workspaces import workspaces_app

console = Console()


def _print_banner() -> None:
    tagline = Text()
    tagline.append("Bossa", style="bold cyan")
    tagline.append(" — ", style="dim")
    tagline.append("long-term memory for AI agents", style="italic")
    console.print(Rule(tagline, style="dim"))


app = typer.Typer(
    name="bossa",
    help="Bossa filesystem CLI",
    add_completion=False,
    no_args_is_help=True,
)


@app.callback()
def _callback(_: typer.Context) -> None:
    """Long-term memory for AI agents — ls, read, write, grep, glob."""
    _print_banner()


app.command("login")(login)
app.command("signup")(signup)
app.command("logout")(logout)
app.command("whoami")(whoami)
app.add_typer(workspaces_app, name="workspaces")
app.add_typer(workspace_app, name="workspace")
app.add_typer(keys_app, name="keys")
app.add_typer(files_app, name="files")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
