"""
Pydantic 数据模型定义
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class TaskRequest(BaseModel):
    """任务请求"""
    task: str


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