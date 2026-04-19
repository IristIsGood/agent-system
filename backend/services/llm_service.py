"""
LLM 服务 - 与 OpenAI API 交互
"""

import os
import logging
from typing import List, Dict, Any, Optional, Generator
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class LLMService:
    """
    OpenAI LLM 服务类
    """
    
    def __init__(self):
        """初始化 LLM 服务"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 环境变量未设置")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("MODEL_TYPE", "gpt-4")
        logger.info(f"✅ LLMService 初始化成功，使用模型: {self.model}")
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        简单聊天
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
        
        Returns:
            LLM 的回复
        """
        try:
            logger.info(f"📝 调用 LLM (非流式)，消息数: {len(messages)}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            result = response.choices[0].message.content
            logger.info(f"✅ LLM 回复成功")
            return result
            
        except Exception as e:
            logger.error(f"❌ LLM 调用失败: {str(e)}")
            raise
    
    def chat_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """
        流式聊天 - 逐字返回结果
        
        Args:
            messages: 消息列表
        
        Yields:
            LLM 的回复（逐字）
        """
        try:
            logger.info(f"📝 调用 LLM (流式)，消息数: {len(messages)}")
            
            with self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=1000
            ) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"❌ 流式调用失败: {str(e)}")
            raise
    
    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        支持工具调用的聊天
        
        Args:
            messages: 消息列表
            tools: 工具定义列表（OpenAI Function Calling 格式）
        
        Returns:
            LLM 的响应（包含可能的工具调用）
        """
        try:
            logger.info(f"📝 调用 LLM（带工具），消息数: {len(messages)}, 工具数: {len(tools) if tools else 0}")
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            response = self.client.chat.completions.create(**kwargs)
            
            result = response.choices[0].message
            logger.info(f"✅ LLM 回复成功")
            
            return {
                "content": result.content or "",
                "tool_calls": result.tool_calls if hasattr(result, 'tool_calls') else None,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            logger.error(f"❌ LLM 调用失败: {str(e)}")
            raise