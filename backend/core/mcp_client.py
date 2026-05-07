"""
MCP Client - 通过 MCP 协议调用工具
"""

import asyncio
import logging
import json
from typing import List, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP 客户端 - 连接 MCP Server 并调用工具"""

    def __init__(self, server_script: str):
        """
        初始化 MCP Client
        server_script: MCP Server 的路径
        """
        self.server_script = server_script
        self.tools = []
        logger.info(f"✅ MCPClient 初始化，Server: {server_script}")

    async def get_tools(self) -> List[Dict]:
        """获取所有可用工具"""
        server_params = StdioServerParameters(
            command="python",
            args=[self.server_script]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                self.tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.inputSchema
                        }
                    }
                    for t in tools.tools
                ]
                logger.info(f"✅ 获取到 {len(self.tools)} 个 MCP 工具")
                return self.tools

    async def call_tool(self, tool_name: str, arguments: Dict) -> str:
        """调用指定工具"""
        server_params = StdioServerParameters(
            command="python",
            args=[self.server_script]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                content = result.content[0].text if result.content else ""
                logger.info(f"✅ MCP 工具 {tool_name} 结果: {content[:100]}")
                return content

    def call_tool_sync(self, tool_name: str, arguments: Dict) -> str:
        """同步版本的工具调用"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.call_tool(tool_name, arguments))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"❌ MCP 工具调用失败: {str(e)}")
            return f"Error: {str(e)}"

    def get_tools_sync(self) -> List[Dict]:
        """同步版本的获取工具"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.get_tools())
            loop.close()
            return result
        except Exception as e:
            logger.error(f"❌ 获取 MCP 工具失败: {str(e)}")
            return []


class MCPAgentExecutor:
    """使用 MCP 工具的 Agent 执行器"""

    def __init__(self, llm_service, mcp_client: MCPClient):
        self.llm = llm_service
        self.mcp = mcp_client
        logger.info("✅ MCPAgentExecutor 初始化成功")

    def execute(self, task: str, history: List[Dict] = []) -> Dict[str, Any]:
        """执行任务"""
        logger.info(f"🚀 MCP Agent 执行: {task}")

        # 获取 MCP 工具
        tools = self.mcp.get_tools_sync()
        if not tools:
            logger.warning("⚠️ 没有获取到 MCP 工具，使用无工具模式")

        messages = [
            {
                "role": "system",
                "content": """You are a helpful AI Agent using MCP tools.
Use search_web for current information, calculate for math, get_weather for weather.
Reply in the same language as the user."""
            }
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": task})

        # Agent Loop
        tools_used = []
        for iteration in range(10):
            logger.info(f"📍 迭代 {iteration + 1}")

            response = self.llm.chat_with_tools(messages=messages, tools=tools)

            assistant_message = {
                "role": "assistant",
                "content": response["content"] or ""
            }

            if response["tool_calls"]:
                assistant_message["tool_calls"] = response["tool_calls"]

            messages.append(assistant_message)

            # 没有工具调用 → 完成
            if not response["tool_calls"]:
                logger.info("✅ MCP Agent 完成任务")
                return {
                    "status": "success",
                    "result": response["content"],
                    "iterations": iteration + 1,
                    "tools_used": tools_used
                }

            # 执行 MCP 工具
            import json
            for tool_call in response["tool_calls"]:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                tools_used.append(tool_name)

                logger.info(f"🔧 调用 MCP 工具: {tool_name}")
                result = self.mcp.call_tool_sync(tool_name, tool_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

        return {
            "status": "failed",
            "result": "Max iterations reached",
            "iterations": 10,
            "tools_used": tools_used
        }