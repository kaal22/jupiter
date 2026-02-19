import os
from fastapi import FastAPI, Request, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from jupiter.dashboard.terminal import TerminalManager

app = FastAPI(title="Jupiter Dashboard")
terminal_manager = TerminalManager()

# Determine base path for templates/static
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.websocket("/ws/terminal")
async def terminal_endpoint(websocket: WebSocket):
    await terminal_manager.handle_websocket(websocket)

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
