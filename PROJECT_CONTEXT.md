# Project Context — AI Agent System

## 项目位置
/Users/irist/agent-system

## 虚拟环境
cd /Users/irist/agent-system
source .venv/bin/activate

## 启动方式
# 后端
cd /Users/irist/agent-system/backend
python app/main.py

# 前端
cd /Users/irist/agent-system/frontend
npm start

## 技术栈
- 后端：FastAPI + SQLite + SQLAlchemy
- LLM：OpenAI GPT-4
- 向量数据库：ChromaDB
- 嵌入模型：sentence-transformers all-MiniLM-L6-v2
- 搜索工具：DuckDuckGo (ddgs)
- 天气工具：wttr.in (真实 API)
- 前端：React + Axios
- 认证：JWT + bcrypt
- Agent 框架：LangGraph + LangChain
- 工具协议：MCP (Model Context Protocol)

## 已完成功能
- ✅ 用户注册 / 登录（JWT）
- ✅ 多轮对话（历史记录传给 LLM）
- ✅ 流式输出（打字机效果）
- ✅ 工具调用（calculate / get_weather / search_web）
- ✅ RAG 知识库（PDF / TXT / Markdown + 相似度分数）
- ✅ 对话历史持久化（SQLite）
- ✅ 对话标题自动生成
- ✅ 删除对话
- ✅ 任务规划和分解（TaskPlanner）
- ✅ 多 Agent 协作（ResearchAgent / AnalysisAgent / WeatherAgent / Orchestrator）
- ✅ 执行流程可视化（实时步骤显示）
- ✅ 数据看板（调用统计 / 响应时间 / 成本 / 模式分布）
- ✅ LangGraph Agent（StateGraph + 条件分支 + 工具节点）
- ✅ MCP 支持（标准化工具协议）

## 待完成功能
- 🔲 Skill 系统
- 🔲 部署上线

## 5种 Agent 模式
- 💬 Default     → 普通流式，工具调用
- 🗺️ Task Planning → 拆解子任务，实时显示步骤
- 🤝 Multi-Agent  → 专门 Agent 协作（Research/Analysis/Weather）
- 🔗 LangGraph    → StateGraph 状态机管理流程
- 🔌 MCP          → MCP 协议标准化工具调用

## API 端点
- POST /api/auth/register
- POST /api/auth/login
- POST /api/agent/execute     ← 工具调用
- POST /api/agent/stream      ← 流式对话
- POST /api/agent/plan        ← 任务规划（流式）
- POST /api/agent/multi       ← 多 Agent（流式）
- POST /api/agent/langgraph   ← LangGraph（流式）
- POST /api/agent/mcp         ← MCP 工具调用
- GET  /api/agent/tools
- POST /api/rag/upload
- POST /api/rag/search
- GET  /api/rag/documents
- POST /api/history/message
- GET  /api/history/conversations
- GET  /api/history/messages/{id}
- DELETE /api/history/conversation/{id}
- PUT /api/history/conversation/{id}/title
- POST /api/stats/log
- GET  /api/stats/dashboard

## 项目结构
agent-system/
├── .venv/
├── backend/
│   ├── app/main.py
│   ├── api/
│   │   ├── agent_routes.py
│   │   ├── auth_routes.py
│   │   ├── history_routes.py
│   │   ├── rag_routes.py
│   │   └── stats_routes.py
│   ├── core/
│   │   ├── agent_executor.py
│   │   ├── database.py
│   │   ├── langgraph_agent.py
│   │   ├── mcp_client.py
│   │   ├── multi_agent.py
│   │   └── task_planner.py
│   ├── mcp_server.py
│   ├── models/schemas.py
│   └── services/
│       ├── llm_service.py
│       ├── tool_service.py
│       └── rag_service.py
├── frontend/
│   └── src/
│       ├── App.js
│       ├── App.css
│       ├── Login.js
│       ├── Dashboard.js
│       └── api.js
├── chroma_db/
├── uploads/
└── agent.db

## 已知问题 / 注意事项
- bcrypt 需要用 4.0.1 版本
- 运行后端要在 backend 目录
- 所有 import 用 backend.xxx 前缀
- 搜索工具用 ddgs（duckduckgo_search 已改名）
- sentence-transformers 如果丢失需要重新 pip install
- MCP stdio server 不能直接在终端测试