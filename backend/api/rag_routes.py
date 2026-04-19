"""
RAG 相关的 API 路由
"""

import os
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from backend.services.rag_service import rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["rag"])

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class QueryRequest(BaseModel):
    query: str
    top_k: int = 3


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    上传文档到知识库
    """
    # 检查文件类型
    allowed = ["pdf", "txt", "md", "markdown"]
    ext = file.filename.lower().split(".")[-1]
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}，支持: {allowed}")
    
    # 保存文件
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # 添加到知识库
    try:
        result = rag_service.add_document(file_path, file.filename)
        return {"status": "success", "message": f"文档已上传", "detail": result}
    except Exception as e:
        logger.error(f"❌ 添加文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_knowledge(request: QueryRequest):
    """
    搜索知识库
    """
    try:
        results = rag_service.search(request.query, request.top_k)
        return {
            "query": request.query,
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"❌ 搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents():
    """
    列出所有已上传的文档
    """
    try:
        docs = rag_service.list_documents()
        return {"total": len(docs), "documents": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))