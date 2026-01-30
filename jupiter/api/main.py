"""Jupiter Local API — localhost-only HTTP API."""
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from jupiter.config import API_HOST, API_PORT, ensure_dirs
from jupiter.agent.daemon import execute_plan
from jupiter.agent.planner import JupiterPlanner
from jupiter.safety.broker import SafetyBroker
from jupiter.storage.memory import MemoryStore
from jupiter.storage.audit import AuditStore

_memory: Optional[MemoryStore] = None
_broker: Optional[SafetyBroker] = None
_planner: Optional[JupiterPlanner] = None

def get_memory(): global _memory; _memory = _memory or MemoryStore(); return _memory
def get_broker(): global _broker; _broker = _broker or SafetyBroker(audit=AuditStore()); return _broker
def get_planner(): global _planner; _planner = _planner or JupiterPlanner(memory=get_memory()); return _planner

app = FastAPI(title="Jupiter OS API")

@app.middleware("http")
async def localhost_only(request: Request, call_next):
    client = request.client
    if not client or client.host not in ("127.0.0.1", "::1", "localhost"):
        return JSONResponse({"detail": "Only localhost allowed"}, status_code=403)
    return await call_next(request)

class ChatIn(BaseModel): message: str
class ChatOut(BaseModel): reply: str

@app.post("/chat", response_model=ChatOut)
async def chat(body: ChatIn):
    memory = get_memory()
    planner = get_planner()
    broker = get_broker()
    memory.session_append("user", body.message)
    plan = planner.plan(body.message)
    output = execute_plan(plan, broker, memory)
    memory.session_append("assistant", output)
    return ChatOut(reply=output)

@app.get("/memory/session")
async def memory_session():
    return {"messages": get_memory().session_get_recent(50)}

@app.delete("/memory/session")
async def memory_session_clear():
    get_memory().session_clear()
    return {"ok": True}

@app.get("/audit")
async def audit_recent(limit: int = 100):
    return {"entries": get_broker().audit.get_recent(limit)}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "jupiter"}

def main():
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT, log_level="info")

if __name__ == "__main__":
    main()
