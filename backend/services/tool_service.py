"""
工具服务 - 管理和执行工具
"""

import logging
from typing import Callable, Dict, Any, Optional, List
import json


logger = logging.getLogger(__name__)

class Tool:
    """
    单个工具的定义和管理
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        params: Dict[str, Any]
    ):
        """
        初始化工具
        
        Args:
            name: 工具名称
            description: 工具描述
            func: 工具执行的函数
            params: 参数定义（JSON Schema 格式）
        """
        self.name = name
        self.description = description
        self.func = func
        self.params = params
        logger.info(f"✅ 工具定义成功: {name}")
    
    def to_llm_format(self) -> Dict[str, Any]:
        """
        转换为 OpenAI Function Calling 格式
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.params
            }
        }
    
    def execute(self, **kwargs) -> Any:
        """
        执行工具
        """
        try:
            logger.info(f"🔧 执行工具: {self.name}，参数: {kwargs}")
            result = self.func(**kwargs)
            logger.info(f"✅ 工具执行成功: {self.name}")
            return result
        except Exception as e:
            logger.error(f"❌ 工具执行失败: {self.name} - {str(e)}")
            raise


class ToolService:
    """
    工具管理服务
    """
    
    def __init__(self):
        """初始化工具服务"""
        self.tools: Dict[str, Tool] = {}
        logger.info("✅ ToolService 初始化成功")
    
    def register(self, tool: Tool) -> None:
        """
        注册工具
        """
        self.tools[tool.name] = tool
        logger.info(f"✅ 工具已注册: {tool.name}")
    
    def execute(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        执行指定的工具
        """
        if tool_name not in self.tools:
            raise ValueError(f"工具不存在: {tool_name}")
        
        tool = self.tools[tool_name]
        return tool.execute(**args)
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的 LLM 格式
        """
        return [tool.to_llm_format() for tool in self.tools.values()]
    
    def list_tools(self) -> Dict[str, str]:
        """
        列出所有工具
        """
        return {name: tool.description for name, tool in self.tools.items()}


# 定义内置工具

def calculate(operation: str, a: float, b: float) -> float:
    """计算器工具"""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            return "错误：除数不能为 0"
        return a / b
    else:
        return "错误：未知的操作"


def get_weather(city: str) -> str:
    """天气查询工具（真实）"""
    try:
        import requests
        url = f"https://wttr.in/{city}?format=3&lang=en"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        return f"Weather info for {city} is unavailable"
    except Exception as e:
        return f"Weather query failed: {str(e)}"


def search_web(query: str) -> str:
    """网页搜索工具（真实）"""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if not results:
            return f"没有找到关于 '{query}' 的结果"
        output = f"搜索 '{query}' 的结果：\n\n"
        for i, r in enumerate(results, 1):
            output += f"{i}. {r['title']}\n{r['body']}\n\n"
        return output
    except Exception as e:
        return f"搜索失败: {str(e)}"


# 创建全局工具服务实例
tool_service = ToolService()

# 注册计算器工具
tool_service.register(Tool(
    name="calculate",
    description="执行数学计算（支持 add/subtract/multiply/divide）",
    func=calculate,
    params={
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide"],
                "description": "运算操作"
            },
            "a": {
                "type": "number",
                "description": "第一个数字"
            },
            "b": {
                "type": "number",
                "description": "第二个数字"
            }
        },
        "required": ["operation", "a", "b"]
    }
))

# 注册天气查询工具
tool_service.register(Tool(
    name="get_weather",
    description="查询指定城市的天气信息",
    func=get_weather,
    params={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "城市名称"
            }
        },
        "required": ["city"]
    }
))

# 注册网页搜索工具
tool_service.register(Tool(
    name="search_web",
    description="搜索网络信息",
    func=search_web,
    params={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词"
            }
        },
        "required": ["query"]
    }
))

logger.info(f"✅ 已注册 {len(tool_service.tools)} 个内置工具")