"""Jupiter OS configuration — paths, URLs, and policy."""
import os
from pathlib import Path

XDG_DATA = Path(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")))
XDG_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")))
XDG_STATE = Path(os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state")))

JUPITER_DATA = XDG_DATA / "jupiter"
JUPITER_CONFIG = XDG_CONFIG / "jupiter"
JUPITER_STATE = XDG_STATE / "jupiter"
DB_PATH = JUPITER_DATA / "jupiter.db"
AUDIT_DB_PATH = JUPITER_DATA / "audit.db"
OLLAMA_BASE_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_CHAT_TIMEOUT = float(os.environ.get("JUPITER_OLLAMA_CHAT_TIMEOUT", "600"))  # seconds; 10 min default for slow CPU-only
API_HOST = "127.0.0.1"
API_PORT = int(os.environ.get("JUPITER_API_PORT", "8765"))

MODEL_POLICY = {
    0: "llama3.2:3b",
    4: "llama3.2:3b",
    6: "llama3.2:3b",
    8: "llama3.2:7b-q4_0",
    12: "llama3.2:7b-q5_0",
    16: "llama3.2:13b-q4_0",
}
DEFAULT_MODEL = "llama3.2:3b"


def ensure_dirs():
    for d in (JUPITER_DATA, JUPITER_CONFIG, JUPITER_STATE):
        d.mkdir(parents=True, exist_ok=True)
