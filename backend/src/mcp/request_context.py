"""Capture HTTP request for MCP tool invocations.

Streamable HTTP tool calls may run in a context where FastMCP's CurrentHeaders
returns empty. We capture the request at connection time and use it as fallback.
"""

from contextvars import ContextVar

from starlette.requests import Request

# Request captured by middleware for /mcp paths; used when CurrentHeaders is empty.
_captured_request: ContextVar[Request | None] = ContextVar(
    "mcp_captured_request",
    default=None,
)


def get_captured_request() -> Request | None:
    """Get the request captured at connection time, or None."""
    return _captured_request.get()


def get_headers_from_captured_request() -> dict[str, str]:
    """Extract headers from the captured request, or empty dict."""
    request = get_captured_request()
    if request is None:
        return {}
    return {k: str(v) for k, v in request.headers.items()}
