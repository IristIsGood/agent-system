"""
多 Agent 协作系统
"""

import json
import logging
from typing import List, Dict, Any, Generator

logger = logging.getLogger(__name__)


class BaseAgent:
    """基础 Agent"""

    def __init__(self, name: str, role: str, llm_service, tool_service=None):
        self.name = name
        self.role = role
        self.llm = llm_service
        self.tools = tool_service
        logger.info(f"✅ Agent 初始化: {name}")

    def run(self, task: str, context: str = "") -> str:
        raise NotImplementedError


class ResearchAgent(BaseAgent):
    """研究 Agent - 专门负责搜索信息"""

    def run(self, task: str, context: str = "") -> str:
        logger.info(f"🔍 ResearchAgent 执行: {task}")
        try:
            result = self.tools.execute("search_web", {"query": task})
            messages = [
                {"role": "system", "content": "You are a research specialist. Summarize the search results clearly and concisely."},
                {"role": "user", "content": f"Task: {task}\n\nSearch results:\n{result}\n\nProvide a clear summary."}
            ]
            return self.llm.chat(messages)
        except Exception as e:
            return f"Research failed: {str(e)}"


class AnalysisAgent(BaseAgent):
    """分析 Agent - 专门负责数据分析"""

    def run(self, task: str, context: str = "") -> str:
        logger.info(f"📊 AnalysisAgent 执行: {task}")
        messages = [
            {"role": "system", "content": "You are an analysis specialist. Analyze the given information and provide insights."},
            {"role": "user", "content": f"Task: {task}\n\nContext:\n{context}\n\nProvide detailed analysis."}
        ]
        return self.llm.chat(messages)


class WeatherAgent(BaseAgent):
    """天气 Agent - 专门负责天气查询"""

    def run(self, task: str, context: str = "") -> str:
        logger.info(f"🌤️ WeatherAgent 执行: {task}")
        try:
            result = self.tools.execute("get_weather", {"city": task})
            return result
        except Exception as e:
            return f"Weather query failed: {str(e)}"


class OrchestratorAgent(BaseAgent):
    """编排 Agent - 负责分配任务和整合结果"""

    def plan(self, user_task: str) -> List[Dict]:
        """把任务分配给不同 Agent"""
        messages = [
            {
                "role": "system",
                "content": """You are an orchestrator that assigns tasks to specialized agents.
Available agents:
- ResearchAgent: searches the web for information
- AnalysisAgent: analyzes data and provides insights
- WeatherAgent: checks weather for a city

Return ONLY JSON:
{
  "assignments": [
    {"agent": "ResearchAgent", "task": "specific task for this agent"},
    {"agent": "AnalysisAgent", "task": "specific task for this agent"}
  ]
}

Rules:
1. Only use agents that are needed
2. Each agent gets a specific, clear task
3. Always end with AnalysisAgent to synthesize results
4. Maximum 4 assignments"""
            },
            {"role": "user", "content": f"Assign agents for this task: {user_task}"}
        ]

        try:
            response = self.llm.chat(messages)
            clean = response.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            return data["assignments"]
        except Exception as e:
            logger.error(f"❌ Orchestrator planning failed: {str(e)}")
            return [{"agent": "ResearchAgent", "task": user_task}]

    def synthesize(self, user_task: str, results: List[Dict], history: List[Dict] = []) -> Generator:
        """整合所有 Agent 的结果，流式输出"""
        context = "\n\n".join([
            f"{r['agent']}:\n{r['result']}"
            for r in results
        ])

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Synthesize all agent results into a clear, comprehensive answer. Reply in the same language as the user."
            }
        ]
        messages.extend(history)
        messages.append({
            "role": "user",
            "content": f"Task: {user_task}\n\nAgent results:\n{context}\n\nProvide a complete answer."
        })

        return self.llm.chat_stream(messages)


class MultiAgentSystem:
    """多 Agent 协作系统"""

    def __init__(self, llm_service, tool_service):
        self.llm = llm_service
        self.tools = tool_service

        self.agents = {
            "ResearchAgent": ResearchAgent("ResearchAgent", "Research Specialist", llm_service, tool_service),
            "AnalysisAgent": AnalysisAgent("AnalysisAgent", "Analysis Specialist", llm_service),
            "WeatherAgent": WeatherAgent("WeatherAgent", "Weather Specialist", llm_service, tool_service),
        }

        self.orchestrator = OrchestratorAgent("Orchestrator", "Task Coordinator", llm_service, tool_service)
        logger.info(f"✅ MultiAgentSystem 初始化，共 {len(self.agents)} 个 Agent")

    def run_stream(self, user_task: str, history: List[Dict] = []) -> Generator:
        """流式执行多 Agent 协作"""

        # 第一步：编排器规划
        yield json.dumps({"type": "status", "message": "🎯 Orchestrator planning agent assignments..."}) + "\n"
        assignments = self.orchestrator.plan(user_task)
        yield json.dumps({"type": "assignments", "assignments": assignments}) + "\n"

        # 第二步：逐个执行 Agent
        results = []
        for assignment in assignments:
            agent_name = assignment["agent"]
            agent_task = assignment["task"]

            if agent_name not in self.agents:
                continue

            yield json.dumps({"type": "agent_start", "agent": agent_name, "task": agent_task}) + "\n"

            agent = self.agents[agent_name]
            context = "\n".join([r["result"] for r in results])
            result = agent.run(agent_task, context)
            results.append({"agent": agent_name, "task": agent_task, "result": result})

            yield json.dumps({"type": "agent_done", "agent": agent_name, "result": result[:200]}) + "\n"

        # 第三步：Orchestrator 整合，流式输出
        yield json.dumps({"type": "status", "message": "🧠 Synthesizing results..."}) + "\n"
        yield json.dumps({"type": "answer_start"}) + "\n"

        for chunk in self.orchestrator.synthesize(user_task, results, history):
            yield json.dumps({"type": "answer_chunk", "chunk": chunk}) + "\n"

        yield json.dumps({"type": "answer_end"}) + "\n"