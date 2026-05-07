# AI Agent System 🤖

A full-stack AI Agent system featuring 5 execution modes, multi-agent collaboration, task planning, RAG knowledge base, real-time execution visualization, analytics dashboard, LangGraph integration, and MCP protocol support. Built with FastAPI and React.

## 🎯 Problem & Solution

* **Problem:** Most AI chatbots are stateless, single-agent, and opaque — they forget previous messages, can't access real-time data, have no knowledge of private documents, and give users no visibility into how answers are generated.
* **Solution:** A **full-stack Agentic System** with 5 execution modes. The system maintains conversation history across sessions, autonomously decides when to call tools, coordinates multiple specialized agents, manages complex workflows via LangGraph, and exposes tools via MCP protocol.

## 🏗️ Technical Architecture

### 5 Execution Modes

**1. Default (Stream)**
User → Tool calling loop (search/calculate/weather) → Stream answer token by token

**2. Task Planning**
User → LLM decomposes into 2-5 typed subtasks → Execute each → Stream consolidated answer
Real-time UI: each step lights up as it executes (pending → running → done)

**3. Multi-Agent**
User → Orchestrator assigns tasks:
ResearchAgent  → searches & summarizes web results
AnalysisAgent  → analyzes data, provides insights
WeatherAgent   → queries real-time weather (wttr.in)
→ Orchestrator synthesizes → Stream final answer

**4. LangGraph**
User → StateGraph:
[LLM Node] → has tool calls? → [Tool Node] → back to LLM
↓ no
[END]
Conditional edges manage the ReAct loop as a proper state machine

**5. MCP (Model Context Protocol)**
User → Agent with MCP-formatted tools → Execute via standard protocol → Answer
Exposes search_web, get_weather, calculate as MCP-compliant tools

### Core Components
1. **Agent Executor** — Custom ReAct loop with OpenAI Function Calling, up to 10 iterations
2. **Task Planner** — LLM-based decomposition into typed subtasks (search/weather/calculate/answer)
3. **Multi-Agent System** — Orchestrator + 3 specialized agents with context passing
4. **LangGraph Agent** — StateGraph with conditional edges, tool nodes, and state management
5. **MCP Layer** — Standard Model Context Protocol tool definitions
6. **RAG Pipeline** — ChromaDB + sentence-transformers, top-k retrieval with similarity scores
7. **Streaming** — Tool calls execute synchronously; final answer streams via SSE
8. **Auth** — JWT + bcrypt, 7-day token expiry
9. **Persistence** — SQLite (Users → Conversations → Messages + CallLogs)

## ✨ Key Features

* **5 Agent Modes** — Default, Task Planning, Multi-Agent, LangGraph, MCP
* **Real-time Execution Visualization** — Live step status (pending → running → done)
* **Tool Calling** — Web search (DuckDuckGo), real weather (wttr.in), math calculator
* **RAG Knowledge Base** — Upload PDF/TXT/Markdown, answers with similarity scores
* **Multi-turn Memory** — Full conversation history passed to LLM on every request
* **Streaming Output** — Token-by-token with tool execution before streaming
* **Analytics Dashboard** — Calls, tokens, cost, response time, mode distribution, tool usage
* **User Authentication** — JWT register/login, per-user conversation isolation
* **Auto-generated Titles** — Conversation titles generated from first message
* **Conversation Management** — Browse, load, delete past conversations

## 🛠️ Tech Stack

**Backend**
* **Framework:** FastAPI + Uvicorn
* **Agent Logic:** Custom ReAct + Task Planner + Multi-Agent + LangGraph + MCP
* **LLM:** OpenAI GPT-4
* **Agent Framework:** LangGraph + LangChain
* **Tool Protocol:** MCP (Model Context Protocol)
* **Vector Store:** ChromaDB (local persistence)
* **Embeddings:** sentence-transformers (all-MiniLM-L6-v2)
* **Database:** SQLite via SQLAlchemy
* **Auth:** JWT (python-jose) + bcrypt (passlib)
* **Tools:** DuckDuckGo (ddgs), wttr.in

**Frontend**
* **Framework:** React
* **HTTP:** Axios + Fetch API (streaming)
* **Dashboard:** Custom charts

## 🚀 Getting Started

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd agent-system
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 2. Configuration

Create `.env` in `backend/`:

```env
OPENAI_API_KEY=sk-your-key-here
MODEL_TYPE=gpt-4
MAX_ITERATIONS=10
```

### 3. Run Backend

```bash
cd backend
python app/main.py
```

### 4. Run Frontend

```bash
cd frontend
npm install
npm start
```

Open `http://localhost:3000`, register and start chatting.

## 🔑 Key Technical Decisions

* **5 Execution Modes** — Each mode is a separate endpoint with its own execution strategy. This keeps concerns separated and makes it easy to add new modes without touching existing code.
* **Custom ReAct Loop** — Built from scratch before introducing LangGraph, to understand the underlying mechanics. LangGraph mode then wraps the same logic in a proper state machine.
* **LangGraph as State Machine** — Chose StateGraph over a plain Python loop for the LangGraph mode to demonstrate graph-based agent orchestration with conditional edges and typed state.
* **MCP Protocol** — Tools are exposed in MCP-compliant format, making them consumable by any MCP-compatible client (Claude Desktop, Cursor, etc.).
* **SSE Streaming** — Backend yields newline-delimited JSON events; frontend reads with `getReader()`. Each event has a `type` field for fine-grained UI updates.
* **SQLite for Zero-Config** — No setup required; SQLAlchemy ORM makes migrating to PostgreSQL trivial.

## 📁 Project Structure
agent-system/
├── backend/
│   ├── app/main.py              # FastAPI entry point
│   ├── api/
│   │   ├── agent_routes.py      # /execute /stream /plan /multi /langgraph /mcp
│   │   ├── auth_routes.py       # /register /login
│   │   ├── history_routes.py    # Conversation persistence
│   │   ├── rag_routes.py        # Document upload & search
│   │   └── stats_routes.py      # Analytics dashboard
│   ├── core/
│   │   ├── agent_executor.py    # Custom ReAct loop
│   │   ├── database.py          # SQLAlchemy models
│   │   ├── langgraph_agent.py   # LangGraph StateGraph agent
│   │   ├── mcp_client.py        # MCP client
│   │   ├── multi_agent.py       # Multi-agent orchestration
│   │   └── task_planner.py      # Task decomposition
│   ├── mcp_server.py            # MCP server (stdio)
│   └── services/
│       ├── llm_service.py       # OpenAI wrapper
│       ├── tool_service.py      # Tool registry & execution
│       └── rag_service.py       # ChromaDB + embeddings
└── frontend/
└── src/
├── App.js               # Main chat interface (5 modes)
├── Login.js             # Auth page
├── Dashboard.js         # Analytics dashboard
└── api.js               # API client

## 🛡️ License
MIT

## 👤 Developer
**Irist** — Building full-stack AI Agent systems from scratch.