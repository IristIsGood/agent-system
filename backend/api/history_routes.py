"""
对话历史 API
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from backend.core.database import get_db, Conversation, Message
from backend.api.auth_routes import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/history", tags=["history"])


class SaveMessageRequest(BaseModel):
    token: str
    conversation_id: Optional[int] = None
    role: str
    content: str


class NewConversationRequest(BaseModel):
    token: str
    title: str = "新对话"


@router.post("/conversation")
def create_conversation(request: NewConversationRequest, db: Session = Depends(get_db)):
    """创建新对话"""
    user_id = verify_token(request.token)

    conversation = Conversation(user_id=user_id, title=request.title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {"conversation_id": conversation.id, "title": conversation.title}


@router.get("/conversations")
def list_conversations(token: str, db: Session = Depends(get_db)):
    """获取用户所有对话列表"""
    user_id = verify_token(token)

    conversations = db.query(Conversation)\
        .filter(Conversation.user_id == user_id)\
        .order_by(Conversation.created_at.desc())\
        .all()

    return {
        "conversations": [
            {"id": c.id, "title": c.title, "created_at": str(c.created_at)}
            for c in conversations
        ]
    }


@router.get("/messages/{conversation_id}")
def get_messages(conversation_id: int, token: str, db: Session = Depends(get_db)):
    """获取某个对话的所有消息"""
    user_id = verify_token(token)

    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    messages = db.query(Message)\
        .filter(Message.conversation_id == conversation_id)\
        .order_by(Message.created_at.asc())\
        .all()

    return {
        "conversation_id": conversation_id,
        "title": conversation.title,
        "messages": [
            {"role": m.role, "content": m.content, "created_at": str(m.created_at)}
            for m in messages
        ]
    }


@router.post("/message")
def save_message(request: SaveMessageRequest, db: Session = Depends(get_db)):
    """保存一条消息"""
    user_id = verify_token(request.token)

    # 如果没有 conversation_id，自动创建新对话
    if not request.conversation_id:
        conversation = Conversation(user_id=user_id, title=request.content[:20])
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conversation_id = conversation.id
    else:
        conversation_id = request.conversation_id

    message = Message(
        conversation_id=conversation_id,
        role=request.role,
        content=request.content
    )
    db.add(message)
    db.commit()

    return {"conversation_id": conversation_id, "status": "saved"}


@router.delete("/conversation/{conversation_id}")
def delete_conversation(conversation_id: int, token: str, db: Session = Depends(get_db)):
    """删除对话"""
    user_id = verify_token(token)

    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    db.query(Message).filter(Message.conversation_id == conversation_id).delete()
    db.delete(conversation)
    db.commit()

    return {"status": "deleted"}

class UpdateTitleRequest(BaseModel):
    token: str
    title: str

@router.put("/conversation/{conversation_id}/title")
def update_title(conversation_id: int, request: UpdateTitleRequest, db: Session = Depends(get_db)):
    """更新对话标题"""
    user_id = verify_token(request.token)

    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    conversation.title = request.title
    db.commit()

    return {"status": "updated", "title": request.title}