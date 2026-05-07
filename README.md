
# 🤖 AI Agent System

A full-stack AI Agent system with **5 execution modes**, multi-agent collaboration, task planning, RAG knowledge base, real-time execution visualization, analytics dashboard, LangGraph integration, and MCP protocol support. Built with **FastAPI** and **React**.

---

## 🎯 Problem & Solution

*   **Problem:** Most AI chatbots are stateless, single-agent, and opaque — they forget previous messages, can't access real-time data, have no knowledge of private documents, and give users no visibility into how answers are generated.
*   **Solution:** A **full-stack Agentic System** with 5 execution modes. The agent maintains conversation history across sessions, autonomously decides when to call tools, coordinates multiple specialized agents for complex tasks, manages workflows via LangGraph, and exposes tools via MCP protocol.

---

## 🏗️ Technical Architecture & Agentic Logic

The system implements multiple agentic patterns, selectable per message:

1.  **The Agent Executor (Default):** Runs a custom **ReAct loop**. It calls the LLM with available tools, executes them, feeds results back, and iterates up to **10 iterations**.
2.  **Task Planner:** Decomposes complex tasks into 2–5 typed subtasks (`search` / `weather` / `calculate` / `answer`), executes each in sequence, and streams results with real-time step visualization.
3.  **Multi-Agent Orchestration:** An Orchestrator assigns tasks to specialized agents:
    *   `ResearchAgent`: Web search + summarization.
    *   `AnalysisAgent`: Data analysis + insights.
    *   `WeatherAgent`: Real-time weather updates.
4.  **LangGraph Agent:** Implemented as a `StateGraph`:  
    `[LLM Node]` → *conditional edge* → `[Tool Node]` → `[LLM Node]` or `[END]`.
5.  **MCP (Model Context Protocol):** Tools are exposed in MCP-compliant format, making them consumable by any MCP-compatible client (Claude Desktop, Cursor, etc.).
6.  **RAG Pipeline:** Retrieves top $k = 3$ chunks from a local **ChromaDB** using `all-MiniLM-L6-v2` embeddings, returning similarity scores and grounding context.
7.  **Streaming Response:** Uses **SSE (Server-Sent Events)** with newline-delimited JSON events (`status`, `tasks`, `executing`, `done`, `chunk`).
8.  **Session Persistence:** Every message is saved to **SQLite**, tied to an authenticated user via JWT.

---

## ✨ Key Features

*   **5 Agent Modes:** Default, Task Planning, Multi-Agent, LangGraph, MCP.
*   **Real-time Visualization:** Live step status (Pending ➔ Running ➔ Done).
*   **Built-in Tooling:** DuckDuckGo Search, wttr.in Weather, Math Calculator.
*   **RAG Knowledge Base:** Upload PDF/TXT/Markdown with similarity score display.
*   **Multi-turn Memory:** Full persistent conversation history.
*   **Analytics Dashboard:** Track calls, tokens, estimated cost, and mode distribution.
*   **User Auth:** Secure JWT register/login with bcrypt.
*   **Management:** Auto-generated titles and full conversation CRUD.

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Backend Framework** | FastAPI + Uvicorn |
| **Agent Framework** | LangGraph + LangChain |
| **LLM** | OpenAI (`gpt-4`) |
| **Vector Store** | ChromaDB (Local) |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) |
| **Database** | SQLite via SQLAlchemy |
| **Auth** | JWT (`python-jose`) + bcrypt |
| **Frontend** | React + Axios |

---

## 🚀 Getting Started

### 1. Clone & Environment Setup
```bash
git clone https://github.com/IristIsGood/agent-system.git
cd agent-system
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 2. Configuration
Create a `.env` file in the `backend/` directory:
```env
OPENAI_API_KEY=sk-your-key-here
MODEL_TYPE=gpt-4
MAX_ITERATIONS=10
```

### 3. Run the Backend
```bash
cd backend
python app/main.py
```

### 4. Run the Frontend
```bash
cd frontend
npm install
npm start
```
Open `http://localhost:3000` to register and start.

---

## 🔑 Key Technical Decisions

*   **Separation of Concerns:** 5 modes are mapped to 5 distinct endpoints (`/stream`, `/plan`, etc.), making the system modular.
*   **Hybrid Logic:** Built the ReAct loop from scratch first for deep understanding, then implemented LangGraph for production-grade state management.
*   **Protocol Standards:** Adopted **MCP** to ensure tools are future-proof and compatible with external AI ecosystems.
*   **UI/UX Synchronicity:** OpenAI requires synchronous tool calls; we bridge this by using SSE to update the UI on tool status before streaming the final text chunk.

---

## 📁 Project Structure

```text
agent-system/
├── backend/
│   ├── app/main.py              # FastAPI entry point
│   ├── api/                     # Route definitions (Auth, Agent, RAG, Stats)
│   ├── core/                    # Core Logic (ReAct, LangGraph, Multi-Agent, Planner)
│   ├── services/                # LLM, Tool, and RAG services
│   └── mcp_server.py            # MCP implementation
└── frontend/
    └── src/
        ├── App.js               # Main Chat Interface
        ├── Login.js             # Auth Page
        └── Dashboard.js         # Analytics
```

---

## 🛡️ License
MIT

## 👤 Developer
**Irist** — Building full-stack AI Agent systems from scratch.