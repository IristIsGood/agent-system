"""
本地测试脚本
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("\n1️⃣ 测试健康检查...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   响应: {response.json()}")


def test_tools():
    """测试获取工具列表"""
    print("\n2️⃣ 获取工具列表...")
    response = requests.get(f"{BASE_URL}/api/agent/tools")
    print(f"   响应: {response.json()}")


def test_execute():
    """测试执行 Agent - 数学计算"""
    print("\n3️⃣ 执行 Agent 任务（数学计算）...")
    
    task = "计算 10 + 5 是多少？"
    print(f"   任务: {task}")
    
    response = requests.post(
        f"{BASE_URL}/api/agent/execute",
        json={"task": task}
    )
    
    if response.status_code != 200:
        print(f"   ❌ HTTP {response.status_code}: {response.json()}")
        return
    
    result = response.json()
    print(f"   状态: {result['status']}")
    print(f"   结果: {result['result']}")
    print(f"   迭代次数: {result['iterations']}")


def test_weather():
    """测试查询天气"""
    print("\n4️⃣ 执行 Agent 任务（天气查询）...")
    
    task = "查询上海今天的天气"
    print(f"   任务: {task}")
    
    response = requests.post(
        f"{BASE_URL}/api/agent/execute",
        json={"task": task}
    )
    
    if response.status_code != 200:
        print(f"   ❌ HTTP {response.status_code}: {response.json()}")
        return
    
    result = response.json()
    print(f"   状态: {result['status']}")
    print(f"   结果: {result['result']}")
    print(f"   迭代次数: {result['iterations']}")


def test_search():
    """测试搜索网络信息"""
    print("\n5️⃣ 执行 Agent 任务（网络搜索）...")
    
    task = "搜索最新的 Python 3.12 有哪些新功能"
    print(f"   任务: {task}")
    
    response = requests.post(
        f"{BASE_URL}/api/agent/execute",
        json={"task": task}
    )
    
    if response.status_code != 200:
        print(f"   ❌ HTTP {response.status_code}: {response.json()}")
        return
    
    result = response.json()
    print(f"   状态: {result['status']}")
    print(f"   结果: {result['result']}")
    print(f"   迭代次数: {result['iterations']}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 本地 API 测试")
    print("=" * 60)
    
    try:
        test_health()
        test_tools()
        test_execute()
        test_weather()
        test_search()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")