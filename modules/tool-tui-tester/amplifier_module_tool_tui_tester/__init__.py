"""TUI Terminal Testing Tool for Amplifier.

Provides terminal session management for testing TUI applications:
- Spawn TUI apps in pseudo-terminals
- Send keystrokes and special keys
- Capture terminal state as text and screenshots
- Manage session lifecycle
"""

from typing import Any

from amplifier_core.interfaces import Tool
from amplifier_core.models import ToolResult

from .keys import parse_keys
from .session_manager import SessionManager

# Re-export for external use
__all__ = ["TUITerminalTool", "SessionManager", "mount"]

# Global session manager (lazy initialization)
_session_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    """Get or create the global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


class TUITerminalTool(Tool):
    """Tool for testing TUI applications via terminal emulation."""

    @property
    def name(self) -> str:
        return "tui_terminal"

    @property
    def description(self) -> str:
        return (
            "Test TUI (Terminal User Interface) applications by spawning "
            "terminal sessions, sending keystrokes, and capturing screenshots.\n\n"
            "Operations:\n"
            "- spawn: Start a new TUI app session\n"
            "- send_keys: Send keystrokes (supports {ENTER}, {TAB}, {UP}, {CTRL+C})\n"
            "- capture: Capture terminal state as text and screenshot\n"
            "- close: Close a session\n"
            "- list: List active sessions\n\n"
            "Example: spawn -> send_keys -> capture -> close\n\n"
            "Special keys: {ENTER}, {TAB}, {ESC}, {UP}, {DOWN}, {LEFT}, {RIGHT}, "
            "{HOME}, {END}, {CTRL+C}, {CTRL+D}, {F1}-{F12}"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["spawn", "send_keys", "capture", "close", "list"],
                    "description": "Operation to perform",
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID (required for send_keys, capture, close)",
                },
                "command": {
                    "type": "string",
                    "description": "Command to run (required for spawn)",
                },
                "keys": {
                    "type": "string",
                    "description": "Keys to send. Use {ENTER}, {TAB}, etc. for special keys",
                },
                "wait_ms": {
                    "type": "integer",
                    "description": "Milliseconds to wait after sending keys (default: 100)",
                    "default": 100,
                },
                "rows": {
                    "type": "integer",
                    "description": "Terminal height in rows (default: 24)",
                    "default": 24,
                },
                "cols": {
                    "type": "integer",
                    "description": "Terminal width in columns (default: 80)",
                    "default": 80,
                },
                "env": {
                    "type": "object",
                    "description": "Additional environment variables",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": ["operation"],
        }

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        """Execute a TUI terminal operation."""
        operation = input.get("operation")

        if not operation:
            return ToolResult(
                success=False,
                error="Missing required parameter: operation",
            )

        manager = get_session_manager()

        try:
            if operation == "spawn":
                return await self._spawn(manager, input)
            elif operation == "send_keys":
                return await self._send_keys(manager, input)
            elif operation == "capture":
                return await self._capture(manager, input)
            elif operation == "close":
                return await self._close(manager, input)
            elif operation == "list":
                return await self._list(manager)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown operation: {operation}",
                )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Operation {operation} failed: {str(e)}",
            )

    async def _spawn(self, manager: SessionManager, kwargs: dict) -> ToolResult:
        """Spawn a new TUI session."""
        command = kwargs.get("command")
        if not command:
            return ToolResult(
                success=False,
                error="Missing required parameter: command",
            )

        rows = kwargs.get("rows", 24)
        cols = kwargs.get("cols", 80)
        env = kwargs.get("env", {})

        session = await manager.spawn(
            command=command,
            rows=rows,
            cols=cols,
            env=env,
        )

        return ToolResult(
            success=True,
            data={
                "session_id": session.id,
                "status": "running" if session.is_alive() else "exited",
                "rows": rows,
                "cols": cols,
                "command": command,
            },
        )

    async def _send_keys(self, manager: SessionManager, kwargs: dict) -> ToolResult:
        """Send keystrokes to a session."""
        session_id = kwargs.get("session_id")
        if not session_id:
            return ToolResult(
                success=False,
                error="Missing required parameter: session_id",
            )

        keys = kwargs.get("keys", "")
        wait_ms = kwargs.get("wait_ms", 100)

        session = manager.get(session_id)
        if not session:
            return ToolResult(
                success=False,
                error=f"Session not found: {session_id}",
            )

        # Parse special keys and convert to bytes
        key_bytes = parse_keys(keys)

        # Send to session
        await session.send(key_bytes, wait_ms=wait_ms)

        return ToolResult(
            success=True,
            data={
                "status": "sent",
                "keys_sent": len(key_bytes),
                "session_alive": session.is_alive(),
            },
        )

    async def _capture(self, manager: SessionManager, kwargs: dict) -> ToolResult:
        """Capture terminal state."""
        session_id = kwargs.get("session_id")
        if not session_id:
            return ToolResult(
                success=False,
                error="Missing required parameter: session_id",
            )

        session = manager.get(session_id)
        if not session:
            return ToolResult(
                success=False,
                error=f"Session not found: {session_id}",
            )

        capture = await session.capture()

        return ToolResult(
            success=True,
            data={
                "text": capture["text"],
                "ansi": capture["ansi"],
                "image_path": capture["image_path"],
                "rows": session.rows,
                "cols": session.cols,
                "session_alive": session.is_alive(),
            },
        )

    async def _close(self, manager: SessionManager, kwargs: dict) -> ToolResult:
        """Close a session."""
        session_id = kwargs.get("session_id")
        if not session_id:
            return ToolResult(
                success=False,
                error="Missing required parameter: session_id",
            )

        success = await manager.close(session_id)

        if success:
            return ToolResult(
                success=True,
                data={"status": "closed", "session_id": session_id},
            )
        else:
            return ToolResult(
                success=False,
                error=f"Session not found: {session_id}",
            )

    async def _list(self, manager: SessionManager) -> ToolResult:
        """List active sessions."""
        sessions = manager.list_sessions()

        return ToolResult(
            success=True,
            data={
                "sessions": [
                    {
                        "session_id": s.id,
                        "command": s.command,
                        "status": "running" if s.is_alive() else "exited",
                        "rows": s.rows,
                        "cols": s.cols,
                    }
                    for s in sessions
                ],
                "count": len(sessions),
            },
        )


# Module mount point
async def mount(coordinator, config: dict) -> Tool:
    """Mount the TUI terminal tool.

    Args:
        coordinator: Module coordinator for registration
        config: Configuration from bundle (session_dir, timeout, etc.)

    Returns:
        The mounted TUI terminal tool instance
    """
    tool = TUITerminalTool()
    await coordinator.mount("tools", tool, name="tui_terminal")
    return tool
