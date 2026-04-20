"""
Pydantic 数据模型定义
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class Message(BaseModel):
    """单条消息"""
    role: str        # "user" 或 "assistant"
    content: str     # 消息内容


class TaskRequest(BaseModel):
    """任务请求"""
    task: str
    history: List[Message] = []   # 对话历史，默认空列表


class TaskResponse(BaseModel):
    """任务响应"""
    status: str
    result: str
    iterations: int


class ToolInfo(BaseModel):
    """工具信息"""
    name: str
    description: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    message: str