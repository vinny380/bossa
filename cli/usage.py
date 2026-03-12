"""Usage command: show account usage and limits."""

import json
from datetime import datetime, timedelta, timezone

import httpx
import typer
from rich.box import DOUBLE
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from cli.config import BOSSA_API_BASE, BOSSA_TIMEOUT
from cli.files import _api_headers, _get_api_key, _handle_response, _json_mode

console = Console()


def _pct_bar(pct: float, width: int = 10) -> tuple[str, str]:
    """Return (bar_string, color) for usage percentage. Color: green <80%, yellow 80-99%, red >=100%."""
    if pct >= 100:
        style = "red"
    elif pct >= 80:
        style = "yellow"
    else:
        style = "green"
    filled = min(int(pct / 100 * width), width)
    bar = "█" * filled + "░" * (width - filled)
    return bar, style


def _format_usage_row(
    metric: str,
    used: float | int,
    limit: float | int,
    unit: str,
    is_owner: bool,
) -> tuple[str, str, str, str, str]:
    """Return (used_str, limit_str, pct_str, bar, remaining_str) for table row."""
    if is_owner or limit <= 0:
        return (
            str(used),
            "unlimited" if is_owner else str(limit),
            "N/A",
            "░" * 10,
            "—" if is_owner else str(max(0, int(limit) - int(used))),
        )
    pct = (used / limit * 100) if limit else 0
    remaining = max(0, limit - used)
    if "MB" in unit or "storage" in metric.lower():
        used_str = f"{used:.2f} MB"
        limit_str = f"{limit:.2f} MB"
        remaining_str = f"{remaining:.2f} MB left"
    elif "request" in metric.lower():
        used_str = f"{int(used):,}"
        limit_str = f"{int(limit):,}"
        remaining_str = f"{int(remaining):,} left"
    else:
        used_str = f"{int(used):,}"
        limit_str = f"{int(limit):,}"
        remaining_str = f"{int(remaining):,} left"
    pct_str = f"{pct:.1f}%"
    bar, _ = _pct_bar(pct)
    return used_str, limit_str, pct_str, bar, remaining_str


def _build_usage_panel(data: dict) -> Panel:
    """Build Rich Panel with usage table."""
    tier = data.get("tier", "free")
    limits = data.get("limits", {})
    storage_mb = data.get("storage_mb", 0)
    files_count = data.get("files_count", 0)
    requests_today = data.get("requests_today", 0)
    limit_storage = limits.get("storage_mb", 100)
    limit_files = limits.get("files", 500)
    limit_requests = limits.get("requests_per_day", 1000)
    is_owner = tier == "owner"

    table = Table(show_header=True, header_style="bold", box=None, expand=False)
    table.add_column("Metric", style="dim", min_width=14, no_wrap=True)
    table.add_column("Used", justify="right")
    table.add_column("Limit", justify="right")
    table.add_column("%", justify="right")
    table.add_column("Bar")
    table.add_column("Remaining", justify="right")

    # Storage row
    used_s, lim_s, pct_s, bar, rem_s = _format_usage_row(
        "storage_mb", storage_mb, limit_storage, "MB", is_owner
    )
    pct_val = (
        (storage_mb / limit_storage * 100) if limit_storage and not is_owner else 0
    )
    _, bar_style = _pct_bar(pct_val)
    table.add_row("storage_mb", used_s, lim_s, pct_s, f"[{bar_style}]{bar}[/]", rem_s)

    # Files row
    used_s, lim_s, pct_s, bar, rem_s = _format_usage_row(
        "files_count", files_count, limit_files, "", is_owner
    )
    pct_val = (files_count / limit_files * 100) if limit_files and not is_owner else 0
    _, bar_style = _pct_bar(pct_val)
    table.add_row("files_count", used_s, lim_s, pct_s, f"[{bar_style}]{bar}[/]", rem_s)

    # Requests row
    used_s, lim_s, pct_s, bar, rem_s = _format_usage_row(
        "requests", requests_today, limit_requests, "", is_owner
    )
    pct_val = (
        (requests_today / limit_requests * 100)
        if limit_requests and not is_owner
        else 0
    )
    _, bar_style = _pct_bar(pct_val)
    table.add_row("requests", used_s, lim_s, pct_s, f"[{bar_style}]{bar}[/]", rem_s)

    # Storage bytes (raw)
    storage_bytes = int(storage_mb * 1_000_000)
    table.add_row("storage_bytes", f"{storage_bytes:,}", "—", "—", "—", "—")

    # Reset info (single line below table to avoid wrapping)
    now = datetime.now(timezone.utc)
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if now.hour or now.minute or now.second or now.microsecond:
        tomorrow += timedelta(days=1)
    reset_str = tomorrow.strftime("%Y-%m-%d 00:00 UTC")

    near_limit = False
    if not is_owner:
        for used, lim in [
            (storage_mb, limit_storage),
            (files_count, limit_files),
            (requests_today, limit_requests),
        ]:
            if lim and (used / lim) >= 0.8:
                near_limit = True
                break

    reset_line = Text.from_markup(f"[dim]reset: requests at {reset_str}[/dim]")
    if near_limit:
        content = Group(
            table,
            "",
            reset_line,
            "",
            Text.from_markup(
                "[yellow]Near limit. Upgrade: bossa billing upgrade[/yellow]"
            ),
        )
    else:
        content = Group(table, "", reset_line)

    return Panel(
        content,
        title=f"Usage · {tier}",
        subtitle=f"tier: {tier}",
        box=DOUBLE,
        border_style="blue",
    )


def _enrich_json(data: dict) -> dict:
    """Add computed fields for JSON output."""
    limits = data.get("limits", {})
    limit_storage = limits.get("storage_mb", 100)
    limit_files = limits.get("files", 500)
    limit_requests = limits.get("requests_per_day", 1000)
    storage_mb = data.get("storage_mb", 0)
    files_count = data.get("files_count", 0)
    requests_today = data.get("requests_today", 0)
    tier = data.get("tier", "free")
    is_owner = tier == "owner"

    out = dict(data)
    out["storage_bytes"] = int(storage_mb * 1_000_000)

    if is_owner:
        out["pct_storage"] = 0
        out["pct_files"] = 0
        out["pct_requests"] = 0
        out["remaining_storage_mb"] = float("inf")
        out["remaining_files"] = float("inf")
        out["remaining_requests"] = float("inf")
    else:
        out["pct_storage"] = (
            round((storage_mb / limit_storage * 100), 2) if limit_storage else 0
        )
        out["pct_files"] = (
            round((files_count / limit_files * 100), 2) if limit_files else 0
        )
        out["pct_requests"] = (
            round((requests_today / limit_requests * 100), 2) if limit_requests else 0
        )
        out["remaining_storage_mb"] = round(max(0, limit_storage - storage_mb), 2)
        out["remaining_files"] = max(0, limit_files - files_count)
        out["remaining_requests"] = max(0, limit_requests - requests_today)

    now = datetime.now(timezone.utc)
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if now.hour or now.minute or now.second or now.microsecond:
        tomorrow += timedelta(days=1)
    out["reset_utc"] = tomorrow.strftime("%Y-%m-%dT%H:%M:%SZ")

    return out


def usage(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    key: str = typer.Option(None, "--key", "-k", help="API key (or BOSSA_API_KEY)"),
) -> None:
    """Show account usage and limits. Exit codes: 0=success, 1=error, 2=auth failure."""
    api_key = _get_api_key(key, BOSSA_API_BASE)
    url = f"{BOSSA_API_BASE}/api/v1/usage"
    with httpx.Client(timeout=BOSSA_TIMEOUT) as client:
        resp = client.get(url, headers=_api_headers(api_key))
    _handle_response(resp)
    data = resp.json()

    if _json_mode(json_output):
        enriched = _enrich_json(data)
        console.print(json.dumps(enriched))
    else:
        panel = _build_usage_panel(data)
        console.print(panel)
