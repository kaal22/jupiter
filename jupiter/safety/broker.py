"""Jupiter Tool Safety Broker — scoped permissions, confirmations, audit."""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional
from jupiter.storage.audit import AuditStore


class Scope(Enum):
    SYSTEM_READ = "system.read"
    SYSTEM_WRITE = "system.write"
    TERMINAL_READ = "terminal.read"
    TERMINAL_EXEC = "terminal.exec"
    EMAIL_READ = "email.read"
    EMAIL_WRITE = "email.write"


@dataclass
class ToolResult:
    success: bool
    output: str
    error: Optional[str] = None
    audit_action: Optional[str] = None


def require_confirmation(action: str, scope: Scope, details: dict, confirmed: bool, audit: AuditStore) -> bool:
    if scope in (Scope.SYSTEM_READ, Scope.TERMINAL_READ, Scope.EMAIL_READ):
        audit.log(action=action, scope=scope.value, details=details, outcome="allowed_read")
        return True
    if not confirmed:
        audit.log(action=action, scope=scope.value, details=details, outcome="denied_no_confirm")
        return False
    audit.log(action=action, scope=scope.value, details=details, outcome="confirmed")
    return True


class SafetyBroker:
    def __init__(self, audit: Optional[AuditStore] = None):
        self.audit = audit or AuditStore()

    def execute(self, tool_name: str, scope: Scope, fn: Callable, *args, confirmed: bool = False, **kwargs) -> ToolResult:
        if not require_confirmation(tool_name, scope, {"args": str(args)}, confirmed, self.audit):
            return ToolResult(success=False, output="", error="Action requires explicit user confirmation.", audit_action=f"{tool_name}_denied")
        result = fn(*args, **kwargs)
        if result.audit_action:
            self.audit.log(action=result.audit_action, scope=scope.value, details={"result_success": result.success}, outcome="success" if result.success else "error")
        return result
