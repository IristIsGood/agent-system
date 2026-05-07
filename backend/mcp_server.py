"""
MCP Server - 提供标准化工具接口
"""

import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 MCP Server
server = Server("agent-system-tools")


@server.list_tools()
async def list_tools():
    """列出所有可用工具"""
    return [
        Tool(
            name="search_web",
            description="Search the web for current information",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_weather",
            description="Get current weather for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="calculate",
            description="Perform math calculations",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "Math operation"
                    },
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                "required": ["operation", "a", "b"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """执行工具"""
    logger.info(f"🔧 MCP 执行工具: {name}, 参数: {arguments}")

    try:
        if name == "search_web":
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(arguments["query"], max_results=3))
            if not results:
                result = f"No results found for '{arguments['query']}'"
            else:
                output = f"Search results for '{arguments['query']}':\n\n"
                for i, r in enumerate(results, 1):
                    output += f"{i}. {r['title']}\n{r['body']}\n\n"
                result = output

        elif name == "get_weather":
            import requests
            url = f"https://wttr.in/{arguments['city']}?format=3&lang=en"
            response = requests.get(url, timeout=5)
            result = response.text.strip() if response.status_code == 200 else f"Weather unavailable for {arguments['city']}"

        elif name == "calculate":
            op = arguments["operation"]
            a, b = arguments["a"], arguments["b"]
            if op == "add": result = str(a + b)
            elif op == "subtract": result = str(a - b)
            elif op == "multiply": result = str(a * b)
            elif op == "divide": result = str(a / b) if b != 0 else "Error: division by zero"
            else: result = f"Unknown operation: {op}"

        else:
            result = f"Unknown tool: {name}"

    except Exception as e:
        result = f"Tool error: {str(e)}"

    logger.info(f"✅ MCP 工具结果: {result[:100]}")
    return [TextContent(type="text", text=result)]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())