"""LangChain agent that connects to Bossa MCP server and does context discovery."""
import asyncio

from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent


async def main() -> None:
    client = MultiServerMCPClient({
        "bossa": {
            "url": "http://localhost:8000/mcp",
            "transport": "http",
        }
    })
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
        print("="*60)
        messages.append(HumanMessage(content=query))
        response = await agent.ainvoke({"messages": messages})
        for msg in response["messages"]:
            if hasattr(msg, "content") and msg.content:
                text = str(msg.content)[:500]
                print(f"{getattr(msg, 'type', 'ASSISTANT').upper()}: {text}")
        messages = list(response["messages"])


if __name__ == "__main__":
    asyncio.run(main())
