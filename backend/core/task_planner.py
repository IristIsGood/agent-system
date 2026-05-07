"""
任务规划器 - 把复杂任务拆解成子任务
"""

import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TaskPlanner:

    def __init__(self, llm_service):
        self.llm = llm_service
        logger.info("✅ TaskPlanner 初始化成功")

    def plan(self, user_task: str) -> List[Dict[str, Any]]:
        """
        把用户任务拆解成子任务列表
        """
        logger.info(f"🗺️ 开始规划任务: {user_task}")

        messages = [
            {
                "role": "system",
                "content": """You are a task planning expert.
                The user will give you a complex task. Break it down into 2-5 executable subtasks.

                Each subtask must be one of these types:
                - search: needs to search the web
                - calculate: needs math calculation
                - weather: needs weather info (query must be ONLY the city name, e.g. Shanghai, 上海, Tokyo)
                - answer: answer directly using existing knowledge, no tools needed

            Return ONLY JSON, no other content:
            {
            "tasks": [
                {"id": 1, "type": "search", "description": "Search top attractions in Shanghai", "query": "Shanghai top tourist attractions 2024"},
                {"id": 2, "type": "weather", "description": "Check Shanghai weather", "query": "Shanghai"},
                {"id": 3, "type": "answer", "description": "Compile the travel plan", "query": ""}
            ]
            }

            Rules:
            1. Simple tasks (one step) = 1 subtask only
            2. Complex tasks = 2-5 subtasks
            3. search query must be short and specific, 3-5 words
            4. weather query must be ONLY the city name, nothing else
            5. Last subtask is usually answer type to consolidate results
            6. Reply in the same language as the user"""
            },

            {
                "role": "user",
                "content": f"请拆解这个任务：{user_task}"
            }
        ]

        try:
            response = self.llm.chat(messages)
            # 清理 JSON
            clean = response.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            tasks = data["tasks"]
            logger.info(f"✅ 任务拆解完成，共 {len(tasks)} 个子任务")
            for t in tasks:
                logger.info(f"   {t['id']}. [{t['type']}] {t['description']}")
            return tasks
        except Exception as e:
            logger.error(f"❌ 任务规划失败: {str(e)}")
            # 失败时返回单个任务
            return [{"id": 1, "type": "answer", "description": user_task, "query": user_task}]

    def execute_plan(self, tasks: List[Dict], tool_service) -> List[Dict]:
        """
        执行所有子任务，收集结果
        """
        results = []

        for task in tasks:
            logger.info(f"⚡ 执行子任务 {task['id']}: {task['description']}")
            result = {"task": task, "result": ""}

            try:
                if task["type"] == "search":
                    result["result"] = tool_service.execute("search_web", {"query": task["query"]})

                elif task["type"] == "calculate":
                    # 从 query 里解析计算参数
                    result["result"] = task["query"]

                elif task["type"] == "weather":
                    result["result"] = tool_service.execute("get_weather", {"city": task["query"]})

                elif task["type"] == "answer":
                    result["result"] = ""  # 由 LLM 最终整合

            except Exception as e:
                result["result"] = f"执行失败: {str(e)}"

            results.append(result)
            logger.info(f"✅ 子任务完成: {result['result'][:100] if result['result'] else '待 LLM 整合'}")

        return results