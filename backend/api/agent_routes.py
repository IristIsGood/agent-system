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

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/api/agent", tags=["agent"])

# 初始化服务（这些会在应用启动时创建）
llm_service = None
agent_executor = None


def init_services():
    """初始化服务"""
    global llm_service, agent_executor
    
    try:
        llm_service = LLMService()
        agent_executor = AgentExecutor(llm_service, tool_service)
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
    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service not initialized")

    def generate():
        # 把历史记录转成 AI 能读的格式
        history = [{"role": m.role, "content": m.content} for m in request.history]

        # 组建完整消息列表
        messages = [
            {
                "role": "system",
                "content": """你是一个智能助手 Agent。
        你可以使用以下工具来完成任务：
        - calculate: 进行数学计算
        - get_weather: 查询天气
        - search_web: 搜索网络信息

        使用工具时，只需要给出工具名称和参数。
        完成任务后，给出最终答案。"""
            }
        ]

        messages.extend(history)
        messages.append({"role": "user", "content": request.task})

        # 流式输出每个字
        for chunk in llm_service.chat_stream(messages):
            yield chunk

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