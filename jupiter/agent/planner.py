"""Jupiter planner — plan next action via local Ollama."""
import json
import httpx
from typing import Optional
from jupiter.config import OLLAMA_BASE_URL, OLLAMA_CHAT_TIMEOUT, DEFAULT_MODEL
from jupiter.storage.memory import MemoryStore
from jupiter.prompt import get_system_info, build_system_prompt

KNOWN_ACTIONS = frozenset({
    "reply", "tool",
    "system_status", "system_logs_tail", "system_diagnostics",
    "terminal_explain", "terminal_exec",
    "remember_preference", "remember_summary", "audit_log",
    "exploit_search", "msf_exec",
})


class JupiterPlanner:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: Optional[str] = None, memory: Optional[MemoryStore] = None):
        self.base_url = base_url.rstrip("/")
        self.model = model or DEFAULT_MODEL
        self.memory = memory or MemoryStore()
        self._system_prompt = build_system_prompt(get_system_info())

    def _chat(self, messages: list) -> str:
        with httpx.Client(timeout=OLLAMA_CHAT_TIMEOUT) as client:
            r = client.post(f"{self.base_url}/api/chat", json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1},
            })
            r.raise_for_status()
            return (r.json().get("message") or {}).get("content", "")

    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract a JSON action object from LLM response."""
        text = text.strip()
        # Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Strip code fences
        for marker in ("```json", "```"):
            if marker in text:
                inner = text.split(marker, 1)[-1].split("```", 1)[0].strip()
                try:
                    return json.loads(inner)
                except json.JSONDecodeError:
                    pass
        # Find JSON by matching braces
        idx = text.find('{')
        while idx is not None and 0 <= idx < len(text):
            depth = 0
            for i in range(idx, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            obj = json.loads(text[idx:i+1])
                            if "action" in obj:
                                return obj
                        except json.JSONDecodeError:
                            pass
                        break
            next_idx = text.find('{', idx + 1)
            idx = next_idx if next_idx > idx else None
        return None

    def plan(self, user_message: str, observations: list = None) -> dict:
        context = self.memory.get_context_for_agent(session_limit=20, episodic_limit=5)
        prompt_parts = []
        if context:
            prompt_parts.append(context)
        prompt_parts.append(f"User: {user_message}")

        if observations:
            prompt_parts.append("\n--- Tool Results ---")
            for obs in observations:
                prompt_parts.append(
                    f"[Step {obs['step']}] {obs['tool']}({json.dumps(obs['args'])})\n"
                    f"Output:\n{obs['result']}"
                )
            prompt_parts.append("---")
            prompt_parts.append(
                "Based on the results, decide next action. "
                "Reply if you have enough info, or run another tool."
            )

        full_prompt = "\n\n".join(prompt_parts)
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": full_prompt},
        ]
        response = self._chat(messages)
        plan = self._extract_json(response)
        if plan is None or plan.get("action") not in KNOWN_ACTIONS:
            plan = {"action": "reply", "content": response}
        return plan
