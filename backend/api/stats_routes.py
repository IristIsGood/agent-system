"""
数据统计 API
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from backend.core.database import get_db, CallLog
from backend.api.auth_routes import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stats", tags=["stats"])

# GPT-4 pricing (per 1K tokens)
PROMPT_PRICE = 0.03
COMPLETION_PRICE = 0.06


class LogRequest(BaseModel):
    token: str
    mode: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    response_time: float = 0
    tools_used: str = ""


@router.post("/log")
def log_call(request: LogRequest, db: Session = Depends(get_db)):
    """记录一次调用"""
    user_id = verify_token(request.token)

    log = CallLog(
        user_id=user_id,
        mode=request.mode,
        prompt_tokens=request.prompt_tokens,
        completion_tokens=request.completion_tokens,
        total_tokens=request.total_tokens,
        response_time=request.response_time,
        tools_used=request.tools_used
    )
    db.add(log)
    db.commit()

    return {"status": "logged"}


@router.get("/dashboard")
def get_dashboard(token: str, days: int = 7, db: Session = Depends(get_db)):
    """获取看板数据"""
    user_id = verify_token(token)

    since = datetime.utcnow() - timedelta(days=days)
    logs = db.query(CallLog).filter(
        CallLog.user_id == user_id,
        CallLog.created_at >= since
    ).all()

    if not logs:
        return {
            "total_calls": 0,
            "total_tokens": 0,
            "total_cost": 0,
            "avg_response_time": 0,
            "by_mode": {},
            "by_day": [],
            "tools_used": {},
            "recent_logs": []
        }

    # 基础统计
    total_calls = len(logs)
    total_tokens = sum(l.total_tokens for l in logs)
    total_cost = sum(
        (l.prompt_tokens * PROMPT_PRICE + l.completion_tokens * COMPLETION_PRICE) / 1000
        for l in logs
    )
    avg_response_time = sum(l.response_time for l in logs) / total_calls

    # 按模式统计
    by_mode = {}
    for log in logs:
        by_mode[log.mode] = by_mode.get(log.mode, 0) + 1

    # 按天统计
    by_day = {}
    for log in logs:
        day = log.created_at.strftime("%m/%d")
        by_day[day] = by_day.get(day, 0) + 1
    by_day_list = [{"date": k, "calls": v} for k, v in sorted(by_day.items())]

    # 工具使用统计
    tools_used = {}
    for log in logs:
        if log.tools_used:
            for tool in log.tools_used.split(","):
                tool = tool.strip()
                if tool:
                    tools_used[tool] = tools_used.get(tool, 0) + 1

    # 最近10条记录
    recent = sorted(logs, key=lambda x: x.created_at, reverse=True)[:10]
    recent_logs = [
        {
            "mode": l.mode,
            "tokens": l.total_tokens,
            "response_time": round(l.response_time, 2),
            "tools": l.tools_used,
            "created_at": l.created_at.strftime("%m/%d %H:%M")
        }
        for l in recent
    ]

    return {
        "total_calls": total_calls,
        "total_tokens": total_tokens,
        "total_cost": round(total_cost, 4),
        "avg_response_time": round(avg_response_time, 2),
        "by_mode": by_mode,
        "by_day": by_day_list,
        "tools_used": tools_used,
        "recent_logs": recent_logs
    }