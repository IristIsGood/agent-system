"""
Agent 相关的 API 路由
"""

import logging
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.models.schemas import TaskRequest, TaskResponse
from backend.services.llm_service import LLMService
from backend.services.tool_service import tool_service
from backend.core.agent_executor import AgentExecutor
from backend.core.task_planner import TaskPlanner
from backend.core.multi_agent import MultiAgentSystem
from backend.core.langgraph_agent import LangGraphAgentExecutor
from backend.core.mcp_client import MCPClient, MCPAgentExecutor
import os

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/api/agent", tags=["agent"])

# 初始化服务（这些会在应用启动时创建）
llm_service = None
agent_executor = None
task_planner = None
multi_agent_system = None
mcp_executor = None


def init_services():
    """初始化服务"""
    global llm_service, agent_executor, task_planner, multi_agent_system, langgraph_executor, mcp_executor
    
    try:
        llm_service = LLMService()
        agent_executor = AgentExecutor(llm_service, tool_service)
        task_planner = TaskPlanner(llm_service)
        multi_agent_system = MultiAgentSystem(llm_service, tool_service)
        langgraph_executor = LangGraphAgentExecutor(tool_service)

                # MCP Client
        mcp_server_path = os.path.join(os.path.dirname(__file__), "..", "mcp_server.py")
        mcp_server_path = os.path.abspath(mcp_server_path)
        mcp_client = MCPClient(mcp_server_path)
        mcp_executor = MCPAgentExecutor(llm_service, mcp_client)

        logger.info("✅ 所有服务初始化成功")
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {str(e)}")
        raise


@router.post("/execute", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    if not agent_executor:
        raise HTTPException(status_code=500, detail="Agent executor not initialized")
    
    try:
        # 把历史记录转成 AI 能读的格式
        history = [{"role": m.role, "content": m.content} for m in request.history]
        
        result = agent_executor.execute(request.task, history=history)
        
        return TaskResponse(
            status=result["status"],
            result=result["result"],
            iterations=result["iterations"]
        )
        
    except Exception as e:
        logger.error(f"❌ 执行任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")


@router.post("/stream")
async def stream_task(request: TaskRequest):
    if not llm_service or not agent_executor:
        raise HTTPException(status_code=500, detail="Services not initialized")

    def generate():
        history = [{"role": m.role, "content": m.content} for m in request.history]

        # 第一步：用 AgentExecutor 执行工具调用（非流式）
        # 但我们只跑工具部分，不要最后的回答
        messages = [
            {
                "role": "system",
                "content": """你是一个智能助手 Agent，可以帮用户完成各种任务。
你有以下工具可以使用：
- calculate: 进行数学计算
- get_weather: 查询指定城市的天气
- search_web: 搜索网络上的最新信息

规则：
1. 需要最新信息或不确定的内容，使用 search_web 搜索
2. 涉及数学计算，使用 calculate
3. 查询天气，使用 get_weather
4. 根据用户的语言回答，用户用中文就用中文，用英文就用英文，用其他语言也跟着用
5. 直接给出有用的答案，不要拒绝正常的问题"""
            }
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": request.task})

        # 工具调用循环
        for iteration in range(10):
            response = llm_service.chat_with_tools(
                messages=messages,
                tools=tool_service.get_tools_for_llm()
            )

            # 没有工具调用 → 用流式输出最终答案
            if not response["tool_calls"]:
                # 把之前的思考内容加进去，流式输出最终回答
                final_messages = messages + []
                if response["content"]:
                    # 已经有答案了，直接流式输出
                    for chunk in llm_service.chat_stream(final_messages):
                        yield chunk
                else:
                    for chunk in llm_service.chat_stream(final_messages):
                        yield chunk
                break

            # 有工具调用 → 执行工具
            assistant_message = {
                "role": "assistant",
                "content": response["content"] or "",
                "tool_calls": response["tool_calls"]
            }
            messages.append(assistant_message)

            for tool_call in response["tool_calls"]:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                try:
                    tool_result = tool_service.execute(tool_name, tool_args)
                except Exception as e:
                    tool_result = f"错误: {str(e)}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result)
                })

    return StreamingResponse(generate(), media_type="text/plain")

@router.get("/tools")
async def list_tools():
    """
    列出所有可用的工具
    """
    
    try:
        tools = tool_service.list_tools()
        return {
            "total": len(tools),
            "tools": tools
        }
        
    except Exception as e:
        logger.error(f"❌ 获取工具列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/plan")
async def plan_and_execute(request: TaskRequest):
    if not task_planner or not llm_service:
        raise HTTPException(status_code=500, detail="Services not initialized")

    def generate():
        import json
        history = [{"role": m.role, "content": m.content} for m in request.history]

        # 第一步：规划任务，发送状态
        yield json.dumps({"type": "status", "message": "🗺️ Planning tasks..."}) + "\n"
        tasks = task_planner.plan(request.task)

        # 发送任务列表
        yield json.dumps({"type": "tasks", "tasks": tasks}) + "\n"

        # 第二步：逐个执行子任务，实时发送进度
        results = []
        for task in tasks:
            icon = {"search": "🔍", "weather": "🌤️", "calculate": "🔢", "answer": "💡"}.get(task["type"], "⚡")
            yield json.dumps({"type": "executing", "task_id": task["id"], "message": f"{icon} {task['description']}"}) + "\n"

            result = {"task": task, "result": ""}
            try:
                if task["type"] == "search":
                    result["result"] = tool_service.execute("search_web", {"query": task["query"]})
                elif task["type"] == "weather":
                    result["result"] = tool_service.execute("get_weather", {"city": task["query"]})
                elif task["type"] == "calculate":
                    result["result"] = task["query"]
                elif task["type"] == "answer":
                    result["result"] = ""
            except Exception as e:
                result["result"] = f"Failed: {str(e)}"

            results.append(result)
            yield json.dumps({"type": "done", "task_id": task["id"], "result": result["result"][:200]}) + "\n"

        # 第三步：整合结果，流式输出最终回答
        yield json.dumps({"type": "status", "message": "💡 Generating final answer..."}) + "\n"

        context = "\n\n".join([
            f"Task {r['task']['id']}: {r['task']['description']}\nResult: {r['result']}"
            for r in results if r['result']
        ])

        messages = [
            {
                "role": "system",
                "content": """You are a helpful assistant. Consolidate all collected information into a clear, complete answer.
Reply in the same language as the user."""
            }
        ]
        messages.extend(history)
        messages.append({
            "role": "user",
            "content": f"Task: {request.task}\n\nCollected info:\n{context}\n\nPlease provide a complete answer."
        })

        # 流式输出最终回答
        yield json.dumps({"type": "answer_start"}) + "\n"
        for chunk in llm_service.chat_stream(messages):
            yield json.dumps({"type": "answer_chunk", "chunk": chunk}) + "\n"
        yield json.dumps({"type": "answer_end"}) + "\n"

    return StreamingResponse(generate(), media_type="text/plain")


@router.post("/multi")
async def multi_agent_execute(request: TaskRequest):
    if not multi_agent_system:
        raise HTTPException(status_code=500, detail="Services not initialized")

    def generate():
        history = [{"role": m.role, "content": m.content} for m in request.history]
        for chunk in multi_agent_system.run_stream(request.task, history):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")


@router.post("/langgraph")
async def langgraph_execute(request: TaskRequest):
    if not langgraph_executor:
        raise HTTPException(status_code=500, detail="LangGraph executor not initialized")

    def generate():
        history = [{"role": m.role, "content": m.content} for m in request.history]
        for chunk in langgraph_executor.stream(request.task, history):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")


@router.post("/mcp")
async def mcp_execute(request: TaskRequest):
    if not llm_service:
        raise HTTPException(status_code=500, detail="Services not initialized")

    try:
        history = [{"role": m.role, "content": m.content} for m in request.history]
        
        # 直接用 tool_service，但走标准 MCP 格式
        tools = tool_service.get_tools_for_llm()
        
        messages = [
            {
                "role": "system",
                "content": """You are a helpful AI Agent using MCP tools.
Use search_web for current information, calculate for math, get_weather for weather.
Reply in the same language as the user."""
            }
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": request.task})

        tools_used = []
        for iteration in range(10):
            response = llm_service.chat_with_tools(messages=messages, tools=tools)

            assistant_message = {
                "role": "assistant",
                "content": response["content"] or ""
            }
            if response["tool_calls"]:
                assistant_message["tool_calls"] = response["tool_calls"]
            messages.append(assistant_message)

            if not response["tool_calls"]:
                return {
                    "status": "success",
                    "result": response["content"],
                    "iterations": iteration + 1,
                    "tools_used": tools_used
                }

            for tool_call in response["tool_calls"]:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                tools_used.append(tool_name)

                try:
                    result = tool_service.execute(tool_name, tool_args)
                except Exception as e:
                    result = f"Error: {str(e)}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })

        return {"status": "failed", "result": "Max iterations reached", "iterations": 10, "tools_used": tools_used}

    except Exception as e:
        logger.error(f"❌ MCP 执行失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))