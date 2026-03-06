"""Interactive chat agent connected to Bossa MCP server."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient


def _bossa_headers(base: str) -> dict[str, str]:
    """Headers for Bossa MCP (API key for workspace)."""
    if "localhost" in base:
        key = "sk-default"
    else:
        key = os.environ.get("BOSSA_API_KEY", "").strip()
        if not key:
            raise SystemExit("Set BOSSA_API_KEY in .env for non-localhost")
    return {"X-API-Key": key, "Authorization": f"Bearer {key}"}


async def main() -> None:
    print("Connecting to Bossa...")
    base = os.environ.get("BOSSA_API_URL", "http://localhost:8000").strip().rstrip("/")
    mcp_url = f"{base}/mcp"
    client = MultiServerMCPClient(
        {
            "bossa": {
                "url": mcp_url,
                "transport": "streamable_http",
                "headers": _bossa_headers(base),
            }
        }
    )
    tools = await client.get_tools()
    agent = create_agent("openai:gpt-4o", tools)

    print(
        "\nBossa chat ready. You have access to the filesystem (ls, read_file, write_file, grep, etc.)."
    )
    print("Type your message and press Enter. 'quit' or 'exit' to stop.\n")

    messages = []
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Bye.")
            break

        messages.append(HumanMessage(content=user_input))
        print("Bossa: ", end="", flush=True)

        response = await agent.ainvoke({"messages": messages})
        messages = list(response["messages"])

        # Print the last assistant message
        for msg in reversed(response["messages"]):
            msg_type = getattr(msg, "type", "") or type(msg).__name__
            if (
                msg_type.lower() in ("ai", "aimessage")
                and hasattr(msg, "content")
                and msg.content
            ):
                text = msg.content
                if isinstance(text, list):
                    text = " ".join(
                        t.get("text", str(t)) if isinstance(t, dict) else str(t)
                        for t in text
                    )
                print(str(text))
                break
        print()


if __name__ == "__main__":
    asyncio.run(main())
