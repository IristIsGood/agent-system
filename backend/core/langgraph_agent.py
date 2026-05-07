"""
LangGraph Agent - 用 LangGraph 重构 Agent 流程
"""

import logging
import json
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
import operator
import os

logger = logging.getLogger(__name__)


# 定义 Agent 状态
class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    tools_used: List[str]
    iterations: int


def create_langgraph_agent(tool_service):
    """创建 LangGraph Agent"""

    # 定义工具
    @tool
    def search_web(query: str) -> str:
        """Search the web for information"""
        return tool_service.execute("search_web", {"query": query})

    @tool
    def get_weather(city: str) -> str:
        """Get weather for a city"""
        return tool_service.execute("get_weather", {"city": city})

    @tool
    def calculate(operation: str, a: float, b: float) -> float:
        """Calculate math: operation can be add/subtract/multiply/divide"""
        return tool_service.execute("calculate", {"operation": operation, "a": a, "b": b})

    tools = [search_web, get_weather, calculate]

    # 初始化 LLM
    llm = ChatOpenAI(
        model=os.getenv("MODEL_TYPE", "gpt-4"),
        api_key=os.getenv("OPENAI_API_KEY"),
        streaming=True
    )
    llm_with_tools = llm.bind_tools(tools)

    # 定义节点

    def llm_node(state: AgentState) -> AgentState:
        """LLM 节点 - 决定下一步"""
        logger.info(f"🤖 LLM Node - 消息数: {len(state['messages'])}")
        response = llm_with_tools.invoke(state["messages"])
        return {
            "messages": [response],
            "tools_used": state["tools_used"],
            "iterations": state["iterations"] + 1
        }

    def tool_node_func(state: AgentState) -> AgentState:
        """工具节点 - 执行工具"""
        last_message = state["messages"][-1]
        tool_calls = last_message.tool_calls
        tools_used = list(state["tools_used"])

        results = []
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tools_used.append(tool_name)

            logger.info(f"🔧 执行工具: {tool_name}, 参数: {tool_args}")

            try:
                if tool_name == "search_web":
                    result = tool_service.execute("search_web", {"query": tool_args["query"]})
                elif tool_name == "get_weather":
                    result = tool_service.execute("get_weather", {"city": tool_args["city"]})
                elif tool_name == "calculate":
                    result = tool_service.execute("calculate", tool_args)
                else:
                    result = f"Unknown tool: {tool_name}"
            except Exception as e:
                result = f"Tool error: {str(e)}"

            results.append(ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            ))

        return {
            "messages": results,
            "tools_used": tools_used,
            "iterations": state["iterations"]
        }

    def should_continue(state: AgentState) -> str:
        """决定继续还是结束"""
        last_message = state["messages"][-1]

        # 超过最大迭代次数
        if state["iterations"] >= 10:
            return "end"

        # 有工具调用 → 继续
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        # 没有工具调用 → 结束
        return "end"

    # 构建图
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("llm", llm_node)
    workflow.add_node("tools", tool_node_func)

    # 添加边
    workflow.set_entry_point("llm")
    workflow.add_conditional_edges(
        "llm",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    workflow.add_edge("tools", "llm")

    # 编译
    app = workflow.compile()
    logger.info("✅ LangGraph Agent 创建成功")

    return app


class LangGraphAgentExecutor:
    """LangGraph Agent 执行器"""

    def __init__(self, tool_service):
        self.tool_service = tool_service
        self.graph = create_langgraph_agent(tool_service)
        logger.info("✅ LangGraphAgentExecutor 初始化成功")

    def execute(self, task: str, history: List[Dict] = []) -> Dict[str, Any]:
        """执行任务"""
        logger.info(f"🚀 LangGraph Agent 执行: {task}")

        # 构建消息列表
        messages = [
            SystemMessage(content="""You are a helpful AI Agent.
You can use tools to complete tasks. Use search_web for current information,
calculate for math, and get_weather for weather.
Reply in the same language as the user.""")
        ]

        # 加入历史记录
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # 加入当前任务
        messages.append(HumanMessage(content=task))

        # 执行图
        result = self.graph.invoke({
            "messages": messages,
            "tools_used": [],
            "iterations": 0
        })

        # 获取最终回答
        final_message = result["messages"][-1]
        final_content = final_message.content if hasattr(final_message, "content") else str(final_message)

        return {
            "status": "success",
            "result": final_content,
            "iterations": result["iterations"],
            "tools_used": result["tools_used"]
        }

    def stream(self, task: str, history: List[Dict] = []):
        """流式执行任务"""
        import json

        messages = [
            SystemMessage(content="""You are a helpful AI Agent.
You can use tools to complete tasks. Use search_web for current information,
calculate for math, and get_weather for weather.
Reply in the same language as the user.""")
        ]

        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=task))

        # 流式执行
        for event in self.graph.stream({
            "messages": messages,
            "tools_used": [],
            "iterations": 0
        }):
            for node_name, node_output in event.items():
                if node_name == "tools":
                    # 工具执行事件
                    tools = node_output.get("tools_used", [])
                    if tools:
                        yield json.dumps({
                            "type": "tool_used",
                            "tool": tools[-1]
                        }) + "\n"

                elif node_name == "llm":
                    # LLM 输出事件
                    msgs = node_output.get("messages", [])
                    if msgs:
                        last = msgs[-1]
                        # 有工具调用
                        if hasattr(last, "tool_calls") and last.tool_calls:
                            for tc in last.tool_calls:
                                yield json.dumps({
                                    "type": "tool_calling",
                                    "tool": tc["name"],
                                    "args": tc["args"]
                                }) + "\n"
                        # 最终回答
                        elif hasattr(last, "content") and last.content:
                            yield json.dumps({
                                "type": "answer",
                                "content": last.content
                            }) + "\n"