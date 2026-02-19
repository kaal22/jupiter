import os
from fastapi import FastAPI, Request, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from jupiter.dashboard.terminal import TerminalManager
from jupiter.storage.audit import AuditStore
import json

try:
    import psutil
except ImportError:
    psutil = None

app = FastAPI(title="Jupiter Dashboard")
terminal_manager = TerminalManager()
audit_store = AuditStore()

# Determine base path for templates/static
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.websocket("/ws/terminal")
async def terminal_endpoint(websocket: WebSocket):
    await terminal_manager.handle_websocket(websocket)

@app.get("/api/stats")
async def get_stats(request: Request):
    if psutil:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        mem_used = round(mem.used / (1024**3), 1)
        mem_pct = mem.percent
    else:
        cpu, mem_used, mem_pct = 0, 0, 0
    
    return HTMLResponse(f"""
    <div class="flex flex-col justify-center border border-cyan-800/50 bg-cyan-900/10 relative overflow-hidden h-full">
        <div class="text-[10px] text-cyan-400 uppercase mb-1">CPU Load</div>
        <div class="text-2xl font-bold text-white">{cpu}%</div>
        <div class="absolute bottom-0 left-0 h-1 bg-cyan-500 transition-all duration-500" style="width: {cpu}%"></div>
    </div>
    <div class="flex flex-col justify-center border border-cyan-800/50 bg-cyan-900/10 relative overflow-hidden h-full">
        <div class="text-[10px] text-cyan-400 uppercase mb-1">Memory</div>
        <div class="text-2xl font-bold text-white">{mem_used}<span class="text-xs">GB</span></div>
        <div class="absolute bottom-0 left-0 h-1 bg-purple-500 transition-all duration-500" style="width: {mem_pct}%"></div>
    </div>
    """)

@app.get("/api/activity")
async def get_activity(request: Request):
    entries = audit_store.get_recent(limit=20)
    html = ""
    for e in entries:
        action = e.get("action", "unknown")
        outcome = str(e.get("outcome", ""))
        
        color = "border-gray-500"
        if "exploit" in action: color = "border-red-500"
        elif "scan" in action: color = "border-cyan-500"
        elif "success" in outcome: color = "border-green-500"
        elif "fail" in outcome: color = "border-orange-500"

        detail_raw = e.get("details", {})
        # If it's a dict, convert to string, otherwise str
        detail_txt = str(detail_raw)
        if isinstance(detail_raw, dict):
            # Try to get cleaner summary
            if "query" in detail_raw: detail_txt = f"Query: {detail_raw['query']}"
            elif "command" in detail_raw: detail_txt = f"Cmd: {detail_raw['command']}"
            elif "target" in detail_raw: detail_txt = f"Target: {detail_raw['target']}"
            elif "tool" in detail_raw: detail_txt = f"Tool: {detail_raw['tool']}"
        
        # Truncate
        if len(detail_txt) > 60: detail_txt = detail_txt[:60] + "..."

        html += f"""
        <div class="border-l-2 {color} pl-2 py-1 mb-1">
            <div class="text-[11px] font-bold text-cyan-300 flex justify-between">
                <span>{action.upper()}</span>
                <span class="text-[9px] opacity-50">{e.get('created_at', '')}</span>
            </div>
            <div class="text-[10px] opacity-70 break-all font-mono leading-tight">{detail_txt}</div>
        </div>
        """
    return HTMLResponse(html or "<div class='text-gray-500 text-xs italic opacity-50'>No recent activity.</div>")

@app.get("/api/targets")
async def get_targets(request: Request):
    logs = audit_store.get_recent(limit=100)
    targets = {}  # target -> status
    
    for log in logs:
        action = log.get("action", "")
        # Check details which is often a dict
        detail = log.get("details", {})
        if not isinstance(detail, dict):
            continue

        if action == "network_scan":
            t = detail.get("target") or detail.get("args", {}).get("target")
            if t:
                targets[t] = "SCANNED"
            
    if not targets:
        return HTMLResponse('<div class="text-xs text-gray-500 italic p-2 opacity-50">No active targets detected.</div>')
        
    html = ""
    for t, status in targets.items():
        html += f"""
        <div class="p-3 border border-cyan-800/50 bg-cyan-900/10 hover:bg-cyan-900/30 cursor-pointer transition-colors group mb-2 relative overflow-hidden">
            <div class="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div class="flex justify-between items-center relative z-10">
                <span class="font-bold text-white group-hover:text-cyan-300 font-mono">{t}</span>
                <span class="text-[9px] bg-cyan-900/80 text-cyan-300 px-1 border border-cyan-800 rounded">{status}</span>
            </div>
            <div class="text-[9px] text-gray-500 mt-1">Found via Nmap</div>
        </div>
        """
    return HTMLResponse(html)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Jupiter Command Center",
        "version": "v2.0"
    })

def run_dashboard(host: str = "127.0.0.1", port: int = 8000):
    """Run the FastAPI server."""
    import uvicorn
    print(f"[*] Launching Jupiter Dashboard at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
