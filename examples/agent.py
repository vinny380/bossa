"""LangChain agent that connects to Bossa MCP server and does context discovery."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient


def _bossa_headers() -> dict[str, str]:
    """Headers for Bossa MCP (API key for workspace)."""
    key = os.environ.get("BOSSA_API_KEY", "sk-default")
    return {"X-API-Key": key, "Authorization": f"Bearer {key}"}


async def main() -> None:
    client = MultiServerMCPClient(
        {
            "bossa": {
                "url": os.environ.get("BOSSA_URL", "http://localhost:8000/mcp"),
                "transport": "streamable_http",
                "headers": _bossa_headers(),
            }
        }
    )
    tools = await client.get_tools()

    agent = create_agent("openai:gpt-4o", tools)

    queries = [
        "What data is available? Explore the filesystem.",
        "Find all Enterprise-tier customers.",
        "Read the details of the first Enterprise customer you found.",
        "Save a summary of your findings to /memory/analysis.md",
    ]

    messages = []
    for query in queries:
        print(f"\n{'='*60}")
        print(f"USER: {query}")
        print("=" * 60)
        messages.append(HumanMessage(content=query))
        response = await agent.ainvoke({"messages": messages})
        for msg in response["messages"]:
            if hasattr(msg, "content") and msg.content:
                text = str(msg.content)[:500]
                print(f"{getattr(msg, 'type', 'ASSISTANT').upper()}: {text}")
        messages = list(response["messages"])


if __name__ == "__main__":
    asyncio.run(main())
