from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SingleAgent API",
    description="单个 Agent 的完整 AI 系统",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Import and register the router
from backend.api.agent_routes import router, init_services
app.include_router(router)

# ✅ RAG 路由（新增）
from backend.api.rag_routes import router as rag_router
app.include_router(rag_router)

# ✅ Call init_services on startup
@app.on_event("startup")
async def startup_event():
    init_services()

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "SingleAgent API is running"}

@app.get("/")
async def root():
    return {
        "name": "SingleAgent System",
        "version": "1.0.0",
        "docs": "http://localhost:8000/docs",
        "health": "http://localhost:8000/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, log_level="info")