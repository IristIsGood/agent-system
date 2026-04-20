"""
Agent 执行引擎 - Agent Loop 的核心
"""

import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class AgentExecutor:
    """
    Agent 执行器 - 实现 Agent Loop
    """
    
    def __init__(self, llm_service, tool_service):
        """
        初始化 Agent 执行器
        
        Args:
            llm_service: LLM 服务实例
            tool_service: 工具服务实例
        """
        self.llm = llm_service
        self.tools = tool_service
        self.max_iterations = 10
        
        logger.info("✅ AgentExecutor 初始化成功")
    

    def execute(self, user_task: str, history: List[Dict] = []) -> Dict[str, Any]:
        """
        执行 Agent - 核心 Loop
        
        流程：
        1. 接收用户任务
        2. 初始化消息列表
        3. 循环：
           a. 调用 LLM（提供可用工具）
           b. LLM 决定是否需要工具
           c. 如果需要，执行工具
           d. 把结果反馈给 LLM
           e. 重复直到完成或达到最大迭代次数
        
        Args:
            user_task: 用户的任务描述
        
        Returns:
            {
                "status": "success" 或 "failed",
                "result": 最终结果,
                "iterations": 迭代次数,
                "messages": 完整的消息历史
            }
        """
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 开始执行 Agent 任务")
        logger.info(f"📌 任务: {user_task}")
        logger.info(f"{'='*60}\n")
        
        # 初始化消息列表
        messages = [
        {
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

        # 加入历史记录
        messages.extend(history)

        # 加入当前任务
        messages.append({
            "role": "user",
            "content": user_task
        })
        
        # Agent Loop
        for iteration in range(self.max_iterations):
            logger.info(f"\n📍 迭代 {iteration + 1}/{self.max_iterations}")
            
            # 1. 调用 LLM
            logger.info(f"🤖 调用 LLM...")
            response = self.llm.chat_with_tools(
                messages=messages,
                tools=self.tools.get_tools_for_llm()
            )
            
            # 2. 添加 LLM 响应到消息列表
            assistant_message = {
                "role": "assistant",
                "content": response["content"] or "",
            }
            
            if response["tool_calls"]:
                assistant_message["tool_calls"] = response["tool_calls"]
            
            messages.append(assistant_message)
            
            # 打印 LLM 的思考过程
            if response["content"]:
                logger.info(f"💭 LLM 思考: {response['content'][:100]}...")
            
            # 3. 检查是否有工具调用
            if not response["tool_calls"]:
                # 没有工具调用，任务完成
                logger.info(f"\n✅ Agent 完成任务！")
                logger.info(f"📌 最终答案: {response['content']}")
                
                return {
                    "status": "success",
                    "result": response["content"],
                    "iterations": iteration + 1,
                    "messages": messages
                }
            
            # 4. 执行工具
            for tool_call in response["tool_calls"]:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"🔧 执行工具: {tool_name}")
                logger.info(f"   参数: {tool_args}")
                
                try:
                    # 执行工具
                    tool_result = self.tools.execute(tool_name, tool_args)
                    logger.info(f"✅ 工具结果: {tool_result}")
                    
                except Exception as e:
                    tool_result = f"错误: {str(e)}"
                    logger.error(f"❌ 工具执行失败: {tool_result}")
                
                # 5. 把工具结果加入消息列表
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result)
                })
        
        # 超过最大迭代次数
        logger.error(f"\n❌ Agent 在 {self.max_iterations} 次迭代后仍未完成")
        
        return {
            "status": "failed",
            "result": f"Agent 在 {self.max_iterations} 次迭代后仍未完成任务",
            "iterations": self.max_iterations,
            "messages": messages
        }