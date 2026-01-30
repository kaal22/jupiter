"""Jupiter planner — plan next action via local Ollama."""
import json
import httpx
from typing import Optional
from jupiter.config import OLLAMA_BASE_URL, DEFAULT_MODEL
from jupiter.storage.memory import MemoryStore
from jupiter.prompt import get_system_info, build_system_prompt


class JupiterPlanner:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: Optional[str] = None, memory: Optional[MemoryStore] = None):
        self.base_url = base_url.rstrip("/")
        self.model = model or DEFAULT_MODEL
        self.memory = memory or MemoryStore()
        self._system_prompt = build_system_prompt(get_system_info())

    def _chat(self, messages: list) -> str:
        with httpx.Client(timeout=120.0) as client:
            r = client.post(f"{self.base_url}/api/chat", json={"model": self.model, "messages": messages, "stream": False})
            r.raise_for_status()
            return (r.json().get("message") or {}).get("content", "")

    def plan(self, user_message: str) -> dict:
        context = self.memory.get_context_for_agent(session_limit=20, episodic_limit=5)
        prompt = (context + "\n\nUser: " + user_message) if context else user_message
        full_user = self._system_prompt + "\n\n---\nConversation context:\n" + prompt
        response = self._chat([{"role": "user", "content": full_user}])
        json_str = response.strip()
        for start in ("```json", "```"):
            if start in json_str:
                json_str = json_str.split(start, 1)[-1].split("```", 1)[0].strip()
        try:
            plan = json.loads(json_str)
        except json.JSONDecodeError:
            plan = {"action": "reply", "content": response}
        if plan.get("action") not in ("reply", "tool"):
            plan["action"] = "reply"
            plan["content"] = response
        return plan
