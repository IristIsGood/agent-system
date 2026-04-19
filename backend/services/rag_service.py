"""
RAG 服务 - 知识库管理
"""

import os
import logging
from typing import List, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer
import pypdf
import markdown

logger = logging.getLogger(__name__)

class RAGService:
    
    def __init__(self):
        """初始化 RAG 服务"""
        # 初始化向量数据库
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection("knowledge_base")
        
        # 初始化 embedding 模型
        logger.info("⏳ 加载 embedding 模型...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("✅ RAG 服务初始化成功")
    
    def add_document(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """
        添加文档到知识库
        """
        # 读取文件内容
        content = self._read_file(file_path, file_name)
        
        # 切割成小块
        chunks = self._split_text(content)
        
        # 生成向量并存储
        for i, chunk in enumerate(chunks):
            doc_id = f"{file_name}_{i}"
            embedding = self.model.encode(chunk).tolist()
            
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{"source": file_name, "chunk": i}]
            )
        
        logger.info(f"✅ 文档已添加: {file_name}，共 {len(chunks)} 个片段")
        return {"file": file_name, "chunks": len(chunks)}
    
    def search(self, query: str, top_k: int = 3) -> List[str]:
        """
        搜索相关文档片段
        """
        query_embedding = self.model.encode(query).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count())
        )
        
        if not results["documents"][0]:
            return []
        
        return results["documents"][0]
    
    def list_documents(self) -> List[str]:
        """
        列出所有已上传的文档
        """
        results = self.collection.get()
        sources = set()
        for meta in results["metadatas"]:
            sources.add(meta["source"])
        return list(sources)
    
    def _read_file(self, file_path: str, file_name: str) -> str:
        """读取文件内容"""
        ext = file_name.lower().split(".")[-1]
        
        if ext == "pdf":
            reader = pypdf.PdfReader(file_path)
            return "\n".join(page.extract_text() for page in reader.pages)
        
        elif ext in ["md", "markdown"]:
            with open(file_path, "r", encoding="utf-8") as f:
                md_content = f.read()
            # 转成纯文本
            html = markdown.markdown(md_content)
            import re
            return re.sub(r"<[^>]+>", "", html)
        
        else:  # txt 等纯文本
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
    
    def _split_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """把长文本切割成小块"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
        return chunks


# 全局单例
rag_service = RAGService()