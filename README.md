# AI Agent System 🤖

A full-stack AI Agent system with multi-turn conversation, tool calling, RAG knowledge base, and user authentication. Built with FastAPI and React.

## 🎯 Problem & Solution

* **Problem:** Most AI chatbots are stateless — they forget previous messages, can't access real-time data, and have no knowledge of your private documents.
* **Solution:** A **full-stack Agentic System**. The agent maintains conversation history across sessions, autonomously decides when to call tools (search, calculate, weather), and can answer questions grounded in your uploaded documents via RAG.

## 🏗️ Technical Architecture & Agentic Logic

The system implements a **ReAct-style Agent Loop** at its core:

1. **The Agent Executor:** Receives the user task and full conversation history. Calls the LLM with available tools and decides whether to act or respond.
2. **Tool Calling Loop:** If the LLM decides to use a tool, the executor calls it, feeds the result back to the LLM, and iterates — up to a maximum of **10 iterations**.
3. **RAG Pipeline:** On demand, the system retrieves the top $k = 3$ relevant chunks from a local **ChromaDB** instance using `sentence-transformers` embeddings, and injects them as context before the LLM generates a response.
4. **Streaming Response:** Once all tool calls are resolved, the final answer is streamed token-by-token to the frontend for a real-time typing effect.
5. **Session Persistence:** Every message is saved to a **SQLite** database, tied to an authenticated user, so conversations survive page refreshes and re-logins.

## ✨ Key Features

* **Multi-turn Memory:** Full conversation history is passed to the LLM on every request.
* **Tool Calling:** Agent autonomously uses real web search (DuckDuckGo), math calculator, and weather lookup.
* **RAG Knowledge Base:** Upload PDF or TXT/Markdown files; the agent answers questions grounded in your documents.
* **Streaming Output:** Token-by-token streaming with tool execution happening silently before the final answer streams.
* **User Authentication:** JWT-based register/login with bcrypt password hashing.
* **Conversation History:** Full persistence in SQLite — browse, load, and delete past conversations.
* **Auto-generated Titles:** Conversation titles are generated automatically from the first message.

## 🛠️ Tech Stack

**Backend**
* **Framework:** FastAPI + Uvicorn
* **Agent Logic:** Custom ReAct loop with OpenAI Function Calling
* **LLM:** OpenAI (`gpt-4`)
* **Vector Store:** ChromaDB (local persistence)
* **Embeddings:** `sentence-transformers` (`all-MiniLM-L6-v2`)
* **Database:** SQLite via SQLAlchemy
* **Auth:** JWT (`python-jose`) + bcrypt (`passlib`)
* **Search Tool:** DuckDuckGo (`duckduckgo-search`)

**Frontend**
* **Framework:** React
* **HTTP:** Axios + Fetch API (streaming)
* **Routing:** React Router DOM

## 🚀 Getting Started

### 1. Clone & Environment Setup

```bash
git clone <your-repo-url>
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
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000  
```

### 4. Run the Frontend

```bash
cd frontend
npm install
npm start
```

Open `http://localhost:3000` — register an account and start chatting.

## 🔑 Key Technical Decisions

* **Custom Agent Loop over LangChain:** Built the ReAct loop from scratch to maintain full visibility and control over tool execution, message formatting, and iteration logic — without the abstraction overhead of a framework.
* **Streaming After Tool Resolution:** Tool calls are executed synchronously first (required by the OpenAI API), then the final answer is streamed. This gives users real-time feedback while ensuring tool results are fully grounded in the response.
* **SQLite for Simplicity:** Chose SQLite over PostgreSQL for zero-setup local development. The SQLAlchemy ORM makes migrating to PostgreSQL trivial when scaling.
* **Separate `/execute` and `/stream` Endpoints:** `/execute` handles raw agent tasks (used internally and for testing), while `/stream` runs the full tool loop and then streams the final answer — separating concerns cleanly.

## 📁 Project Structure
