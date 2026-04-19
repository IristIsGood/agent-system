"""
Agent 相关的 API 路由
"""

import logging
from fastapi import APIRouter, HTTPException
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
    """
    执行 Agent 任务
    
    Args:
        request: 任务请求 {"task": "..."}
    
    Returns:
        {
            "status": "success" 或 "failed",
            "result": "结果",
            "iterations": 迭代次数
        }
    """
    
    if not agent_executor:
        raise HTTPException(
            status_code=500,
            detail="Agent executor not initialized"
        )
    
    try:
        result = agent_executor.execute(request.task)
        
        return TaskResponse(
            status=result["status"],
            result=result["result"],
            iterations=result["iterations"]
        )
        
    except Exception as e:
        logger.error(f"❌ 执行任务失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Task execution failed: {str(e)}"
        )


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